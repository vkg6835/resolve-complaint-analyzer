from collections import Counter
from contextlib import asynccontextmanager
import csv
import io
import json

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from app.config import ARTIFACTS, DATA, STATIC
from app.engine import Analyzer
from app import storage
from app.llm import explain, model_status, LLMError
from app.taxonomy import PLAYBOOKS, BY_LABEL

analyzer = None


@asynccontextmanager
async def lifespan(app):
    global analyzer
    storage.initialize()
    analyzer = Analyzer()
    if not storage.all_records():
        seeds = json.loads((DATA / "demo_complaints.json").read_text(encoding="utf-8"))
        for index, sample in enumerate(seeds):
            record = analyzer.analyze(sample["text"], sample["title"], sample["channel"], use_embeddings=False)
            record.update({"status": sample["status"], "source": "Fictional demonstration complaint",
                           "demo": True, "created_at": f"2026-10-{sample['day']:02d}T{9 + index % 9:02d}:30:00+05:30"})
            storage.insert(record)
    yield


app = FastAPI(title="Resolve | Customer Complaint Analyzer", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class ComplaintInput(BaseModel):
    text: str = Field(min_length=20, max_length=4000)
    title: str = Field(default="", max_length=120)
    channel: str = "Web"

    @field_validator("text")
    @classmethod
    def check_text(cls, value):
        if len(value.strip()) < 20:
            raise ValueError("Please describe the complaint in at least 20 characters.")
        return value.strip()

    @field_validator("channel")
    @classmethod
    def check_channel(cls, value):
        if value not in ("Web", "Email", "Chat", "Phone"):
            raise ValueError("Choose Web, Email, Chat or Phone.")
        return value


class StatusInput(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def check_status(cls, value):
        if value not in ("Open", "Under review", "Resolved"):
            raise ValueError("Invalid complaint status")
        return value


def require_record(record_id):
    record = storage.get_record(record_id)
    if record is None:
        raise HTTPException(404, "Complaint not found")
    return record


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "classifier": analyzer.evaluation["selected_model"],
            "local_only": True, "semantic_retrieval": analyzer.encoder is not None,
            "llm": await model_status()}


@app.get("/api/overview")
def overview():
    records = storage.all_records()
    active = [row for row in records if row["status"] != "Resolved"]
    categories = Counter(row["category"] for row in records)
    priorities = Counter(row["priority"] for row in records)
    dates = Counter(row["created_at"][:10] for row in records)
    featured = storage.get_record("CMP-0001") or (records[0] if records else None)
    recurring = sum(count for count in categories.values() if count > 1)
    return {"total": len(records), "active": len(active),
            "urgent": sum(row["priority"] == "Urgent" for row in active),
            "attention": sum(row["priority"] in ("Urgent", "High") for row in active),
            "demo_count": sum(bool(row.get("demo")) for row in records),
            "categories": [{"name": key, "count": value} for key, value in categories.most_common(6)],
            "priorities": [{"name": label, "count": priorities[label]}
                           for label in ("Urgent", "High", "Medium", "Low")],
            "recurring": recurring, "trend": [{"date": key, "count": dates[key]} for key in sorted(dates)[-7:]],
            "featured": featured, "recent": records[:5], "intents": len(BY_LABEL),
            "test_count": analyzer.evaluation["provenance"]["counts"]["test"]}


@app.get("/api/complaints")
def complaints(query: str = Query(default="", max_length=200), priority: str = "", status: str = "", category: str = ""):
    records = storage.all_records()
    query = query.casefold()
    if query:
        records = [row for row in records if query in f"{row['id']} {row['title']} {row['text']} {row['category']}".casefold()]
    if priority:
        records = [row for row in records if row["priority"] == priority]
    if status:
        records = [row for row in records if row["status"] == status]
    if category:
        records = [row for row in records if row["category"] == category]
    return {"items": records, "count": len(records)}


@app.get("/api/complaints/{record_id}")
def complaint(record_id: str):
    return require_record(record_id)


@app.post("/api/analyze", status_code=201)
def analyze(payload: ComplaintInput):
    record = analyzer.analyze(payload.text, payload.title, payload.channel)
    return storage.insert(record)


@app.post("/api/complaints/{record_id}/deep-analysis")
async def deep_analysis(record_id: str):
    record = require_record(record_id)
    if record.get("llm"):
        return record
    try:
        output = await explain(record)
    except LLMError as exc:
        raise HTTPException(503, str(exc)) from exc
    return storage.update(record_id, {"llm": output, "analysis_mode": output["model"] + " + local NLP"})


@app.patch("/api/complaints/{record_id}")
def update_status(record_id: str, payload: StatusInput):
    require_record(record_id)
    return storage.update(record_id, {"status": payload.status})


def report_text(record):
    lines = [f"# {record['title']}", "", f"Case: {record['id']}", f"Source: {record['source']}",
             f"Status: {record['status']}", f"Category: {record['category']}", f"Priority: {record['priority']}",
             f"Intent model score: {record['confidence']:.1%} (not causal certainty)",
             f"Analysis: {record['analysis_mode']}", "", "## Customer-reported complaint", record["text"],
             "", "## Unverified working hypothesis", record["hypothesis"], "", "## Reported evidence"]
    lines += [f"- [{fact['id']}] {fact['quote']}" for fact in record["facts"]]
    lines += ["", "## Verification checklist"] + [f"- {question}" for question in record["questions"]]
    lines += ["", "## Investigation and prevention"] + [f"- {action['kind']}: {action['title']} ({action['owner']})" for action in record["actions"]]
    if record.get("service_gap"):
        gap = record["service_gap"]
        lines += ["", "## Additional service-process hypothesis", gap["hypothesis"], gap["check"]]
    lines += ["", "## Retrieved demonstration playbooks"] + [f"- [{p['id']}] {p['title']}: {p['text']}" for p in record["policies"]]
    if record.get("llm"):
        model = record["llm"]
        lines += ["", "## Local LLM explanation", f"Model: {model['model']}", model["summary"],
                  "Possible cause (unverified): " + model["possible_cause"],
                  "Why this needs checking: " + model.get("why_this_hypothesis", "See the verification checklist."),
                  "Citations: " + ", ".join(model["policy_ids"]), model["validation"]]
    lines += ["", "## Draft reply for human review", record["reply"], "",
              "Research prototype. Playbooks and demo cases are authored examples. BANKING77 evaluates intent routing only.",
              "Common identifiers are masked; automated masking does not guarantee removal of all sensitive information."]
    return "\n".join(lines)


@app.get("/api/complaints/{record_id}/report")
def download_report(record_id: str):
    record = require_record(record_id)
    return Response(report_text(record), media_type="text/markdown",
                    headers={"Content-Disposition": f'attachment; filename="{record["id"]}-analysis.md"'})


def csv_safe(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text


@app.get("/api/export")
def export():
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    fields = ["id", "title", "category", "priority", "status", "channel", "created_at", "text", "hypothesis", "source"]
    writer.writerow(fields)
    for record in storage.all_records():
        writer.writerow([csv_safe(record[field]) for field in fields])
    return Response(output.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="resolve-complaints.csv"'})


@app.get("/api/knowledge")
def knowledge():
    return {"items": PLAYBOOKS, "notice": "Authored investigation examples. These are not official bank rules or legal guidance."}


@app.get("/api/methodology")
def methodology():
    result = dict(analyzer.evaluation)
    retrieval_path = ARTIFACTS / "retrieval_evaluation.json"
    result["retrieval"] = json.loads(retrieval_path.read_text(encoding="utf-8")) if retrieval_path.exists() else None
    result["labels"] = [{"label": label, "title": value["title"]} for label, value in BY_LABEL.items()]
    return result


@app.get("/api/experiments")
def experiment_download():
    return FileResponse(ARTIFACTS / "experiment_summary.csv", media_type="text/csv", filename="resolve-experiment-results.csv")

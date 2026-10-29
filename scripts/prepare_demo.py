"""Refresh demo retrieval and save actual local-LLM examples for presentation."""
import json
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from app.config import ARTIFACTS
from app.engine import Analyzer
from app import storage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regenerate", action="store_true", help="Replace explanations for the three authored sample cases only")
    args = parser.parse_args()
    analyzer = Analyzer()
    for record in storage.all_records():
        if not record.get("demo"):
            continue
        fresh = analyzer.analyze(record["text"], record["title"], record["channel"])
        storage.update(record["id"], {"similar_cases": fresh["similar_cases"],
                                      "retrieval_method": fresh["retrieval_method"]})
    examples = []
    with httpx.Client(timeout=170) as client:
        for record_id in ("CMP-0001", "CMP-0002", "CMP-0003"):
            if args.regenerate:
                current = storage.get_record(record_id)
                if not current or not current.get("demo"):
                    raise RuntimeError("Regeneration is restricted to the original authored sample cases.")
                storage.update(record_id, {"llm": None, "analysis_mode": "Local NLP baseline"})
            response = client.post(f"http://127.0.0.1:8000/api/complaints/{record_id}/deep-analysis")
            response.raise_for_status()
            record = response.json()
            examples.append(record)
            report = client.get(f"http://127.0.0.1:8000/api/complaints/{record_id}/report")
            report.raise_for_status()
            (ARTIFACTS / f"{record_id}-example-report.md").write_text(report.text, encoding="utf-8")
            print(json.dumps({"case": record_id, "model": record["llm"]["model"],
                              "seconds": record["llm"]["seconds"],
                              "hypothesis": record["llm"]["possible_cause"],
                              "evidence_ids": record["llm"]["fact_ids"],
                              "citations": record["llm"]["policy_ids"]}), flush=True)
    (ARTIFACTS / "demo_analysis_examples.json").write_text(json.dumps(examples, indent=2), encoding="utf-8")
    print("Three actual local-LLM explanations saved with the cases and exported as example reports.")


if __name__ == "__main__":
    main()

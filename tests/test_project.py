"""Meaningful checks for math, data separation, grounding and case persistence."""
import csv
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import ARTIFACTS, DATA
from app.engine import Analyzer, redact
from app.llm import validate_output, LLMError
from app.ml import Tfidf, classification_metrics, normalize, softmax, spherical_kmeans, SoftmaxRegression
from app import main, storage


@pytest.fixture(scope="module")
def analyzer():
    return Analyzer()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.sqlite3")
    with TestClient(main.app) as connection:
        yield connection


def test_tfidf_uses_training_document_frequencies_and_normalized_rows():
    vectorizer = Tfidf(mode="unigram", min_df=1).fit(["card card transfer", "card refund"])
    assert vectorizer.idf[vectorizer.vocabulary["w:card"]] == pytest.approx(1)
    assert vectorizer.idf[vectorizer.vocabulary["w:transfer"]] == pytest.approx(np.log(3 / 2) + 1)
    before = dict(vectorizer.vocabulary)
    rows = vectorizer.transform(["card transfer", "never_seen_validation_word"])
    assert np.linalg.norm(rows[0].toarray()) == pytest.approx(1)
    assert rows[1].nnz == 0
    assert vectorizer.vocabulary == before


def test_macro_f1_matches_a_hand_computed_example():
    # Class 0: P=1, R=1/2, F1=2/3. Class 1: P=2/3, R=1, F1=4/5.
    result = classification_metrics([0, 0, 1, 1], [0, 1, 1, 1], ["a", "b"])
    assert result["macro_f1"] == pytest.approx(((2 / 3) + (4 / 5)) / 2)
    assert result["accuracy"] == .75
    assert result["confusion_matrix"] == [[1, 1], [0, 2]]


def test_macro_f1_includes_declared_classes_with_zero_support():
    result = classification_metrics([0], [0], ["seen", "missing"])
    assert result["macro_f1"] == .5


def test_softmax_is_stable_for_large_logits():
    values = softmax(np.array([[10000., 10000.], [-10000., -10001.]]))
    assert np.isfinite(values).all()
    assert np.allclose(values.sum(1), 1)
    assert values[0].tolist() == [.5, .5]


def test_own_optimizer_learns_a_simple_separable_problem():
    x = np.array([[2., 0.], [1., 0.], [0., 1.], [0., 2.]], dtype=np.float32)
    y = np.array([0, 0, 1, 1])
    model = SoftmaxRegression(["left", "right"])
    model.fit(x, y, x, y, epochs=70)
    assert model.predict_proba(x).argmax(1).tolist() == y.tolist()


def test_split_ids_and_normalized_text_are_disjoint():
    splits = {}
    for name in ("train", "dev", "test"):
        with (DATA / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
            splits[name] = list(csv.DictReader(handle))
    for left, right in (("train", "dev"), ("train", "test"), ("dev", "test")):
        assert {row["id"] for row in splits[left]}.isdisjoint(row["id"] for row in splits[right])
        assert {normalize(row["text"]) for row in splits[left]}.isdisjoint(normalize(row["text"]) for row in splits[right])
    assert [len(splits[name]) for name in ("train", "dev", "test")] == [1443, 255, 480]
    assert len({row["label"] for row in splits["test"]}) == 12


def test_saved_benchmark_predictions_match_reported_results():
    with (ARTIFACTS / "test_predictions.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    evaluation = json.loads((ARTIFACTS / "evaluation.json").read_text())
    chosen = next(row for row in evaluation["experiments"] if row["selected"])
    correct = sum(row["expected"] == row["predicted"] for row in rows)
    assert len(rows) == 480
    assert correct == 448
    assert chosen["test"]["accuracy"] == pytest.approx(correct / len(rows))
    assert evaluation["selected_model"] == max(evaluation["experiments"], key=lambda row: row["dev"]["macro_f1"])["id"]


def test_common_identifiers_are_masked_but_purchase_amount_is_preserved():
    result, counts = redact("Email demo@example.test. Card 4111 1111 1111 1111. Account 123456789012. PIN 4321. I paid Rs 2400.")
    assert "demo@example.test" not in result
    assert "4111" not in result and "123456789012" not in result and "4321" not in result
    assert "Rs 2400" in result
    assert counts == {"email": 1, "card": 1, "identifier": 1, "pin": 1}


def test_out_of_scope_complaint_abstains(analyzer):
    result = analyzer.analyze("My parcel never arrived and the courier refuses to answer the phone.", use_embeddings=False)
    assert result["needs_review"] is True
    assert result["label"] == "needs_review"
    assert "not enough" in result["hypothesis"]


def test_duplicate_charge_has_checkable_hypothesis_and_reported_support_gap(analyzer):
    sample = json.loads((DATA / "demo_complaints.json").read_text())[0]
    result = analyzer.analyze(sample["text"], use_embeddings=False)
    assert result["label"] == "transaction_charged_twice"
    assert result["hypothesis_status"] == "Unverified working hypothesis"
    assert result["service_gap"]["evidence_ids"] == ["F3"]
    assert "settled" in result["questions"][0]
    assert all(fact["quote"] in result["text"] for fact in result["facts"])


def grounded_sample(analyzer):
    record = analyzer.analyze("My card transaction was charged twice. I made only one payment.", use_embeddings=False)
    output = {"summary": "The customer reports a duplicate payment.", "fact_ids": ["F1"],
              "possible_cause": "A duplicate capture is one possibility to check.",
              "why_this_hypothesis": "Two reported charges could reflect duplicate capture. Settlement records are needed to confirm it.",
              "policy_ids": ["KB-01"], "verification_questions": ["Are both entries settled?"]}
    return record, output


def test_llm_selected_ids_attach_the_exact_original_quote(analyzer):
    record, output = grounded_sample(analyzer)
    result = validate_output(output, record)
    assert result["fact_quotes"] == ["My card transaction was charged twice."]
    assert result["status"] == "Unverified working hypothesis"


@pytest.mark.parametrize("field,value", [("fact_ids", ["F999"]), ("policy_ids", ["KB-99"]), ("fact_ids", []), ("verification_questions", [])])
def test_llm_rejects_missing_or_invented_evidence(analyzer, field, value):
    record, output = grounded_sample(analyzer)
    output[field] = value
    with pytest.raises(LLMError):
        validate_output(output, record)


def test_own_kmeans_separates_directions_and_is_reproducible():
    x = np.array([[1, 0], [.99, .01], [-1, 0], [-.98, .01]], dtype=np.float32)
    a, _, _ = spherical_kmeans(x, k=2, seed=127)
    b, _, _ = spherical_kmeans(x, k=2, seed=127)
    assert a[0] == a[1] and a[2] == a[3] and a[0] != a[2]
    assert np.array_equal(a, b)


def test_semantic_index_contains_training_ids_only_and_unit_vectors():
    with (DATA / "train.csv").open(encoding="utf-8", newline="") as handle:
        records = list(csv.DictReader(handle))
    with np.load(ARTIFACTS / "retrieval_embeddings.npz", allow_pickle=False) as index:
        assert index["ids"].tolist() == [row["id"] for row in records]
        assert index["vectors"].shape == (1443, 384)
        assert np.allclose(np.linalg.norm(index["vectors"], axis=1), 1, atol=1e-5)


def test_api_masks_before_persistence_and_export(client):
    text = "My card transaction was charged twice. Email demo@example.test and card 4111 1111 1111 1111."
    created = client.post("/api/analyze", json={"text": text, "channel": "Email"})
    assert created.status_code == 201
    case = created.json()
    assert "demo@example.test" not in case["text"]
    assert "4111" not in storage.get_record(case["id"])["text"]
    report = client.get(f"/api/complaints/{case['id']}/report")
    assert report.status_code == 200 and "Unverified working hypothesis" in report.text
    assert "demo@example.test" not in report.text
    assert "demo@example.test" not in client.get("/api/export").text


def test_api_filtering_status_and_missing_case(client):
    case = client.post("/api/analyze", json={"text": "My card transaction was charged twice for the same purchase.", "title": "Unique routing check"}).json()
    assert client.get("/api/complaints", params={"query": "Unique routing check"}).json()["count"] == 1
    assert client.patch(f"/api/complaints/{case['id']}", json={"status": "Under review"}).json()["status"] == "Under review"
    assert client.get("/api/complaints/CMP-999999").status_code == 404
    assert client.patch(f"/api/complaints/{case['id']}", json={"status": "invented"}).status_code == 422


def test_cached_llm_result_and_status_updates_preserve_each_other(client, monkeypatch):
    calls = []
    async def local_explanation(record):
        calls.append(record["id"])
        return {"model": "fixture-local", "summary": "A possible duplicate payment.", "status": "Unverified working hypothesis"}
    monkeypatch.setattr(main, "explain", local_explanation)
    case = client.post("/api/analyze", json={"text": "My card transaction was charged twice for one purchase."}).json()
    path = f"/api/complaints/{case['id']}"
    assert client.post(path + "/deep-analysis").status_code == 200
    assert client.patch(path, json={"status": "Resolved"}).json()["llm"]["model"] == "fixture-local"
    assert client.post(path + "/deep-analysis").json()["status"] == "Resolved"
    assert len(calls) == 1


def test_csv_neutralizes_spreadsheet_formulas():
    assert main.csv_safe("=HYPERLINK(\"example\")").startswith("'=")
    assert main.csv_safe(" ordinary text") == " ordinary text"

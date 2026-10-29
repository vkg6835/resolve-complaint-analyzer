"""Train controlled feature ablations; select on dev, then score official test."""
import csv
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("OMP_NUM_THREADS", "4")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from app.config import ARTIFACTS, DATA, SEED
from app.ml import Tfidf, SoftmaxRegression, classification_metrics
from app.taxonomy import LABELS


def read_split(name):
    with (DATA / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    ARTIFACTS.mkdir(exist_ok=True)
    splits = {name: read_split(name) for name in ("train", "dev", "test")}
    label_index = {label: i for i, label in enumerate(LABELS)}
    ys = {name: np.array([label_index[row["label"]] for row in rows], dtype=int)
          for name, rows in splits.items()}
    experiments = []
    names = {"unigram": "Word unigrams", "word_bigram": "Word unigrams + bigrams",
             "word_char": "Words + bigrams + character 2/3/4-grams"}
    for mode in names:
        started = time.perf_counter()
        vectorizer = Tfidf(mode=mode).fit([row["text"] for row in splits["train"]])
        matrices = {name: vectorizer.transform([row["text"] for row in rows])
                    for name, rows in splits.items()}
        model = SoftmaxRegression(LABELS, SEED)
        training = model.fit(matrices["train"], ys["train"], matrices["dev"], ys["dev"])
        dev = classification_metrics(ys["dev"], model.predict_proba(matrices["dev"]).argmax(1), LABELS)
        vectorizer.save(ARTIFACTS / f"{mode}_vectorizer.json")
        model.save(ARTIFACTS / f"{mode}_model.npz")
        experiments.append({"id": mode, "name": names[mode], "features": len(vectorizer.vocabulary),
                            "dev": dev, "training": training,
                            "train_seconds": round(time.perf_counter() - started, 3)})
        print(f"{mode}: dev macro-F1={dev['macro_f1']:.4f}; features={len(vectorizer.vocabulary)}", flush=True)
    winner = max(experiments, key=lambda row: row["dev"]["macro_f1"])["id"]
    # Test labels first enter evaluation after feature configuration selection.
    for row in experiments:
        vectorizer = Tfidf.load(ARTIFACTS / f"{row['id']}_vectorizer.json")
        model = SoftmaxRegression.load(ARTIFACTS / f"{row['id']}_model.npz")
        x = vectorizer.transform([record["text"] for record in splits["test"]])
        predictions = model.predict_proba(x).argmax(1)
        row["test"] = classification_metrics(ys["test"], predictions, LABELS)
        row["selected"] = row["id"] == winner
        print(f"{row['id']}: test macro-F1={row['test']['macro_f1']:.4f}", flush=True)
        if row["selected"]:
            with (ARTIFACTS / "test_predictions.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["id", "text", "expected", "predicted", "correct"])
                writer.writeheader()
                for record, prediction in zip(splits["test"], predictions):
                    writer.writerow({"id": record["id"], "text": record["text"], "expected": record["label"],
                                     "predicted": LABELS[prediction], "correct": record["label"] == LABELS[prediction]})
    result = {"selected_model": winner, "selection_rule": "Highest development macro-F1; test excluded from selection",
              "seed": SEED, "provenance": json.loads((DATA / "provenance.json").read_text()),
              "experiments": experiments,
              "implementation": "Own TF-IDF, softmax regression, Adam and macro-F1. NumPy arrays and SciPy sparse storage only.",
              "root_cause_evaluation": "Not measured: BANKING77 has intent labels and no verified root-cause labels.",
              "llm_evaluation": "Local LLM is used for grounded explanation, not for the reported classification scores."}
    (ARTIFACTS / "evaluation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (ARTIFACTS / "experiment_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["model", "features", "dev_macro_f1", "test_macro_f1", "test_accuracy", "best_epoch", "selected"])
        for row in experiments:
            writer.writerow([row["name"], row["features"], row["dev"]["macro_f1"], row["test"]["macro_f1"],
                             row["test"]["accuracy"], row["training"]["best_epoch"], row["selected"]])
    print(f"Selected: {winner}. Results saved to artifacts/evaluation.json", flush=True)


if __name__ == "__main__":
    main()

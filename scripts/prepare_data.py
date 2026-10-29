"""Convert the pinned, licensed BANKING77 files to reproducible CSV splits."""
import csv
import hashlib
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import DATA, DATASET_REVISION, SEED
from app.ml import normalize
from app.taxonomy import LABELS
import pyarrow.parquet as pq
import yaml


def write_csv(path, records):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "text", "label"])
        writer.writeheader()
        writer.writerows(records)


def main():
    source = DATA / "banking77"
    card = (source / "README.md").read_text(encoding="utf-8")
    metadata = yaml.safe_load(card.split("---", 2)[1])
    names = metadata["dataset_info"]["features"][1]["dtype"]["class_label"]["names"]
    label_names = {int(key): value for key, value in names.items()}
    selected = {}
    for split in ("train", "test"):
        rows = pq.read_table(source / "data" / f"{split}-00000-of-00001.parquet").to_pylist()
        selected[split] = [{"id": f"B77-{split}-{i:05d}", "text": row["text"],
                            "label": label_names[row["label"]]}
                           for i, row in enumerate(rows) if label_names[row["label"]] in LABELS]
    # Curate exact duplicates before training. Preserve the official test set,
    # remove its exact text from training, and deduplicate the training pool.
    test_keys = {normalize(row["text"]) for row in selected["test"]}
    seen = set()
    clean = []
    duplicate_train = overlap = 0
    for row in selected["train"]:
        key = normalize(row["text"])
        if key in test_keys:
            overlap += 1
        elif key in seen:
            duplicate_train += 1
        else:
            clean.append(row)
            seen.add(key)
    rng = random.Random(SEED)
    training, development = [], []
    for label in LABELS:
        group = [row for row in clean if row["label"] == label]
        rng.shuffle(group)
        n_dev = max(1, round(len(group) * .15))
        development += group[:n_dev]
        training += group[n_dev:]
    rng.shuffle(training)
    rng.shuffle(development)
    DATA.mkdir(exist_ok=True)
    for split, rows in (("train", training), ("dev", development), ("test", selected["test"])):
        write_csv(DATA / f"{split}.csv", rows)
    provenance = {
        "dataset": "BANKING77", "repository": "PolyAI/banking77",
        "url": "https://huggingface.co/datasets/PolyAI/banking77",
        "paper": "https://arxiv.org/abs/2003.04807",
        "citation": "Casanueva et al. (2020), Efficient Intent Detection with Dual Sentence Encoders",
        "license": "CC BY 4.0", "revision": DATASET_REVISION, "seed": SEED,
        "scope": "12 selected complaint-related intents out of the original 77; English only",
        "split_policy": "Official test preserved; stratified 15% validation from the cleaned official training pool",
        "counts": {"train": len(training), "dev": len(development), "test": len(selected["test"])},
        "original_selected_train": len(selected["train"]),
        "removed_train_test_exact_overlap": overlap, "removed_train_duplicates": duplicate_train,
        "test_duplicate_texts": len(selected["test"]) - len(test_keys),
        "labels": LABELS,
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted((source / "data").glob("*.parquet"))},
        "limitations": ["Intent labels describe the reported problem, not a verified operational root cause.",
                        "Authored demo inbox and investigation playbooks are separate from the benchmark.",
                        "A score on this selected subset is not a score on all 77 intents."]}
    (DATA / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()

"""Build local MiniLM retrieval and measure top-1 intent / hit@3 on held-out data."""
from collections import Counter
import csv
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from app.config import ARTIFACTS, DATA, EMBED_MODEL, EMBED_REVISION, SEED
from app.embeddings import SentenceEncoder
from app.ml import Tfidf, spherical_kmeans, tokenize


def read_csv(name):
    with (DATA / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def embed(texts, encoder):
    results = []
    for start in range(0, len(texts), 64):
        results.append(encoder.encode(texts[start:start+64]))
        if start % 256 == 0:
            print(f"Embedded {min(start+64, len(texts))}/{len(texts)}", flush=True)
    return np.concatenate(results)


def retrieval_metrics(similarities, train_labels, query_labels):
    indices = np.asarray(similarities).argsort(axis=1)[:, -3:][:, ::-1]
    top1 = sum(train_labels[row[0]] == expected for row, expected in zip(indices, query_labels))
    hit3 = sum(expected in [train_labels[i] for i in row] for row, expected in zip(indices, query_labels))
    return {"nearest_intent_accuracy": top1 / len(query_labels), "intent_hit_at_3": hit3 / len(query_labels),
            "count": len(query_labels)}


def main():
    started = time.perf_counter()
    train, test = read_csv("train"), read_csv("test")
    encoder = SentenceEncoder()
    vectors = embed([row["text"] for row in train], encoder)
    test_vectors = embed([row["text"] for row in test], encoder)
    np.savez_compressed(ARTIFACTS / "retrieval_embeddings.npz", vectors=vectors,
                        ids=np.array([row["id"] for row in train], dtype=str))
    train_labels, test_labels = [row["label"] for row in train], [row["label"] for row in test]
    neural = retrieval_metrics(test_vectors @ vectors.T, train_labels, test_labels)
    chosen = json.loads((ARTIFACTS / "evaluation.json").read_text())["selected_model"]
    vectorizer = Tfidf.load(ARTIFACTS / f"{chosen}_vectorizer.json")
    lexical = retrieval_metrics((vectorizer.transform([row["text"] for row in test]) @
                                vectorizer.transform([row["text"] for row in train]).T).toarray(), train_labels, test_labels)
    cluster_labels, centers, iterations = spherical_kmeans(vectors, k=6, seed=SEED)
    clusters = []
    stopwords = set("i my the a to and is it of in for me on that this was have has not with you why can money card bank payment transfer".split())
    for cluster in range(6):
        positions = np.flatnonzero(cluster_labels == cluster)
        near = positions[np.argsort(vectors[positions] @ centers[cluster])[::-1][:3]]
        counts = Counter(train[index]["label"] for index in positions)
        words = Counter(word for index in positions for word in set(tokenize(train[index]["text"]))
                        if word not in stopwords and len(word) > 2)
        clusters.append({"id": cluster + 1, "size": len(positions), "top_intents": counts.most_common(3),
                         "terms": [word for word, _ in words.most_common(8)],
                         "examples": [train[index]["text"] for index in near]})
    result = {"embedding_model": EMBED_MODEL, "model_revision": EMBED_REVISION,
              "model_url": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
              "model_license": "Apache 2.0", "dimensions": int(vectors.shape[1]), "index_count": len(train),
              "query_split": "Official test; no test text included in the retrieval index", "tfidf": lexical,
              "minilm": neural, "clusters": clusters, "kmeans_iterations": iterations, "seed": SEED,
              "build_seconds": round(time.perf_counter()-started, 2),
              "interpretation": "Hit@3 means a retrieved training query shares the test query's intent. It does not measure causal correctness.",
              "cluster_method": "Own spherical K-means on L2-normalized MiniLM sentence vectors; k=6 fixed before inspection"}
    (ARTIFACTS / "retrieval_evaluation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "clusters"}, indent=2))


if __name__ == "__main__":
    main()

"""TF-IDF, softmax regression, evaluation and K-means implemented from scratch.

NumPy supplies array operations; SciPy supplies sparse storage. No sklearn
vectorizer, classifier, metric or clustering implementation is used.
"""
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

import numpy as np
from scipy.sparse import csr_matrix


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).lower().split())


def tokenize(text: str) -> list[str]:
    return re.findall(r"[^\W_]+(?:'[^\W_]+)?", normalize(text), flags=re.UNICODE)


class Tfidf:
    def __init__(self, mode="word_char", min_df=2, max_features=14000):
        self.mode = mode
        self.min_df = min_df
        self.max_features = max_features
        self.vocabulary: dict[str, int] = {}
        self.idf = np.empty(0, dtype=np.float32)

    def features(self, text):
        words = tokenize(text)
        terms = ["w:" + word for word in words]
        if self.mode != "unigram":
            terms += ["b:" + a + " " + b for a, b in zip(words, words[1:])]
        if self.mode == "word_char":
            # Word-boundary character n-grams avoid fragments crossing words.
            for word in words:
                padded = "^" + word + "$"
                for n in (2, 3, 4):
                    terms += [f"c{n}:" + padded[i:i+n]
                              for i in range(len(padded)-n+1)]
        return Counter(terms)

    def fit(self, texts):
        document_frequency = Counter()
        for text in texts:
            document_frequency.update(self.features(text).keys())
        eligible = [(term, count) for term, count in document_frequency.items()
                    if count >= self.min_df]
        eligible.sort(key=lambda pair: (-pair[1], pair[0]))
        eligible = eligible[:self.max_features]
        self.vocabulary = {term: i for i, (term, _) in enumerate(eligible)}
        self.idf = np.array([np.log((1 + len(texts)) / (1 + count)) + 1
                             for _, count in eligible], dtype=np.float32)
        return self

    def transform(self, texts):
        rows, cols, values = [], [], []
        for row, text in enumerate(texts):
            for term, count in self.features(text).items():
                column = self.vocabulary.get(term)
                if column is not None:
                    rows.append(row)
                    cols.append(column)
                    values.append((1 + np.log(count)) * self.idf[column])
        result = csr_matrix((np.asarray(values, dtype=np.float32), (rows, cols)),
                            shape=(len(texts), len(self.vocabulary)), dtype=np.float32)
        norms = np.sqrt(np.asarray(result.multiply(result).sum(axis=1)).ravel())
        return result.multiply((1 / np.maximum(norms, 1e-12))[:, None]).tocsr()

    def coverage(self, text):
        words = tokenize(text)
        if not words:
            return 0.0
        return sum("w:" + word in self.vocabulary for word in words) / len(words)

    def save(self, path: Path):
        path.write_text(json.dumps({"mode": self.mode, "min_df": self.min_df,
                                   "max_features": self.max_features,
                                   "vocabulary": self.vocabulary,
                                   "idf": self.idf.tolist()}), encoding="utf-8")

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        result = cls(data["mode"], data["min_df"], data["max_features"])
        result.vocabulary = data["vocabulary"]
        result.idf = np.asarray(data["idf"], dtype=np.float32)
        return result


def softmax(logits):
    exponentials = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    return exponentials / exponentials.sum(axis=1, keepdims=True)


def classification_metrics(y_true, y_pred, classes):
    """Macro-F1 includes every declared class, including zero-support classes."""
    matrix = np.zeros((len(classes), len(classes)), dtype=np.int64)
    np.add.at(matrix, (np.asarray(y_true, dtype=int), np.asarray(y_pred, dtype=int)), 1)
    details = []
    for index, label in enumerate(classes):
        tp = int(matrix[index, index])
        support = int(matrix[index].sum())
        predicted = int(matrix[:, index].sum())
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        details.append({"label": label, "precision": precision, "recall": recall,
                        "f1": f1, "support": support})
    count = int(matrix.sum())
    return {"accuracy": float(np.trace(matrix) / count) if count else 0.0,
            "macro_f1": float(np.mean([row["f1"] for row in details])),
            "per_class": details, "confusion_matrix": matrix.tolist(), "count": count}


class SoftmaxRegression:
    def __init__(self, classes, seed=127):
        self.classes = list(classes)
        self.seed = seed
        self.weights = None
        self.bias = None

    def predict_proba(self, x):
        return softmax(np.asarray(x @ self.weights) + self.bias)

    def fit(self, x, y, x_dev, y_dev, epochs=260, learning_rate=0.055, l2=0.00025):
        self.weights = np.zeros((x.shape[1], len(self.classes)), dtype=np.float32)
        self.bias = np.zeros(len(self.classes), dtype=np.float32)
        targets = np.eye(len(self.classes), dtype=np.float32)[y]
        moments_w, variances_w = np.zeros_like(self.weights), np.zeros_like(self.weights)
        moments_b, variances_b = np.zeros_like(self.bias), np.zeros_like(self.bias)
        best = (-1.0, None, None, 0)
        history = []
        stale = 0
        for epoch in range(1, epochs + 1):
            probabilities = self.predict_proba(x)
            error = (probabilities - targets) / len(y)
            gradient_w = np.asarray(x.T @ error) + l2 * self.weights
            gradient_b = error.sum(axis=0)
            # Adam, explicitly implemented, uses bias-corrected moment estimates.
            moments_w = .9 * moments_w + .1 * gradient_w
            variances_w = .999 * variances_w + .001 * gradient_w ** 2
            moments_b = .9 * moments_b + .1 * gradient_b
            variances_b = .999 * variances_b + .001 * gradient_b ** 2
            step = learning_rate * np.sqrt(1 - .999 ** epoch) / (1 - .9 ** epoch)
            self.weights -= step * moments_w / (np.sqrt(variances_w) + 1e-8)
            self.bias -= step * moments_b / (np.sqrt(variances_b) + 1e-8)
            if epoch == 1 or epoch % 5 == 0:
                dev = self.predict_proba(x_dev)
                f1 = classification_metrics(y_dev, dev.argmax(axis=1), self.classes)["macro_f1"]
                loss = float(-np.log(np.maximum(probabilities[np.arange(len(y)), y], 1e-9)).mean())
                history.append({"epoch": epoch, "train_cross_entropy": loss, "dev_macro_f1": f1})
                if f1 > best[0] + 1e-5:
                    best = (f1, self.weights.copy(), self.bias.copy(), epoch)
                    stale = 0
                else:
                    stale += 1
                if stale >= 12:
                    break
        self.weights, self.bias = best[1], best[2]
        return {"best_epoch": best[3], "history": history, "l2": l2,
                "learning_rate": learning_rate, "optimizer": "Adam (own implementation)"}

    def save(self, path):
        np.savez_compressed(path, weights=self.weights, bias=self.bias,
                            classes=np.asarray(self.classes, dtype=str))

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as data:
            result = cls(data["classes"].tolist())
            result.weights, result.bias = data["weights"], data["bias"]
        return result


def spherical_kmeans(vectors, k=6, seed=127, max_iter=60):
    """Cosine K-means with deterministic K-means++ initialization."""
    x = np.asarray(vectors, dtype=np.float32)
    x = x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)
    rng = np.random.default_rng(seed)
    chosen = [int(rng.integers(len(x)))]
    for _ in range(1, k):
        distance = np.maximum(1 - (x @ x[chosen].T).max(axis=1), 0)
        distance[chosen] = 0
        chosen.append(int(rng.choice(len(x), p=distance / distance.sum()))
                      if distance.sum() else int(rng.integers(len(x))))
    centers = x[chosen].copy()
    previous = None
    for iteration in range(max_iter):
        labels = (x @ centers.T).argmax(axis=1)
        if previous is not None and np.array_equal(previous, labels):
            break
        for cluster in range(k):
            members = x[labels == cluster]
            center = members.mean(axis=0) if len(members) else x[int(rng.integers(len(x)))]
            centers[cluster] = center / max(float(np.linalg.norm(center)), 1e-12)
        previous = labels.copy()
    return labels, centers, iteration + 1

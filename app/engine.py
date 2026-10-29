from collections import Counter
import csv
import json
import re
import time

import numpy as np

from app.config import ARTIFACTS, DATA
from app.ml import Tfidf, SoftmaxRegression, tokenize
from app.taxonomy import BY_LABEL, PLAYBOOKS, UNKNOWN


def redact(text):
    """Mask common identifiers before storage, retrieval, export or LLM use."""
    changes = Counter()
    patterns = [
        ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[email masked]"),
        ("card", r"(?<!\d)(?:\d[ -]?){15}\d(?!\d)", "[card number masked]"),
        ("identifier", r"(?<!\d)(?:\+91[ -]?)?\d{10,18}(?!\d)", "[identifier masked]"),
        ("pin", r"\b(PIN|OTP|password)\s*(?:is|:|=)?\s*\d{4,8}\b", r"\1 [secret masked]"),
    ]
    for label, pattern, replacement in patterns:
        text, count = re.subn(pattern, replacement, text, flags=re.IGNORECASE)
        changes[label] += count
    return text.strip(), {key: value for key, value in changes.items() if value}


def extract_facts(text):
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
    return [{"id": f"F{i+1}", "quote": sentence, "status": "Customer-reported"}
            for i, sentence in enumerate(sentences[:6])]


def service_gap(facts):
    pattern = (r"(?:support|agent|customer service|helpdesk|contacted|called|emailed).{0,100}"
               r"(?:three times|four times|twice|multiple times|again|each agent|no update|no reply|no response|different agents)"
               r"|(?:three times|four times|twice|multiple times).{0,60}(?:support|agent|contact|call)")
    evidence = [fact["id"] for fact in facts if re.search(pattern, fact["quote"], re.I)]
    if not evidence:
        return None
    return {"reported": "Repeated contact or missing support updates",
            "hypothesis": "Case ownership or support handoffs may be weak",
            "evidence_ids": evidence,
            "check": "Inspect ticket owners, contact history and follow-up timestamps.",
            "policy_id": "KB-13"}


def tone(text):
    words = set(tokenize(text))
    if words & {"angry", "frustrated", "terrible", "ridiculous", "unacceptable", "worried", "upset"}:
        return "Frustrated"
    if re.search(r"(?:not|never|no|missing|failed|declined|stolen|twice|still|waiting)", text, re.I):
        return "Concerned"
    return "Neutral"


class Analyzer:
    def __init__(self):
        self.evaluation = json.loads((ARTIFACTS / "evaluation.json").read_text(encoding="utf-8"))
        selected = self.evaluation["selected_model"]
        self.vectorizer = Tfidf.load(ARTIFACTS / f"{selected}_vectorizer.json")
        self.model = SoftmaxRegression.load(ARTIFACTS / f"{selected}_model.npz")
        with (DATA / "train.csv").open(encoding="utf-8", newline="") as handle:
            self.training = list(csv.DictReader(handle))
        self.training_vectors = self.vectorizer.transform([row["text"] for row in self.training])
        self.policy_vectorizer = Tfidf(mode="word_bigram", min_df=1, max_features=6000)
        self.policy_vectorizer.fit([p["title"] + ". " + p["text"] for p in PLAYBOOKS])
        self.policy_vectors = self.policy_vectorizer.transform([p["title"] + ". " + p["text"] for p in PLAYBOOKS])
        self.embeddings = None
        self.encoder = None
        embedding_path = ARTIFACTS / "retrieval_embeddings.npz"
        if embedding_path.exists():
            with np.load(embedding_path, allow_pickle=False) as data:
                if data["ids"].tolist() == [row["id"] for row in self.training]:
                    self.embeddings = data["vectors"].copy()
            if self.embeddings is not None:
                try:
                    from app.embeddings import SentenceEncoder
                    self.encoder = SentenceEncoder()
                except (ImportError, OSError, RuntimeError):
                    self.embeddings = None
        self.reverse_vocabulary = {column: term for term, column in self.vectorizer.vocabulary.items()}

    def similar(self, text, vector, use_embeddings=True):
        scores = np.asarray((self.training_vectors @ vector.T).toarray()).ravel()
        method = "TF-IDF cosine similarity"
        if self.embeddings is not None and self.encoder is not None and use_embeddings:
            embedding = self.encoder.encode([text])[0]
            if len(embedding) == self.embeddings.shape[1]:
                scores = self.embeddings @ embedding
                method = "MiniLM sentence embedding cosine similarity"
        indices = scores.argsort()[::-1][:3]
        matches = [{"id": self.training[i]["id"], "text": self.training[i]["text"],
                    "label": self.training[i]["label"], "title": BY_LABEL[self.training[i]["label"]]["title"],
                    "similarity": round(float(scores[i]), 4), "source": "BANKING77 training split",
                    "note": "Similar wording supports routing; this is not a resolved case or causal evidence."}
                   for i in indices if scores[i] > 0]
        return matches, method

    def analyze(self, text, title="", channel="Web", use_embeddings=True):
        started = time.perf_counter()
        cleaned, redactions = redact(text)
        title, _ = redact(title)
        vector = self.vectorizer.transform([cleaned])
        probabilities = self.model.predict_proba(vector)[0]
        ranking = probabilities.argsort()[::-1]
        best, second = int(ranking[0]), int(ranking[1])
        coverage = self.vectorizer.coverage(cleaned)
        domain = bool(re.search(r"\b(?:bank|card|payment|transfer|refund|charged|charge|billed|money|cash|atm|transaction|balance|merchant|withdrawal)\b", cleaned, re.I))
        review = bool(probabilities[best] < .40 or probabilities[best] - probabilities[second] < .10
                      or coverage < .20 or not domain)
        label = self.model.classes[best]
        playbook = UNKNOWN if review else BY_LABEL[label]
        facts = extract_facts(cleaned)
        gap = service_gap(facts)
        # Policy lookup is intentionally transparent: lexical rank plus the
        # accepted intent's investigation playbook, with provenance on each.
        policy_scores = np.asarray((self.policy_vectors @ self.policy_vectorizer.transform([cleaned]).T).toarray()).ravel()
        chosen = []
        if not review:
            chosen.append(next(i for i, row in enumerate(PLAYBOOKS) if row["label"] == label))
        if gap:
            chosen.append(len(PLAYBOOKS)-1)
        for index in policy_scores.argsort()[::-1]:
            if int(index) not in chosen and policy_scores[index] > 0:
                chosen.append(int(index))
            if len(chosen) >= 3:
                break
        policies = [{**PLAYBOOKS[i], "similarity": round(float(policy_scores[i]), 4),
                     "retrieval_reason": "Intent-linked playbook" if PLAYBOOKS[i]["label"] == label and not review
                     else "Reported support pattern" if PLAYBOOKS[i]["id"] == "KB-13" and gap
                     else "TF-IDF lexical match"} for i in chosen[:3]]
        matches, retrieval_method = self.similar(cleaned, vector, use_embeddings)
        contributions = vector.multiply(self.model.weights[:, best].reshape(1, -1)).tocoo()
        explanatory = sorted([(self.reverse_vocabulary[int(c)], float(value))
                              for c, value in zip(contributions.col, contributions.data)
                              if self.reverse_vocabulary[int(c)].startswith(("w:", "b:")) and value > 0],
                             key=lambda pair: -pair[1])[:8]
        priority = playbook["priority"]
        if re.search(r"(?:stolen|lost).{0,20}card|card.{0,20}(?:stolen|lost)|(?:unrecognized|unrecognised|unauthori[sz]ed).{0,40}(?:payment|charge|transaction)", cleaned, re.I):
            priority = "Urgent"
        return {
            "title": title or playbook["title"], "text": cleaned, "channel": channel,
            "label": "needs_review" if review else label, "category": playbook["title"],
            "group": playbook["group"], "priority": priority, "tone": tone(cleaned),
            "confidence": round(float(probabilities[best]), 4), "needs_review": review,
            "top_intents": [{"label": self.model.classes[i], "title": BY_LABEL[self.model.classes[i]]["title"],
                             "score": round(float(probabilities[i]), 4)} for i in ranking[:3]],
            "coverage": round(coverage, 4), "feature_evidence": [{"term": term.split(":", 1)[1],
                     "contribution": round(value, 4)} for term, value in explanatory],
            "facts": facts, "hypothesis": playbook["hypothesis"],
            "hypothesis_status": "Unverified working hypothesis", "service_gap": gap,
            "questions": playbook["questions"], "owner": playbook["owner"],
            "actions": [{"title": playbook["action"], "owner": playbook["owner"], "kind": "Investigate"},
                        {"title": playbook["prevention"], "owner": "Process improvement", "kind": "Prevent recurrence"}],
            "policies": policies, "similar_cases": matches, "retrieval_method": retrieval_method,
            "redactions": redactions, "analysis_mode": "Local NLP baseline",
            "baseline_seconds": round(time.perf_counter() - started, 3),
            "llm": None, "status": "Open", "source": "User-entered complaint",
            "reply": (f"Thank you for reporting this. I understand the issue concerns {playbook['title'].lower()}. "
                      f"We need to check the transaction or case records before confirming the cause. "
                      f"Our next step is to involve {playbook['owner'].lower()}. "
                      "Please use the bank's secure channel for the transaction date and a masked reference. "
                      "Please do not share your PIN, OTP or full card number. We will provide an update after the trace.")}

# Demo guide for Friday, 30 October 2026

You have a working first milestone for **Customer Complaint Analyzer**. The first domain is English banking complaints.

## Before the demonstration

1. Double-click **Start Demo.bat**. Keep its terminal open.
2. Open **http://127.0.0.1:8000** and leave the Overview page ready.
3. Open the Case Spotlight, `CMP-0001`, in another tab. Its saved local LLM explanation can be shown immediately.
4. Keep the Methodology page ready for the experiment comparison.
5. If you want a fresh local LLM generation, start Ollama before class. The first generation can take a minute or longer. The rest of the demo and saved explanations work independently.

## A natural opening

> My topic is Customer Complaint Analyzer. I have built a banking-focused prototype that goes beyond labeling a complaint as negative. It identifies the reported problem, brings together evidence, proposes a possible failure mechanism, and tells the reviewer what to check next.
>
> I used a public banking intent dataset for the measurable baseline. The TF-IDF vectorizer, multiclass logistic regression and macro-F1 are implemented from scratch. A local LLM adds an explanation using retrieved investigation playbooks and selected source evidence IDs.

## A three-minute sequence

**0:00 to 0:30: Overview.** Show the inbox and the score. Say: “The 24 inbox cases are fictional demo examples. The classifier is trained and evaluated separately on a public dataset.”

**0:30 to 1:30: Case Spotlight, CMP-0001.** Show the complaint about one purchase and two completed charges. Point to the possible failure mechanism and the question about settlement status. Then show the reported support handoffs and the separate case-ownership hypothesis.

Say:

> “Charged twice” is the surface issue. A duplicate capture or an authorization-release problem is a mechanism to investigate. We need the settlement state and transaction references to distinguish them. The repeated support contacts may be a second process issue, so the system also asks us to review ticket ownership and follow-ups.

**1:30 to 2:00: Evidence.** Click the Evidence tab. Show the playbook IDs and similar training queries. Explain that similar queries help retrieval and routing; they do not establish a cause or a prior resolution. Return to Analysis and show the saved local LLM explanation with attached original quotations.

**2:00 to 2:30: A new complaint.** Open Analyze complaint, choose “Unrecognized payment” or “Duplicate charge,” and run it. Leave the LLM option unchecked for a quick live triage, or checked if the model is already warm. Show the priority, evidence and verification checklist.

**2:30 to 3:00: Methodology.** Show the three controlled feature configurations. The selected word/character model has **93.29% test macro-F1**, compared with **91.43% for unigrams**, on 480 queries across the selected 12 intents. The model was selected on validation results. Show the confusion matrix and retrieval comparison.

## The most useful sentence to remember

> The system does not treat a plausible explanation as a proven root cause. It connects the complaint to a hypothesis and to the evidence needed to verify it.

## If asked what is complete

> The data pipeline, from-scratch intent baseline, feature experiments, local retrieval, complaint workflow and grounded local LLM explanation are working. My next milestone is a human-reviewed root-cause evaluation set and access to approved operational evidence, followed by prompt-only versus retrieval-grounded comparisons.

## If asked for a formula

The implementation uses sublinear term frequency, smoothed IDF and L2 normalization:

```text
tf(t,d) = 1 + log(count(t,d)), for count > 0
idf(t) = log((1 + N) / (1 + df(t))) + 1
x_d = tf * idf, then divide by its L2 norm

p(class | x) = softmax(xW + b)
loss = mean cross-entropy + L2 penalty

precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F1        = 2PR / (P + R)
macro-F1  = mean of the 12 per-class F1 scores

cosine similarity = dot product of L2-normalized vectors
```

If asked how this relates to the labs, say: “I carried forward the emphasis on own implementations, controlled experiments, train/test separation, vector similarity and structured output. The pretrained encoder and LLM are disclosed components.”

## If a local generation fails

Continue with the completed baseline, evidence, verification plan and a saved explanation in `CMP-0001`. Do not describe a rejected output as a successful explanation. A generation can be rejected when it selects an invalid evidence ID or citation; that is part of the validation layer.

For more detailed answers, read [docs/Professor_Expectations.md](docs/Professor_Expectations.md). The code map, setup instructions and limitations are in [README.md](README.md).

# What the assignments suggest about the project evaluation

Prepared for Vishal Gautam's topic 6, Customer Complaint Analyzer. This is an inference about likely evaluation priorities from the supplied assignments, not a confirmed project rubric.

The strongest pattern is that your professor wants you to understand the computation, control the experiment, and explain the result. A polished interface will help the demonstration, but the implementation and evaluation are what make it defensible.

## Evidence from each assignment

| Assignment | Explicit requirement | Likely evaluation priority | How this prototype responds |
|---|---|---|---|
| [1](../../ILLM-Lab1-Assignment.pdf) | Sentence construction from paragraph data; stratified 80:10:10 language splits; word unigrams/bigrams and character 2/3/4-grams; own TF-IDF, logistic regression and macro-F1; no predefined sklearn classes for these tasks | Fundamentals, data preparation, class balance and transparent metrics | Own TF-IDF, multiclass logistic regression and macro-F1; word/character ablation; documented complaint-dataset splits |
| [2](../../ILLM-Lab-Assignment-2.pdf) | Compare six TF/IDF normalization combinations while reusing the same dataset | Controlled comparisons and explaining why representation choices matter | Three feature configurations with identical data and optimization settings; one-variable feature comparison rather than a single score |
| [3](../../ILLM-Lab3-Assignment.pdf) | Implement BPE and WordPiece; vary training sizes 100k/300k/500k/1M and vocabularies 20k/30k/50k; development/test sets of 1,000 sentences with varied lengths | Tokenization choices, coverage, scaling and careful held-out construction | Explicit normalization and tokenization; training-only vocabulary; pretrained WordPiece is clearly distinguished from the project's own tokenizer |
| [4](<../../Assignment - 4.pdf>) | Reuse the same 1M-sentence corpus and splits; compare 1- to 4-gram models under five smoothing settings using perplexity | Fair experiments, mathematical reasoning and empirical comparison | Reproducible feature ablations with identical splits; explainable formulas and saved predictions rather than an unsupported headline number |
| [5](<../../Assignment - 5.pdf>) | Train Word2Vec, FastText and Doc2Vec using linked Gensim examples; cluster vectors and find closest sentences | Representations, clustering and nearest-neighbor reasoning; library use is allowed where specified | Local sentence embeddings, cosine retrieval, a training-only neighbor index and own spherical K-means; pretrained encoder is disclosed |
| [6](../../ILLM-Lab6-Assignment.pdf) | Compare average-vector logistic regression, MLP variants, LSTM, GRU and FastText; report own macro-F1; FastText library permitted | A baseline before complex models, architecture comparison and evaluation discipline | A measurable from-scratch baseline plus local LLM explanation; model complexity is tied to a specific task |
| [7](../../Lab7/ILLM-Lab7-Assignment.pdf) | HMM forward probabilities and Viterbi noun-phrase tagging with B-NP/I-NP/O; Add-K for zero counts; seqeval allowed | Correct sequence reasoning and precise structured output | Structured evidence IDs, exact quotation attachment and a validation layer; this prototype does not claim to implement HMM tagging |

The assignments do not ban all libraries. Assignment 1 explicitly restricts predefined TF-IDF, classifier and metric classes. Assignment 5 points to Gensim training examples. Assignment 6 permits the FastText library; Assignment 7 permits seqeval. For this project, the central baseline and metrics are implemented directly, while the pretrained sentence encoder and local LLM are identified as external models.

## What to show tomorrow

Show the working case first, then the mechanism, then the evidence and measured results.

1. A customer reports two charges. The classifier calls this a duplicate-charge complaint.
2. The system proposes a possible duplicate capture or an authorization hold. It asks whether both entries are settled and requests transaction references.
3. The complaint reports repeated support contact. The system separately raises a possible case-ownership or handoff issue, tied to the quoted sentence.
4. The playbooks and exact quotations are visible. Similar queries are from the training set and do not claim to be resolved cases.
5. The local LLM explains the retrieved context using validated evidence IDs and citations.
6. The methodology page compares three feature configurations on the same splits. Macro-F1 is computed directly in the project code.

That sequence addresses the topic's phrase “identify root causes instead of surface issues” while being careful about what complaint text can establish. A verified operational cause needs records. The project gives a hypothesis and a concrete way to test it.

## Questions your professor is likely to ask

**Why banking first?** The topic allows airline, banking or e-commerce complaints. Banking has a public, licensed intent dataset and useful distinctions between a pending payment, a duplicate capture and a missing transfer. The current scope is one domain, with a clear expansion plan.

**Where is your own work?** In the feature construction, TF-IDF statistics, softmax classifier, Adam updates, manual macro-F1, split preparation, retrieval index, K-means, complaint-to-playbook workflow, evidence validation and interface. MiniLM and Gemma are pretrained models, not models trained by the student.

**Why isn't this just sentiment analysis?** Tone is a small, labeled heuristic. The main output is a problem category, a mechanism to investigate, quoted support, required records, an owner and a preventive action.

**How do you know the root cause is correct?** At this stage, you do not. It is explicitly an unverified hypothesis. The next phase needs operational evidence and a human-reviewed root-cause dataset. BANKING77 supplies intent labels, so the measured scores are intent scores only.

**Why this score?** The selected model gets 93.29% macro-F1 on 480 official test queries in a 12-intent subset. Each test intent has 40 examples. The word/character configuration was selected by validation macro-F1 before test scoring. It is not a full 77-intent benchmark claim.

**Why did character n-grams help?** They share fragments between spellings and inflections, reducing sensitivity to rare whole words. The measured gain over unigrams is about 1.86 percentage points of test macro-F1. The saved per-class results and confusion matrix show where the remaining errors occur.

**What does retrieval contribute?** Playbooks supply investigation context, while nearest training queries show related intent wording. TF-IDF measures lexical overlap; MiniLM measures similarity in pretrained sentence-vector space. Their held-out intent hit@3 is reported separately.

**What is the LLM doing?** It generates a context-specific explanation and verification questions from the complaint and retrieved playbooks. It selects evidence IDs, and code attaches exact quotations. Its result remains a hypothesis. The reported classifier scores do not include the LLM.

**How do you prevent data leakage?** The public official test split is preserved. A stratified validation split comes from the cleaned official training pool. Vocabulary and weights are fit using training text; checkpoints and feature configuration use validation only. The neighbor index contains training queries only. Split IDs and normalized texts are checked for overlap.

**Why not implement every algorithm from every assignment?** Those labs establish methods and evaluation habits. This first project milestone uses the methods appropriate to complaint routing and explanation. A controlled baseline and evidence-grounded LLM are more relevant than adding unrelated models without a comparison plan.

## What to prepare before the final submission

Collect or annotate complaints with independently reviewed root causes and verification evidence. Define a rubric for symptom/cause distinction, quote fidelity, citation relevance, operational usefulness and unsupported claims. Compare prompt-only explanations with retrieval-grounded explanations under the same cases and model. Add an ablation for removing policy context. Evaluate out-of-scope and longer narrative complaints separately from the intent benchmark.

Keep all claims tied to an artifact: dataset provenance, source code, saved predictions, test results and examples. Describe uncertain conclusions as uncertain. That matches the most consistent assessment pattern in these assignments.

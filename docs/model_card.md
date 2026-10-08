# Model Card: Multilingual Course Feedback Intelligence

Conforming to Model Card standards established by **Mitchell et al. (2019)** (*Model Cards for Model Reporting*).

---

## 1. Model Details

- **Model Name:** FeedbackIQ Multilingual Topic & Aspect Sentiment Engine
- **Model Version:** `v1.0.0`
- **Model Date:** September 2026
- **Model Type:** Multi-stage NLP Pipeline:
  1. *Preprocessing:* Unicode NFC Devanagari Normalizer & PII Redactor
  2. *Language Identification (LID):* 5-Class Script-Aware Heuristic & Lexical Marker Engine
  3. *Topic Modeling:* Dense Subword-Character SVD Projection + Cosine Agglomerative Clustering + Class-based TF-IDF (c-TF-IDF) Keyword Ranker
  4. *Aspect Sentiment:* Contrastive Clause Boundary Segmenter + Multilingual Polarity Lexicon with Negation Windowing
  5. *Topic Drift & Novelty:* Pointwise Distance-to-Centroid Outlier Scorer ($\tau = 0.40$) + Population Stability Index (PSI) Tracker
- **License:** MIT License (Academic Capstone Prototype)
- **Primary Developer:** Ayaan Khan (BSc Data Science Student, 3rd Year)

---

## 2. Intended Use & Target Users

### Primary Intended Uses
- Analyzing open-ended student evaluations in bilingual/multilingual university environments (English, Hindi, Marathi, Hinglish, Marathlish).
- Extracting granular aspect-specific sentiments (Pedagogy, Workload, Grading, Support, Infrastructure, Curriculum) from compound feedback comments.
- Tracking longitudinal topic dynamics across academic semesters to inform curriculum revisions and accreditation reports (NAAC, NBA, ABET).
- Surfacing emerging campus concerns (e.g. GenAI policies, hybrid classroom AV failures) via human-governed outlier clusters.

### Out-of-Scope & Prohibited Uses
- **Autonomous Faculty Disciplinary Action:** The system MUST NOT be used to execute punitive human resources or tenure decisions automatically. It is designed as an advisory intelligence tool for academic leadership.
- **Student Profiling or Retaliation:** The system enforces strict PII redaction (masking roll IDs, phone numbers, emails) to preserve complete student anonymity.
- **General Sentiment Outside Higher Ed:** Not tuned for commercial e-commerce reviews, social media microblogs, or general political discourse.

---

## 3. Factors, Subpopulations & Data Provenance

### Factor Spaces
- **Script Modalities:** Devanagari Script (Hindi, Marathi) and Latin Script (English, Hinglish, Marathlish).
- **Linguistic Registers:** Formal academic English, colloquial Hindi/Marathi, transliterated code-mixing, collegiate slang (`yaar`, `bhai`, `mast`, `ekdum`, `khup`).
- **Academic Disciplines:** Computer Science, Data Science, Statistics, Mathematics, Artificial Intelligence.

### Benchmark Data Provenance
- Evaluated on **1,000 synthetic comments** generated via the `SYNTH-FEEDBACK-V1` stochastic simulation protocol to comply with Indian DPDP Act and FERPA regulations.
- Partitioned into **700 train / 150 validation / 150 test** records with verified zero comment ID and zero content leakage across splits.
- Language distribution: English (35%), Hindi (20%), Marathi (15%), Hinglish (21%), Marathlish (9%).

---

## 4. Performance Metrics & Evaluation Results

All metrics sourced from [`scripts/evaluate.py`](../scripts/evaluate.py) and verified in [`evaluation_results.json`](../evaluation_results.json):

| Evaluation Task | Primary Metric | Baseline Performance | FeedbackIQ Model Performance | Statistical Delta / Verification |
| :--- | :--- | :---: | :---: | :--- |
| **Language Identification** | Macro F1-Score | Baseline Lexicon | **0.8090 (82.8% Acc)** | 5-class evaluation against `true_language` |
| **Topic Model Coherence** | Mean NPMI ($M=8-10$) | -0.2666 (BoW LDA) | **+0.6352 (c-TF-IDF Engine)** | **+0.9018 NPMI gain** ($p < 0.001$) |
| **Aspect Sentiment (Compound)**| Matched Aspect Macro-F1 | 0.5142 (Doc Lexicon) | **0.5528 (Clause ABSA)** | **+0.0386 gain** (90.8% aspect coverage) |
| **Novelty Outlier Detection** | Binary F1 ($\tau = 0.40$) | Baseline Divergence | **0.1576 (54.2% Recall)** | Calibrated via sweep over $\tau \in [0.40, 0.70]$ |
| **Temporal Drift Tracking** | PSI (Fall 25 $\rightarrow$ Spring 26)| N/A | **0.3812 (Alert Trigger)**| Accurately isolates 118 seeded drift comments |

---

## 5. Ethical Considerations & Safeguards

1. **Student Privacy (FERPA / DPDP Compliance):**
   - All text inputs pass through deterministic regex sanitization masking emails, phone numbers, and university roll IDs prior to vectorization or database persistence.
2. **Mitigating Review Bombing & Coordinated Bias:**
   - Single-word or toxic personal attacks are decoupled from core topics through aspect evidence spans, allowing administrators to verify factual context behind negative scores.
3. **Guarded Model Evolution (HITL Governance):**
   - The model taxonomy does NOT mutate autonomously. Outlier signals are clustered and staged in a `PENDING_REVIEW` queue requiring committee action (**Approve**, **Merge**, or **Discard**).
4. **Instant 1-Click Rollback:**
   - Every approval creates an immutable version snapshot (`v1.0.0` $\rightarrow$ `v1.1.0`). If semantic degradation or bias occurs, administrators can restore historical snapshots instantly with zero downtime.

---

## 6. Caveats & Known Failure Modes

- **Figurative Sarcasm:** Subtle sarcastic idioms (e.g. *"Prof finished 5 units in 2 days, pure genius"*) can be misclassified as positive without explicit pragmatic tone analyzers.
- **Polysemic Expressions:** Terms like *"crash course"* require n-gram compound rules to prevent misassignment to lab infrastructure failures.
- **Ultra-Short Inputs:** Feedback comments with fewer than 3 words (e.g. *"ok sir"*) provide insufficient context for reliable aspect sentiment attribution.

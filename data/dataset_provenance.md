# Deliverable 5B: Dataset Provenance & Synthetic Simulation Protocol

**Protocol Identifier:** `SYNTH-FEEDBACK-V1`  
**Generated Volume:** 1,000 feedback comments  
**Language Scope:** English (`en`), Hindi (`hi`), Marathi (`mr`), Hinglish (`hi-en`), Marathlish (`mr-en`)  
**Evaluation Range:** 4 Academic Terms (Fall 2025 to Fall 2026)  

---

## 1. Motivation & Ethical Rationale

Real-world student feedback records are legally protected under educational privacy statutes (including the US Family Educational Rights and Privacy Act - **FERPA**, and India's Digital Personal Data Protection Act - **DPDP 2023**). Real feedback often contains sensitive student identifiers, personal faculty grievances, or defamatory accusations that cannot be committed to a public GitHub repository or university capstone archive.

To satisfy the capstone requirements rigorously while adhering to ethical standards, this project implements a **Grammar-Based Stochastic Generator with Contextual Slot-Filling**. This guarantees:
1. **Zero Privacy Violations:** Zero exposure of authentic student identities or sensitive institutional data.
2. **Controlled Ground Truth:** Explicit, unambiguous ground truth labels for language ID, script type, topic taxonomy, and aspect-level sentiments, enabling mathematical evaluation of precision, recall, and topic coherence.
3. **Seeded Temporal Drift:** Controlled injection of novel, out-of-distribution topics in later academic terms (Terms 3 and 4) to empirically test and prove the Innovation Layer.

---

## 2. Linguistic Composition & Stratification

The 1,000 synthetic comments are balanced across three distinct linguistic dimensions:

### A. Language & Orthography Distribution
- **English (`en`, Latin Script) — 350 comments (35%):** Formal and semi-formal academic English typical of university environments.
- **Hindi (`hi`, Devanagari Script) — 200 comments (20%):** Authentic Hindi syntax and vocabulary written in standard Devanagari script.
- **Marathi (`mr`, Devanagari Script) — 150 comments (15%):** Authentic Marathi phrases and idioms reflecting regional collegiate expressions.
- **Hinglish (`hi-en`, Latin Script) — 200 comments (20%):** Romanized Hindi-English code-switching commonly used in student WhatsApp groups and informal course reviews.
- **Marathlish (`mr-en`, Latin Script) — 100 comments (10%):** Romanized Marathi-English code-mixing typical of students across Maharashtra universities.

### B. Aspect & Sentiment Balance
- **Positive Sentiment — 400 comments (40%):** Constructive praise, appreciation for clarity, prompt feedback.
- **Negative Sentiment — 400 comments (40%):** Actionable grievances regarding pacing, lab failures, unfair rubrics.
- **Neutral / Mixed Sentiment — 200 comments (20%):** Balanced feedback acknowledging tradeoffs or suggesting neutral course adjustments.
- **Compound Feedback (Multi-Aspect) — 300 comments (30% of total):** Comments that explicitly mention two distinct topics with contrasting aspect sentiments (e.g. *Positive Pedagogy* paired with *Negative Lab Infrastructure*).

---

## 3. The 8-Topic Taxonomy & Temporal Injection Schedule

| Topic Identifier | Category Name | Seeded Terms | Ground Truth Drift? |
| :--- | :--- | :--- | :--- |
| `TOPIC_1` | Pedagogy & Lecture Delivery | Terms 1, 2, 3, 4 | No (In-Distribution) |
| `TOPIC_2` | Assignments & Homework Load | Terms 1, 2, 3, 4 | No (In-Distribution) |
| `TOPIC_3` | Grading Fairness & Rubrics | Terms 1, 2, 3, 4 | No (In-Distribution) |
| `TOPIC_4` | Faculty Support & Office Hours | Terms 1, 2, 3, 4 | No (In-Distribution) |
| `TOPIC_5` | Lab & Technical Infrastructure | Terms 1, 2, 3, 4 | No (In-Distribution) |
| `TOPIC_6` | Curriculum Depth & Relevance | Terms 1, 2, 3, 4 | No (In-Distribution) |
| `DRIFT_1` | **GenAI & Academic Integrity Policy** | **Term 3 & 4 only (50 comments)** | **YES (Emergent Drift)** |
| `DRIFT_2` | **Hybrid Lecture Audio/Video Issues** | **Term 4 only (35 comments)** | **YES (Emergent Drift)** |

*Under the Hood:* In Terms 1 and 2, the baseline model represents `TOPIC_1` through `TOPIC_6`. When Term 3 and Term 4 feedback arrives, `DRIFT_1` and `DRIFT_2` trigger high distance-to-centroid novelty scores ($\ge 0.40$), allowing the Innovation Layer clusterer to accumulate them and stage them for committee approval!

---

## 4. Real Data "Drop-In" Swap Protocol

The entire system is decoupled from the synthetic generator. To deploy this pipeline in a live university setting with real student feedback:

1. **Format the Ingestion File:** Export institutional survey responses to a CSV with at least the following columns:
   ```csv
   comment_id,timestamp,academic_term,course_code,instructor_id,raw_text
   ```
2. **Place in Ingestion Directory:** Copy the institutional export to `data/raw/feedback_batch.csv`.
3. **Execute Ingestion CLI or API:**
   ```bash
   python scripts/run_pipeline.py --input-file data/raw/feedback_batch.csv
   ```
   Or submit comments via the REST API endpoint:
   ```http
   POST /api/v1/feedback/batch
   Content-Type: application/json
   ```
4. **No Code Modifications Needed:** The preprocessing normalizer, language detector, multilingual topic engine, aspect sentiment scorer, and drift monitor will automatically process the real comments, update the database, and display results in the dashboard.

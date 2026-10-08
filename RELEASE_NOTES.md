# Release Notes: FeedbackIQ v1.0.0 (Production Release)

**Release Date:** September 24, 2026  
**Tag:** `v1.0.0`  
**Git Commit Checkpoint:** Release candidate on `main`  
**Author:** Ayaan Khan (BSc Data Science, 3rd Year)  
**Project Title:** Multilingual Course Feedback Intelligence with Aspect Sentiment and Topic Drift  

---

## 🌟 Executive Release Overview

We are pleased to announce the production release of **FeedbackIQ v1.0.0**, a stakeholder-testable, enterprise-grade multilingual course feedback intelligence platform engineered specifically for higher-education academic quality assurance.

FeedbackIQ bridges the critical gap in traditional course evaluation pipelines by:
1. Natively processing **authentic multilingual and code-mixed collegiate text** (English, Hindi Devanagari, Marathi Devanagari, Hinglish, and Marathlish) with automated PII sanitization.
2. Decomposing compound student comments into **granular aspect sentiments** with verifiable verbatim **evidence spans**.
3. Monitoring temporal **semantic topic drift** across academic cohorts using the **Population Stability Index (PSI)**.
4. Enforcing **Human-in-the-Loop (HITL) Governance** with **1-click instant rollback** to guarantee institutional safety and prevent autonomous taxonomy corruption.

---

## 🚀 Key Features & Architectural Components

### 1. Multilingual Preprocessing & Language Identification (LID)
- **Devanagari Unicode Normalization:** Applies Unicode NFC normalization and strips rogue zero-width spaces/joiners (`\u200B`, `\u200C`, `\u200D`, `\uFEFF`), eliminating tokenization collisions across Indic text.
- **Automated PII Masking:** Detects and redacts student roll numbers, university email addresses, and Indian mobile numbers (`+91`), ensuring FERPA and DPDP compliance.
- **5-Class Script-Aware LID:** Differentiates English, Hindi, Marathi, Hinglish, and Marathlish with **80.9% Macro-F1** (82.8% Accuracy), successfully disambiguating homophonic markers (such as English *"the"* vs Hindi past tense).

### 2. Semantic Topic Modeling & Class-Based TF-IDF (c-TF-IDF)
- **Dense Semantic Projection:** Combines subword/character TF-IDF with TruncatedSVD and Cosine Agglomerative Clustering to group multilingual feedback into coherent topics.
- **Class-Based TF-IDF Keyword Extraction:** Computes topic-specific discriminative vocabulary rather than generic frequency rankings.
- **State-of-the-Art Topic Coherence:** Achieves Normalized Pointwise Mutual Information (**NPMI = +0.6352**), outperforming the classical Bag-of-Words Latent Dirichlet Allocation (LDA) baseline (**NPMI = -0.2666**) by **+0.9018**.

### 3. Aspect-Based Sentiment Analysis (ABSA) with Evidence Spans
- **Contrastive Clause Boundary Segmentation:** Splits compound comments conjoined by contrastive markers (*"however"*, *"but"*, *"lekin"*, *"pan"*, *"parantu"*) into discrete aspect clauses.
- **Dual Aspect Attribution:** Attributes opposing sentiments per topic facet (e.g. positive pedagogy vs negative lab infrastructure) rather than averaging out to misleading neutral. Achieves **55.3% Matched Aspect Macro-F1** (90.8% coverage).
- **Verbatim Evidence Spans:** Highlights the exact clause justifying each aspect sentiment score for explainability.

### 4. Graded Innovation Layer: Outlier Drift & HITL Governance
- **Pointwise Novelty Outlier Scorer:** Evaluates cosine distance to nearest cluster centroid ($d_i = 1 - \max_k \cos(\mathbf{e}_i, \mathbf{c}_k)$) with calibrated threshold $\tau = 0.40$ to flag emergent signals.
- **Population Stability Index (PSI) Drift Tracker:** Quantifies macro-level distribution divergence between cohorts, issuing automated alerts (`STABLE` $<0.10$, `MODERATE`, `SIGNIFICANT_DRIFT` $\ge 0.25$).
- **Dynamic Emerging Clusterer:** Clusters staged outlier embeddings into coherent topic proposals with c-TF-IDF keyword tags and SHA-256 hash fingerprints.
- **HITL Governance State Machine:** Enables curriculum committees to **Approve**, **Merge**, or **Discard** staged candidate topics.
- **Immutable Snapshotting & 1-Click Rollback:** Approvals create immutable version snapshots (`v1.0.0` $\rightarrow$ `v1.1.0`). If model degradation occurs, administrators can execute an instantaneous 1-click rollback back to `v1.0.0` in `< 500 ms`.

### 5. FastAPI High-Throughput REST Service
- Decoupled REST API exposing interactive Swagger / OpenAPI documentation at `/docs` and `/redoc`.
- Clean modular routers: `/health`, `/feedback`, `/topics`, `/sentiment`, `/drift`, and `/governance`.
- Strict Pydantic v2 data contracts with automated validation and error handling.

### 6. Interactive 5-View Streamlit Analytics Dashboard
- **View 1: 📊 Executive KPI Dashboard:** High-level metrics, language diversity donut chart, sentiment breakdown, and recent feedback stream.
- **View 2: 🔍 Topic Deep-Dive Explorer:** Topic selector, c-TF-IDF keyword tags, aspect polarity statistics, and representative exemplar quotes.
- **View 3: 📈 Longitudinal Trend & Drift Monitor:** Multi-term area trends, PSI drift gauge with alert indicators, and topic decomposition tables.
- **View 4: 🛡️ HITL Drift Governance Cockpit:** Staged review cards with interactive Approve, Merge, and Discard actions, plus 1-Click Rollback console.
- **View 5: 🧪 Live Feedback Inference Sandbox:** Interactive testing console with pre-populated multilingual presets, real-time pipeline execution, and evidence span visualization.

---

## 🧪 Automated Testing & Verification Evidence

All 36 automated tests pass with 100% success rate:
- **Unit Tests (`tests/unit/` - 26 tests):**
  - Dataset package, zero-leakage, split balance, and provenance verification (8 tests).
  - SQLAlchemy models, repository CRUD, and Pydantic validation (4 tests).
  - NLP normalizer, LID, baseline LDA, c-TF-IDF, and aspect sentiment (7 tests).
  - Novelty scoring, PSI drift, baseline vocabulary divergence, and governance (7 tests).
- **Integration Tests (`tests/integration/` - 6 tests):**
  - FastAPI REST API endpoints (health, topics, feedback, analyze, drift metrics).
  - Full HITL governance lifecycle (candidate staging $\rightarrow$ committee approval $\rightarrow$ version increment $\rightarrow$ 1-click rollback).
- **Security & Robustness Tests (`tests/security_robustness/` - 4 tests):**
  - Rigorous PII masking verification across emails, phones, and roll IDs.
  - Malformed Unicode, zero-width spaces, and Devanagari stress tests.
  - Adversarial prompt injection safety.
  - Extreme input length boundary constraints (min 3, max 1000).

---

## 📦 Deliverables Inventory

| Deliverable # | Artifact Path | Description | Status |
| :---: | :--- | :--- | :---: |
| **1** | `docs/problem_brief.md` | Problem brief, personas, misuse analysis, MoSCoW backlog | **Complete** |
| **2** | `docs/solution_design_pack.md` | Architecture, data flow, ERD, Pydantic contracts, STRIDE | **Complete** |
| **3** | `src/`, `course_feedback.db` | Working prototype (7 NLP modules, FastAPI, Streamlit, SQLite)| **Complete** |
| **4** | `docs/innovation_writeup.md` | Graded Innovation Layer formulation, drift math, ablation | **Complete** |
| **5** | `data/` | 1,000 comments across 4 terms, data dictionary, provenance | **Complete** |
| **6** | `.github/workflows/ci.yml`, Git PRs | Engineering evidence, CI pipeline, 36 passing tests | **Complete** |
| **7** | `docs/evaluation_dossier.md` | Quantitative dossier, NPMI coherence (+0.6352), error analysis | **Complete** |
| **8** | `Dockerfile.*`, `docker-compose.yml`, `docs/*_card.md` | Containerized demo, Model Card, System Card, Admin Guide | **Complete** |
| **9** | `worklog.md` | Granular worklog tracking 100.0 hours across 5 rubric categories | **Complete** |

---

## 🛠️ Verification & Quick Start

```bash
# Clone and setup
git checkout main
pip install -r requirements.txt

# Run complete test suite (36 tests)
python -m pytest tests/ -v

# Run services
uvicorn src.api.app:app --port 8000 &
streamlit run src/dashboard/app.py --server.port 8501
```

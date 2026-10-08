# Multilingual Course Feedback Intelligence with Aspect Sentiment and Topic Drift

**A BSc Data Science Capstone Project**  
*An enterprise-grade NLP prototype for higher-education stakeholders to analyze multilingual student feedback, attribute sentiment per course topic, and govern topic drift with human-in-the-loop oversight.*

---

## 📌 Project Overview
Course evaluations in multilingual regions (e.g. India) arrive in a mix of English, Hindi, Marathi, and code-mixed formats (*Hinglish*, *Marathlish*). Traditional sentiment analyzers fail because:
1. They ignore language diversity or break on non-Latin / code-mixed scripts.
2. They produce a flat, single document-level score (masking mixed sentiment, e.g., great teaching vs. terrible lab infrastructure).
3. They rely on fixed, static topic taxonomies that fail to detect emerging student concerns (topic drift, such as new AI policies or infrastructure failures).

This project delivers an end-to-end intelligence system with a **Graded Innovation Layer**: an Outlier & Drift Detection Engine paired with a Human-in-the-Loop (HITL) approval and 1-click rollback workflow.

---

## 🚀 Key Modules
1. **Multilingual Preprocessing & LID:** Script-aware Unicode Devanagari normalization, noise filtering, and Language Identification via lexical marker sets and script heuristics (EN, HI, MR, Hinglish, Marathlish).
2. **Topic Modeling:** Dual-model architecture comparing a classical Latent Dirichlet Allocation (LDA) baseline with an Advanced Multilingual Topic Engine (subword & word TF-IDF + TruncatedSVD + Cosine Agglomerative Clustering + c-TF-IDF keyword extraction).
3. **Aspect-Based Sentiment Analysis (ABSA):** Clause-level sentiment analyzer scoring sentiment *per topic facet*, benchmarked against a document-level multilingual lexicon baseline.
4. **Keyword & Trend Tracking:** Aggregates topic velocity and student satisfaction shifts across academic semesters.
5. **Representative Comment Extraction:** Selects central exemplars per topic via centroid cosine similarity for human review.
6. **INNOVATION LAYER (Topic Drift & Governance):**
   - Detects Out-of-Distribution (OOD) emerging feedback using dense centroid distance novelty scores ($d_i = 1.0 - \max_k \cos(e_i, c_k)$).
   - Computes Population Stability Index (PSI) over multi-semester batches.
   - Accumulates and clusters novel feedback into candidate topics via `EmergingTopicClusterer`.
   - Exposes a controlled HITL approval state machine with 1-click rollback to historical topic snapshots.
7. **FastAPI & Streamlit UI:** Documented REST API (`/docs`) and an interactive intelligence dashboard.

---

## 📂 Repository Structure
```
capstone_course_feedback/
├── .github/workflows/      # Automated CI pipeline
├── data/
│   ├── raw/                # 1,000 synthetic multilingual comments
│   ├── processed/          # Stratified train/val/test splits
│   ├── data_dictionary.md  # Schema documentation
│   └── dataset_provenance.md# Synthesis protocol & ethical simulation notes
├── docs/                   # 9 Mandatory Capstone Deliverables
├── src/
│   ├── preprocessing/      # Text normalizers & Language ID
│   ├── topic_modeling/     # LDA baseline & Multilingual c-TF-IDF engine
│   ├── sentiment/          # Lexicon baseline & Clause-level ABSA
│   ├── innovation/         # Drift detection, clustering, HITL rollback
│   ├── database/           # SQLite models & repositories
│   ├── api/                # FastAPI application & routes
│   └── dashboard/          # Streamlit multi-page dashboard
├── tests/                  # Unit, integration, and security test suites
├── scripts/                # Pipeline runners and benchmarking
├── docker/                 # Dockerfiles & docker-compose.yml
├── requirements.txt        # Python dependencies
└── worklog.md              # Rubric-mapped time tracking (~100 hours)
```

---

## 🛠️ Quickstart

### Prerequisites
- Python 3.11+
- Git
- Docker & Docker Compose (optional for containerized deployment)

### 1. Clone & Setup
```bash
git clone https://github.com/ayaansgit57/capstone_course_feedback.git
cd capstone_course_feedback
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Generate Dataset & Run Pipeline
```bash
python data/generate_dataset.py
python scripts/run_pipeline.py
```

### 3. Launch Services
```bash
# Terminal 1: Launch FastAPI Backend
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Launch Streamlit Dashboard
streamlit run src/dashboard/app.py
```
- API Docs: `http://localhost:8000/docs`
- Dashboard UI: `http://localhost:8501`

### 4. Run Test Suite
```bash
python -m pytest tests/ -v
```
- **Verified Status:** `36 passed` across unit, integration, and security suites with per-test database isolation.

---

## 📊 Worklog & Grading Rubric
Hours and verification sessions are tracked in [worklog.md](worklog.md), reflecting initial scaffolding and ongoing student review toward the 100-hour capstone requirement.

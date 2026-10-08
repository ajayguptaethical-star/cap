# System Card: Multilingual Course Feedback Intelligence System

**System Name:** FeedbackIQ End-to-End Intelligence Platform  
**System Version:** `v1.0.0` (Production Release)  
**Architecture:** Decoupled Modular Monolith (FastAPI + Streamlit + SQLite)  
**Operating Environment:** Cross-platform (Linux / Windows / Docker Compose)  

---

## 1. System Architecture & Component Mapping

FeedbackIQ is structured as a decoupled, reproducible modular monolith designed for institutional on-premises or private cloud deployment:

```
┌───────────────────────────────────────────────────────────────┐
│                     USER INTERACTION LAYER                    │
│   Streamlit Web Dashboard (Port 8501)                         │
│   ├── View 1: Executive KPI Dashboard                         │
│   ├── View 2: Topic Deep-Dive Explorer                        │
│   ├── View 3: Longitudinal Trend & PSI Drift Monitor          │
│   ├── View 4: HITL Governance & 1-Click Rollback Cockpit      │
│   └── View 5: Live Real-Time Inference Sandbox                │
└──────────────────────────────┬────────────────────────────────┘
                               │ HTTP / Direct ORM
┌──────────────────────────────▼────────────────────────────────┐
│                       REST API SERVICE                        │
│   FastAPI Backend (Port 8000)                                 │
│   ├── /api/v1/health       - Readiness & version probes       │
│   ├── /api/v1/feedback     - Single/batch ingestion & query   │
│   ├── /api/v1/topics       - Taxonomy retrieval & versions    │
│   ├── /api/v1/analyze      - Live NLP sandbox inference       │
│   ├── /api/v1/drift        - PSI metrics & pending review     │
│   └── /api/v1/governance   - Committee approve/merge/rollback │
└──────────────────────────────┬────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────┐
│                   NLP & INNOVATION ENGINE                     │
│   ├── normalizer.py        - Unicode Devanagari NFC & PII     │
│   ├── lang_detector.py     - 5-class script-aware LID         │
│   ├── bertopic_engine.py   - Subword SVD + c-TF-IDF ranker    │
│   ├── aspect_sentiment.py  - Multi-clause ABSA with evidence  │
│   ├── drift_detector.py    - Outlier distance & PSI tracker   │
│   ├── emerging_clusterer.py- Outlier agglomerative clustering │
│   └── governance.py        - State machine & immutable snaps  │
└──────────────────────────────┬────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────┐
│                  DATA PERSISTENCE LAYER                       │
│   SQLite Database (course_feedback.db)                        │
│   ├── feedback (1,000 baseline records)                       │
│   ├── topic_versions (Immutable snapshot history)             │
│   ├── topics (Active institutional catalog)                   │
│   ├── aspect_sentiments (Relational topic polarities)         │
│   └── drift_candidates (HITL review staging queue)            │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. Resource Requirements & Hardware Boundaries

To ensure 100% reproducibility in academic evaluations and budget-constrained educational institutions, FeedbackIQ is engineered for zero-GPU operation:

- **Minimum Compute:** 2 vCPU cores, 2.0 GB RAM
- **Recommended Compute:** 4 vCPU cores, 4.0 GB RAM
- **Storage Footprint:** < 500 MB (including Python runtime, scikit-learn models, and SQLite database)
- **Inference Latency:**
  - Single feedback comment: **~12–25 ms**
  - Batch of 100 comments: **~850 ms**
  - Cross-semester PSI calculation (500 records): **~45 ms**
- **Throughput:** ~40 requests/second on standard 4-core commodity hardware.

---

## 3. Operational Security & Privacy Controls

1. **Mandatory PII Scrubbing:** All raw text ingested via `/api/v1/feedback` or analyzed in `/api/v1/analyze` undergoes pre-persistence redaction of Indian mobile phone formats (`+91`), academic email domains, and roll numbers.
2. **SQL Injection Defense:** All queries are executed through SQLAlchemy ORM parameterized statements, preventing raw SQL string concatenation.
3. **CORS & Network Isolation:** In Docker Compose, the database file is mounted in a private volume (`feedback_storage`) accessible only by the internal containers on `feedback_network`.

---

## 4. Resilience & Failure Fallback Modes

| Failure Scenario | System Behavior & Mitigation Protocol |
| :--- | :--- |
| **Model Degradation / Drift Poisoning** | **1-Click Rollback:** If an approved topic causes semantic drift or instability, an administrator selects the previous version (e.g. `v1.0.0`) in View 4 and restores active state in `< 500 ms`. |
| **Malformed Unicode / Non-Standard Text** | **NFC Fallback:** Text with rogue zero-width spaces or uncomposed Devanagari vowels is normalized automatically before tokenization. |
| **Database Lock / High Concurrency** | **SQLite WAL Mode:** The connection pool enforces `check_same_thread=False` with Write-Ahead Logging (WAL) support for concurrent reads. |
| **Network Disconnection between UI & API** | **Direct DB Fallback:** The Streamlit dashboard includes native repository fallback logic, allowing standalone execution even if the REST API port is inaccessible. |

---

## 5. Maintenance & Telemetry

- **Health Checks:** `/api/v1/health` verifies database connectivity and reports active model version and record counts.
- **Audit Logging:** Every administrative governance action (**Approve**, **Merge**, **Discard**, **Rollback**) records reviewer identity, timestamp, and rationale in the immutable `drift_candidates` and `topic_versions` tables.

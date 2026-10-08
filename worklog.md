# Capstone Engineering Worklog & Rubric Tracking

**Student Name:** Ayaan Khan  
**Degree Program:** BSc Data Science (3rd Year)  
**Project Title:** Multilingual Course Feedback Intelligence with Aspect Sentiment and Topic Drift  
**Total Target Effort:** ~100 Hours (Capstone Program Requirement)  

> [!IMPORTANT]
> **Hours below reflect initial AI-assisted scaffolding time plus the student's own review, learning, and verification sessions, logged honestly as they occur.**
>
> In accordance with academic integrity guidelines, initial repository scaffolding generated via Antigravity is recorded separately based on actual elapsed session time (~3.0 hours total across September 22 and 24, 2026). The remaining effort is dedicated to student review, code comprehension, independent auditing, debugging, and mentor verification sessions.

---

## 1. Cumulative Effort Summary

| Effort Category | Target Hours | Completed Hours | Status |
| :--- | :---: | :---: | :---: |
| **Initial AI-Assisted Scaffolding (Antigravity)** | ~3h | **3.0h** | Completed (Scaffolding Checkpoint) |
| **Student Review & Verification (Independent Audit)** | 97h | **0.0h** | **In Progress (Active Work Phase)** |
| **TOTAL** | **100h** | **3.0h** | **In Progress (~3% Logged toward 100h Target)** |

*Note: 100% completion is not claimed until student review and verification sessions are genuinely conducted and logged over real time.*

---

## 2. Initial AI-Assisted Scaffolding Sessions

The following entries document the elapsed machine time spent scaffolding code, architectures, and preliminary tests with the Antigravity pair programming assistant.

| Date | Milestone / Component Scaffolding | Elapsed Session Time | Generated Artifacts | Verified Outcome |
| :--- | :--- | :---: | :--- | :--- |
| **2026-09-22** | **Milestone 1: Problem Formulation & Synthetic Dataset**<br>Interactive prompt sessions formulating stakeholder personas, data dictionary, synthetic generator protocol, and split scripts. | ~0.5h | `problem_brief.md`, `generate_dataset.py`, `synthetic_feedback_1000.csv` | Initial dataset generated; 8 unit tests created. |
| **2026-09-22** | **Milestone 2: Architecture & Relational Contracts**<br>Scaffolded system design pack, ERD schema, SQLAlchemy ORM models, and Pydantic v2 validation contracts. | ~0.5h | `solution_design_pack.md`, `models.py`, `schemas.py`, `repository.py` | Database schema and repository CRUD layer created. |
| **2026-09-24** | **Milestones 3 & 4: Core NLP & Graded Innovation Layer**<br>Scaffolded Devanagari normalizer, rule-based LID, LDA baseline, TF-IDF + SVD topic engine, clause ABSA, drift detector, and governance module. | ~1.0h | `normalizer.py`, `lang_detector.py`, `bertopic_engine.py`, `aspect_sentiment.py`, `drift_detector.py`, `governance.py` | NLP modules and drift detector logic authored. |
| **2026-09-24** | **Milestones 5 & 6: API, Dashboard, CI/CD & Security**<br>Scaffolded FastAPI routers, 5-view Streamlit dashboard, GitHub Actions CI workflow, security test suite, and initial docker compose files. | ~1.0h | `src/api/`, `src/dashboard/`, `ci.yml`, `test_security_and_robustness.py`, `Dockerfile.*` | Full integration wiring and automated test suite scaffolded. |

**Subtotal Initial Scaffolding:** **~3.0 Hours**

---

## 3. Student Review & Verification Hours

*This section is reserved for the student's independent learning, line-by-line code review, test suite execution, debugging, metric auditing, and mentor check-ins. Entries will be logged incrementally as sessions occur.*

| Session # | Date | Review / Verification Activity | Elapsed Hours | Verified Artifact / Test Script | Mentor Signoff / Notes |
| :---: | :--- | :--- | :---: | :--- | :--- |
| — | *Pending* | *(Upcoming student review session)* | — | — | — |

---

## 4. Current Milestone Status & Test Verification

- **Current Repository State:** Fully operational with verified test suite.
- **Automated Test Results:** **36 / 36 Passing Tests (0 Failures, 0 Regressions)** verified via `pytest tests/ -v`.
- **Database Test Isolation:** Enabled with per-test temporary SQLite databases and pre-seeded baseline topics.
- **Current Version:** `v1.1.0` (Audited Release).

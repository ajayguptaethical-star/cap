# FeedbackIQ: Administrator & End-User Operational Manual

**Project Title:** Multilingual Course Feedback Intelligence with Aspect Sentiment and Topic Drift  
**Target Audience:** University Leadership, Department Chairs, Curriculum Review Committees, Faculty, and System Administrators  
**System Version:** `v1.0.0` (Production Release)  

---

## 1. Quick Start & Deployment

### Option A: Local Native Execution (Recommended for Evaluation)

```bash
# 1. Clone repository and navigate to workspace
cd capstone_course_feedback

# 2. Install dependencies (Python 3.11+ recommended)
pip install -r requirements.txt

# 3. Initialize SQLite database and run NLP pipeline
python scripts/run_pipeline.py

# 4. Launch FastAPI REST Service (Terminal 1)
uvicorn src.api.app:app --reload --port 8000

# 5. Launch Streamlit Analytics Dashboard (Terminal 2)
streamlit run src/dashboard/app.py --server.port 8501
```

- **Interactive UI:** Open browser at `http://localhost:8501`
- **Interactive OpenAPI / Swagger Documentation:** Open browser at `http://localhost:8000/docs`

---

### Option B: Docker Compose Multi-Container Orchestration

```bash
# Build and launch both FastAPI and Streamlit services
docker compose up --build -d

# Check service health status
docker compose ps

# View container logs
docker compose logs -f
```

To stop the containers:
```bash
docker compose down
```

---

## 2. End-User Guide (Faculty & Academic Leadership)

### View 1: 📊 Executive KPI Dashboard
- **Total Feedback & Multilingual Coverage:** Shows total volume of course reviews and percentage of multilingual/code-mixed responses (targeting $\ge 65\%$).
- **Language Donut Chart:** Visualizes distribution across English (`EN`), Hindi (`HI`), Marathi (`MR`), Hinglish (`HINGLISH`), and Marathlish (`MARATHLISH`).
- **Topic Volume Bar Chart:** Displays feedback counts allocated across active institutional categories.
- **Recent Submissions Stream:** Live feed of verified student comments displaying course code, instructor ID, primary topic, and sentiment tags.

### View 2: 🔍 Topic Deep-Dive Explorer
1. Select any institutional topic from the dropdown selector (e.g. *TOPIC_1 - Pedagogy & Teaching Quality*).
2. Inspect the **c-TF-IDF Discriminative Keyword Signature** to understand distinctive vocabulary associated with that topic.
3. Review the **Aspect Sentiment Breakdown** to see positive, neutral, and negative distributions specifically for that facet.
4. Read **Representative Exemplar Quotes** displaying authentic verbatim comments that exemplify student sentiment.

### View 5: 🧪 Live Feedback Inference Sandbox
1. Select a multilingual preset or type arbitrary text into the input box:
   - *Example (Hinglish):* `"Teaching standard was decent but Wi-Fi connection bilkul bekar tha and lab machines hung ho rahi thi."`
2. Click **🚀 Analyze Feedback**.
3. View instant 7-stage NLP pipeline predictions:
   - **Language ID:** Detected language, script type, and confidence percentage.
   - **Primary Topic:** Thematic classification.
   - **Aspect Breakdown:** Per-topic sentiment labels, polarity scores ($-1.0$ to $+1.0$), and verbatim **Evidence Spans**.
   - **Novelty Outlier Score:** Indicator flagging whether comment is in-catalog or represents emerging drift ($\ge 0.40$).

---

## 3. Administrator Guide (Curriculum Committees & Deans)

### View 3: 📈 Longitudinal Trend & Drift Monitor
1. **Area Trend Chart:** Track how topic mentions shift across academic terms (Fall 2024 $\rightarrow$ Spring 2026).
2. **PSI Drift Gauge:**
   - Select reference baseline semester (e.g. `Fall 2024`) and comparison semester (e.g. `Spring 2026`).
   - The gauge computes the Population Stability Index:
     - **$\text{PSI} < 0.10$ (`STABLE` - Green):** Routine term-to-term variation.
     - **$0.10 \le \text{PSI} < 0.25$ (`MODERATE_SHIFT` - Amber):** Mild shifts; advisory monitoring.
     - **$\text{PSI} \ge 0.25$ (`SIGNIFICANT_DRIFT` - Red):** Structural divergence; triggers Stage 2 review.
3. **Decomposition Table:** View each topic's individual mathematical contribution to overall PSI.

### View 4: 🛡️ HITL Drift Governance Cockpit
The governance cockpit ensures that **no autonomous model mutations** happen without explicit human approval.

#### Step 1: Review Staged Candidates
In the **Staged Drift Candidates** tab, inspect novel outlier clusters detected by the engine (e.g. *Candidate #1: GenAI Policy Concerns* with 28 comments, NPMI coherence +0.6125, keywords: *chatgpt, ai tool, copilot*).

#### Step 2: Choose Governance Action
- **Option 1: ✅ Approve as New Official Topic:**
  - Enter official catalog name (e.g. `Generative AI Academic Policies`).
  - Enter reviewer notes and Admin ID (`dr_sharma`).
  - Click **Confirm Approval & Increment Version**.
  - The system creates a new immutable version snapshot (e.g. `v1.0.0` $\rightarrow$ `v1.1.0`), adds the topic to the active catalog, and archives the previous version.
- **Option 2: 🔄 Merge into Existing Topic:**
  - Select an existing topic (e.g. `TOPIC_2 - Assignments & Homework Workload`).
  - Folds the candidate cluster into that topic without modifying catalog taxonomy.
- **Option 3: 🗑️ Discard Candidate:**
  - Rejects the cluster as spurious spam or unaligned noise.

#### Step 3: Emergency 1-Click Rollback
If an approved topic introduces unexpected bias or model degradation:
1. Open the **Model Version Snapshots & 1-Click Rollback** tab.
2. Select target historical version (e.g. `v1.0.0`).
3. Click **🚨 Execute Instant Rollback**.
4. The system reactivates `v1.0.0` atomically in under 500 ms with complete audit logs preserved.

---

## 4. API Reference Summary

| Method | Endpoint | Description | Request Body / Query Params |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | System readiness & active model version | None |
| `GET` | `/api/v1/topics` | List active catalog topics | None |
| `GET` | `/api/v1/topics/versions` | List all historical model snapshots | None |
| `GET` | `/api/v1/feedback` | Query feedback records with multi-filters | `term`, `course`, `topic`, `lang`, `limit` |
| `POST`| `/api/v1/feedback` | Ingest single feedback comment | `raw_text`, `course_code`, `instructor_id` |
| `POST`| `/api/v1/analyze` | Real-time sandbox inference with spans | `text`, `primary_topic` |
| `GET` | `/api/v1/drift/metrics` | Calculate PSI drift across terms | `ref_term`, `curr_term` |
| `GET` | `/api/v1/drift/pending` | List candidates awaiting review | None |
| `POST`| `/api/v1/governance/approve`| Approve candidate & increment version | `candidate_id`, `approved_name`, `admin_notes` |
| `POST`| `/api/v1/governance/merge` | Merge candidate into existing topic | `candidate_id`, `merge_into_topic_code` |
| `POST`| `/api/v1/governance/discard`| Discard candidate as noise | `candidate_id`, `admin_notes` |
| `POST`| `/api/v1/governance/rollback`| Restore historical version snapshot | `target_version_tag`, `admin_notes` |

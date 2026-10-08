# Deliverable 5A: Course Feedback Data Dictionary

**Schema Version:** 1.0.0  
**Target Entities:** Student Course Feedback, Topic Taxonomy, Aspect-Level Sentiment, Temporal Metadata  
**Primary Storage Format:** CSV (Raw & Processed) and SQLite Relational Database  

---

## 1. Primary Feedback Table (`feedback`)

This table stores individual student course evaluation comments, both raw and normalized, along with ground truth simulation labels (for evaluation) and downstream model inference outputs.

| Column Name | Data Type | Nullable | Constraints & Valid Range | Description | Example Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `comment_id` | `VARCHAR(36)` | No | Primary Key, UUIDv4 format | Unique identifier for each student feedback entry. | `e4b3c2a1-7890-4def-9876-123456789abc` |
| `timestamp` | `DATETIME` | No | ISO-8601 string (`YYYY-MM-DDTHH:MM:SS`) | Precise date and time when the feedback was recorded. | `2026-03-14T11:42:19` |
| `academic_term` | `VARCHAR(20)` | No | `Fall 2025`, `Spring 2026`, `Summer 2026`, `Fall 2026` | Academic evaluation semester / cohort grouping. | `Spring 2026` |
| `course_code` | `VARCHAR(10)` | No | Format: `[A-Z]{2,3}[0-9]{3}` | Anonymized course code. | `DS101`, `ML202`, `CS303`, `MATH201` |
| `instructor_id` | `VARCHAR(15)` | No | E.g., `INST_01` to `INST_10` | Anonymized faculty instructor identifier. | `INST_03` |
| `raw_text` | `TEXT` | No | $10 \le \text{length} \le 1,000$ chars | Original raw comment as submitted by the student, containing original script, slang, or emojis. | *"Prof explains derivations clearly, but lab servers crash constantly!"* |
| `cleaned_text` | `TEXT` | Yes | Unicode NFC normalized | Post-preprocessing text with normalized Devanagari characters, trimmed whitespace, and redacted PII. | *"Prof explains derivations clearly, but lab servers crash constantly!"* |
| `true_language` | `VARCHAR(10)` | No | `en`, `hi`, `mr`, `hi-en`, `mr-en` | Ground truth language classification. `hi-en` denotes Hinglish, `mr-en` denotes Marathlish. | `hi-en` |
| `script_type` | `VARCHAR(15)` | No | `Latin`, `Devanagari`, `Mixed` | Primary orthographic script used in the comment. | `Devanagari` |
| `primary_topic` | `VARCHAR(30)` | No | Valid taxonomy code (e.g., `TOPIC_1` to `TOPIC_6`, `DRIFT_1`, `DRIFT_2`) | Dominant theme or pedagogical aspect addressed in the comment. | `TOPIC_1` |
| `secondary_topic`| `VARCHAR(30)`| Yes | Null or valid taxonomy code | Secondary theme addressed in compound multi-aspect comments. | `TOPIC_5` |
| `aspect_sentiment`| `JSON` | No | Valid JSON string: `{"TOPIC_X": "sentiment"}` | Ground truth sentiment mapping per mentioned topic (`positive`, `negative`, `neutral`). | `{"TOPIC_1": "positive", "TOPIC_5": "negative"}` |
| `overall_sentiment`| `VARCHAR(10)`| No | `positive`, `negative`, `neutral` | Holistic comment-level sentiment. | `neutral` |
| `is_emergent_drift`| `BOOLEAN` | No | `True` or `False` | Ground truth flag indicating whether this comment belongs to an emerging out-of-distribution theme. | `False` |

---

## 2. Topic Taxonomy Table (`topics`)

Defines the official institutional topic catalog governed by the Academic Quality Committee.

| Column Name | Data Type | Nullable | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `topic_code` | `VARCHAR(30)` | No | Machine-readable topic key. | `TOPIC_1` |
| `topic_name` | `VARCHAR(100)`| No | Human-readable title for dashboards and reports. | `Pedagogy & Lecture Delivery` |
| `description` | `TEXT` | No | Scope and definition of what falls under this topic. | Pacing, slide clarity, conceptual explanations, classroom engagement. |
| `core_keywords`| `TEXT` | No | Comma-separated top seed keywords across languages. | `lecture, explain, speed, clarity, samajh, शिकवणे, सोपे` |
| `is_active` | `BOOLEAN` | No | Whether the topic is currently active in the production classifier. | `True` |

---

## 3. Governance & Topic Drift Candidate Table (`drift_candidates`)

Maintains the audit log of detected Out-of-Distribution emerging clusters pending human review.

| Column Name | Data Type | Nullable | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `candidate_id` | `INTEGER` | No | Auto-incrementing primary key. | `1` |
| `cluster_hash` | `VARCHAR(64)` | No | SHA-256 hash identifying the outlier cluster embeddings. | `a7f93b...` |
| `detected_at` | `DATETIME` | No | Timestamp of initial cluster discovery. | `2026-06-15T09:30:00` |
| `academic_term` | `VARCHAR(20)` | No | Term during which the cluster emerged. | `Summer 2026` |
| `proposed_label`| `VARCHAR(100)`| No | c-TF-IDF generated label based on top terms. | `genai_chatgpt_policy` |
| `top_keywords` | `TEXT` | No | Top extracted multilingual keywords. | `chatgpt, ai tool, detector, copyleaks, policy` |
| `sample_size` | `INTEGER` | No | Number of comments assigned to this emerging cluster. | `28` |
| `coherence_score`| `FLOAT` | No | Mathematical topic coherence score ($C_v$). | `0.584` |
| `status` | `VARCHAR(20)` | No | `PENDING_REVIEW`, `APPROVED`, `MERGED`, `DISCARDED` | `PENDING_REVIEW` |
| `reviewed_by` | `VARCHAR(50)` | Yes | Username of the administrator who reviewed the candidate. | `dr_sharma` |
| `review_notes` | `TEXT` | Yes | Human rationale recorded during approval or rejection. | *"Approved as official topic for Fall 2026."* |

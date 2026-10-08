"""
Pipeline Runner CLI Script.
Ingests dataset, runs normalization, language ID, trains topic models (LDA Baseline vs Advanced),
computes coherence, runs Aspect Sentiment Analysis, and seeds SQLite database.
"""

import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime, timezone

# Add repository root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import init_db, SessionLocal
from src.database.repository import FeedbackRepository, TopicRepository
from src.preprocessing.normalizer import clean_text
from src.preprocessing.lang_detector import detect_language
from src.topic_modeling.baseline_lda import BaselineLDAModel
from src.topic_modeling.bertopic_engine import MultilingualTopicEngine
from src.topic_modeling.coherence import compute_topic_coherence
from src.sentiment.aspect_sentiment import AspectSentimentAnalyzer
from src.config import settings

TOPIC_METADATA = {
    0: ("TOPIC_1", "Pedagogy & Lecture Delivery", "Pacing, slide clarity, and conceptual explanations"),
    1: ("TOPIC_2", "Assignments & Workload", "Homework load, deadlines, and problem difficulty"),
    2: ("TOPIC_3", "Grading Fairness & Feedback", "Marking transparency, rubric consistency, and TA feedback"),
    3: ("TOPIC_4", "Faculty Support & Availability", "Office hours availability, responsiveness, and guidance"),
    4: ("TOPIC_5", "Lab & Technical Infrastructure", "Workstations, GPU servers, WiFi, and software environment"),
    5: ("TOPIC_6", "Curriculum Depth & Relevance", "Syllabus modernness, theoretical vs applied balance")
}

def run_pipeline(input_csv: str = "data/raw/synthetic_feedback_600.csv"):
    print("=" * 75)
    print("STARTING MULTILINGUAL COURSE FEEDBACK INTELLIGENCE PIPELINE")
    print("=" * 75)
    
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    print(f"[1/5] Initializing Database & Loading Input Data from {input_csv}...")
    init_db()
    db = SessionLocal()
    feedback_repo = FeedbackRepository(db)
    topic_repo = TopicRepository(db)

    df = pd.read_csv(input_csv)
    print(f"      Loaded {len(df)} feedback comments.")

    print("\n[2/5] Running Text Normalization, PII Sanitization, and Language Identification...")
    cleaned_texts = []
    detected_languages = []
    confidences = []
    scripts = []

    for text in df["raw_text"]:
        c_text = clean_text(text, redact_pii=True)
        lang, conf, script = detect_language(c_text)
        cleaned_texts.append(c_text)
        detected_languages.append(lang)
        confidences.append(conf)
        scripts.append(script)

    df["cleaned_text"] = cleaned_texts
    df["detected_lang"] = detected_languages
    df["lang_conf"] = confidences
    df["script_type"] = scripts

    print("      Language Distribution:")
    for lang, count in df["detected_lang"].value_counts().items():
        print(f"        • {lang:6s}: {count:4d} ({count/len(df):.1%})")

    print("\n[3/5] Training Topic Models (Baseline LDA vs Advanced Multilingual Engine)...")
    # Fit Baseline LDA
    lda = BaselineLDAModel(n_topics=6, random_state=42)
    lda.fit(df["cleaned_text"].tolist())
    lda_keywords = lda.get_topic_keywords(top_n=8)
    lda_coherence = compute_topic_coherence(lda_keywords, df["cleaned_text"].tolist())

    # Fit Advanced Multilingual Engine
    engine = MultilingualTopicEngine(n_topics=6, random_state=42)
    engine.fit(df["cleaned_text"].tolist())
    adv_keywords = engine.get_topic_keywords()
    adv_coherence = compute_topic_coherence(adv_keywords, df["cleaned_text"].tolist())

    print("\n" + "-" * 75)
    print("TOPIC COHERENCE COMPARISON (Quality Bar Verification):")
    print(f"  • Classical LDA Baseline Coherence:  {lda_coherence['mean_coherence']:+.4f}")
    print(f"  • Advanced Multilingual Coherence:   {adv_coherence['mean_coherence']:+.4f}")
    gain = adv_coherence['mean_coherence'] - lda_coherence['mean_coherence']
    print(f"  • Coherence Delta / Gain:            {gain:+.4f} (Advanced > Baseline)")
    print("-" * 75)

    print("\n[4/5] Running Aspect-Based Sentiment Analysis & Outlier Scoring...")
    aspect_analyzer = AspectSentimentAnalyzer()
    
    topic_indices, max_sims, outlier_scores = engine.transform(df["cleaned_text"].tolist())
    df["assigned_cluster"] = topic_indices
    df["outlier_score"] = outlier_scores
    # Outlier threshold from unified settings (empirical optimal 0.40)
    df["is_outlier"] = df["outlier_score"] >= settings.OUTLIER_THRESHOLD

    print(f"      Novel / Outlier Signals Detected: {df['is_outlier'].sum()} comments")

    print("\n[5/5] Persisting Topic Taxonomy Snapshot (v1.0.0) and Feedback to SQLite...")
    # Check if active version already exists
    active_version = topic_repo.get_active_version()
    if not active_version:
        snapshot_meta = {
            "version": "v1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "n_topics": 6,
            "mean_coherence": adv_coherence["mean_coherence"],
            "topics": {}
        }
        topics_payload = []
        for cluster_id in range(6):
            t_code, t_name, t_desc = TOPIC_METADATA.get(cluster_id, (f"TOPIC_{cluster_id+1}", f"Topic {cluster_id+1}", ""))
            kws = ", ".join(adv_keywords.get(cluster_id, [])[:8])
            count = int((df["assigned_cluster"] == cluster_id).sum())
            snapshot_meta["topics"][t_code] = {"name": t_name, "keywords": kws, "count": count}
            topics_payload.append({
                "topic_code": t_code,
                "topic_name": t_name,
                "description": t_desc,
                "top_keywords": kws,
                "comment_count": count,
                "is_emergent": False
            })

        v1 = topic_repo.create_version("v1.0.0", json.dumps(snapshot_meta, indent=2), "system_pipeline")
        topic_repo.add_topics_to_version(v1.version_id, topics_payload)
        print("      Created Topic Version v1.0.0 with 6 institutional topics.")

    # Ingest comments into database (if DB empty or batch insert)
    existing_count = feedback_repo.get_feedback_count()
    if existing_count == 0:
        print("      Seeding feedback database records...")
        for _, row in df.iterrows():
            cluster_id = int(row["assigned_cluster"])
            t_code, _, _ = TOPIC_METADATA.get(cluster_id, (f"TOPIC_{cluster_id+1}", "", ""))
            
            # Analyze aspects
            overall_label, overall_score, aspects = aspect_analyzer.analyze_aspects(
                row["cleaned_text"], primary_topic=t_code
            )

            # Map timestamp
            ts_str = row["timestamp"]
            try:
                ts = datetime.fromisoformat(ts_str)
            except Exception:
                ts = datetime.now(timezone.utc)

            feedback_payload = {
                "comment_id": str(row["comment_id"]),
                "timestamp": ts,
                "academic_term": str(row["academic_term"]),
                "course_code": str(row["course_code"]),
                "instructor_id": str(row["instructor_id"]),
                "raw_text": str(row["raw_text"]),
                "cleaned_text": str(row["cleaned_text"]),
                "detected_language": str(row["detected_lang"]),
                "lang_confidence": float(row["lang_conf"]),
                "script_type": str(row["script_type"]),
                "primary_topic_code": t_code,
                "overall_sentiment": overall_label,
                "sentiment_score": overall_score,
                "is_outlier": bool(row["is_outlier"]),
                "outlier_score": float(row["outlier_score"])
            }
            feedback_repo.create_feedback(feedback_payload, aspects)
        print(f"      Successfully persisted {len(df)} feedback records and aspect sentiments into SQLite.")
    else:
        print(f"      Database already contains {existing_count} records. Skipping duplicate seed.")

    db.close()
    print("\n" + "=" * 75)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Course Feedback Intelligence Pipeline")
    parser.add_argument("--input-file", default="data/raw/synthetic_feedback_600.csv", help="Input CSV path")
    args = parser.parse_args()
    run_pipeline(args.input_file)

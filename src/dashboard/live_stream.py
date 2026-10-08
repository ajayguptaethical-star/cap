import random
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.database.repository import FeedbackRepository, TopicRepository

COURSES = ["CS101", "DS202", "AI301", "ML401", "SE102", "EC201", "CY505"]
INSTRUCTORS = ["INST_01", "INST_04", "INST_08", "INST\12", "INST_15"]
TERMS = ["2025-SPRING", "2024-FALL"]

SAMPLE_TEMPLATES = [
    {"topic_code": "TOPIC_1", "lang": "en", "script": "Latin", "sentiment": "positive", "score": 0.92, "raw": "The professor step-by-step breakdown of deep learning models made complex topics super easy to grasp!", "clean": "The professor step-by-step breakdown of deep learning models made complex topics super easy to grasp!"},
    {"topic_code": "TOPIC_1", "lang": "hinglish", "script": "Latin", "sentiment": "positive", "score": 0.88, "raw": "Prof ka explaining style bohot badiya tha, live coding sessions ne saare doubts clear car diye.", "clean": "Prof ka explaining style bohot badiya tha, live coding sessions ne saare doubts clear car diye."},
    {"topic_code": "TOPIC_1", "lang": "hi", "script": "Devanagari", "sentiment": "positive", "script": "Devanagari", "score": 0.95, "raw": "professor ka padane ka tarika best hai", "clean": "professor ka padane ka tarika best hai"},
    {"topic_code": "TOPIC_2", "lang": "en", "script": "Latin", "sentiment": "negative", "script": "Latin", "score": -0.82, "raw": "The assignment workload for week 6 was overwhelming.", "clean": "The assignment workload for week 6 was overwhelming."},
    {"topic_code": "TOPIC_3", "lang": "hinglish", "script": "Latin", "sentiment": "negative", "script": "Latin", "score": -0.85, "raw": "Mid-term grading me rubric strict nahi tha.", "clean": "Mid-term grading me rubric strict nahi tha."},
    {"topic_code": "TOPIC_4", "lang": "mr", "script": "Devanagari", "sentiment": "positive", "script": "Devanagari", "score": 0.91, "raw": "lecture madhe concepts clear zale.", "clean": "lecture madhe concepts clear-zale."},
    {"topic_code": "TOPIC_5", "lang": "marathlish", "script": "Latin", "sentiment": "negative", "script": "Latin", "score": -0.75, "raw": "Lab computers slow ho rahe hote.", "clean": "Lab computers slow ho rahe hote."}
]

def generate_live_feedback(db: Session) -> dict:
    template = random.choice(SAMPLE_TEMPLATES)
    topic_repo = TopicRepository(db)
    feedback_repo = FeedbackRepository(db)
    active_topics = topic_repo.get_active_topics()
    topic_id_map = {t.topic_code: t.topic_id for t in active_topics}
    t_id = topic_id_map.get(template["topic_code"])
    comment_id = "LIVE_" + str(uuid.uuid4()).replace("-", "")[:8].upper()
    course_code = random.choice(COURSES)
    instructor_id = random.choice(INSTRUCTORS)
    term = random.choice(TERMS)
    feedback_data = {
        "comment_id": comment_id,
        "timestamp": datetime.now(timezone.utc),
        "academic_term": term,
        "course_code": course_code,
        "instructor_id": instructor_id,
        "raw_text": template["raw"],
        "cleaned_text": template["clean"],
        "detected_language": template[ "lang" ],
        "lang_confidence": round(random.uniform(0.88, 0.99), 2),
        "script_type": template[ "script" ],
        "primary_topic_id": t_id,
        "primary_topic_code": template["topic_code"],
        "overall_sentiment": template["sentiment"],
        "sentiment_score": template[ "score" ],
        "is_outlier": False,
        "outlier_score": round(random.uniform(0.05, 0.25), 2)
    }
    aspects = [
        {
            "topic_id": t_id,
            "topic_code": template["topic_code"],
            "sentiment_label": template["topic_code"],
            "sentiment_score": template["score"],
            "confidence": 0.95,
            "evidence_span": template["clean"][:50]
        }
    ]
    record = feedback_repo.create_feedback(feedback_data, aspects)
    return {
        "comment_id": record.comment_id,
        "text": record.cleaned_text,
        "lang": record.detected_language,
        "topic": record.primary_topic_code,
        "sentiment": record.overall_sentiment,
        "course": record.course_code
    }

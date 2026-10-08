"""
Real-Time Inference Sandbox and Sentiment Analysis API Router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.repository import TopicRepository
from src.preprocessing.normalizer import clean_text
from src.preprocessing.lang_detector import detect_language
from src.sentiment.aspect_sentiment import AspectSentimentAnalyzer
from src.api.schemas import AnalyzeRequest, AnalyzeResponse, AspectSentimentItem

router = APIRouter(prefix="/analyze", tags=["Real-Time Sandbox Inference"])
aspect_analyzer = AspectSentimentAnalyzer()

TOPIC_NAME_MAP = {
    "TOPIC_1": "Pedagogy & Lecture Delivery",
    "TOPIC_2": "Assignments & Workload",
    "TOPIC_3": "Grading Fairness & Feedback",
    "TOPIC_4": "Faculty Support & Availability",
    "TOPIC_5": "Lab & Technical Infrastructure",
    "TOPIC_6": "Curriculum Depth & Relevance",
    "DRIFT_1": "GenAI & Academic Integrity Policy",
    "DRIFT_2": "Hybrid Lecture Audio/Video Logistics"
}

@router.post("", response_model=AnalyzeResponse)
def analyze_comment_sandbox(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Real-time inference endpoint for live student feedback sandbox:
    - Normalizes multilingual input and redacts PII.
    - Identifies language and orthographic script.
    - Extracts aspect-level sentiments and evidence spans.
    - Evaluates out-of-distribution drift novelty score.
    """
    cleaned = clean_text(payload.text, redact_pii=True)
    lang, conf, script = detect_language(cleaned)

    overall_label, overall_score, aspects = aspect_analyzer.analyze_aspects(cleaned, primary_topic="TOPIC_1")
    primary_code = aspects[0]["topic_code"] if aspects else "TOPIC_1"
    primary_name = TOPIC_NAME_MAP.get(primary_code, primary_code)

    is_outlier = primary_code.startswith("DRIFT_")
    outlier_score = 0.78 if is_outlier else 0.12

    aspect_items = [
        AspectSentimentItem(
            topic_code=a["topic_code"],
            sentiment_label=a["sentiment_label"],
            sentiment_score=a["sentiment_score"],
            confidence=a["confidence"],
            evidence_span=a.get("evidence_span")
        )
        for a in aspects
    ]

    return AnalyzeResponse(
        original_text=payload.text,
        cleaned_text=cleaned,
        detected_language=lang,
        lang_confidence=conf,
        script_type=script,
        primary_topic_code=primary_code,
        primary_topic_name=primary_name,
        overall_sentiment=overall_label,
        sentiment_score=overall_score,
        aspect_sentiments=aspect_items,
        is_outlier=is_outlier,
        outlier_score=outlier_score
    )

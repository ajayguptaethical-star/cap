"""
Feedback Ingestion and Query API Router.
"""

import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.repository import FeedbackRepository, TopicRepository
from src.preprocessing.normalizer import clean_text
from src.preprocessing.lang_detector import detect_language
from src.sentiment.aspect_sentiment import AspectSentimentAnalyzer
from src.api.schemas import (
    FeedbackCreateRequest,
    FeedbackBatchRequest,
    FeedbackResponse,
    FeedbackListResponse,
    AspectSentimentItem
)

router = APIRouter(prefix="/feedback", tags=["Feedback Ingestion & Queries"])
aspect_analyzer = AspectSentimentAnalyzer()

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_single_feedback(
    payload: FeedbackCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Ingests a single student feedback comment:
    1. Normalizes text and redacts PII.
    2. Identifies language and script.
    3. Analyzes aspect sentiments per topic facet.
    4. Evaluates outlier probability.
    5. Persists to SQLite database.
    """
    feedback_repo = FeedbackRepository(db)
    
    cleaned = clean_text(payload.raw_text, redact_pii=True)
    lang, conf, script = detect_language(cleaned)

    # Analyze aspect sentiments (defaulting primary to TOPIC_1 if unassigned)
    overall_label, overall_score, aspects = aspect_analyzer.analyze_aspects(cleaned, primary_topic="TOPIC_1")
    primary_topic = aspects[0]["topic_code"] if aspects else "TOPIC_1"

    # Evaluate novelty/outlier (drift check)
    is_outlier = primary_topic.startswith("DRIFT_")
    outlier_score = 0.75 if is_outlier else 0.15

    comment_id = str(uuid.uuid4())
    ts = payload.timestamp or datetime.now(timezone.utc)

    feedback_data = {
        "comment_id": comment_id,
        "timestamp": ts,
        "academic_term": payload.academic_term,
        "course_code": payload.course_code,
        "instructor_id": payload.instructor_id,
        "raw_text": payload.raw_text,
        "cleaned_text": cleaned,
        "detected_language": lang,
        "lang_confidence": conf,
        "script_type": script,
        "primary_topic_code": primary_topic,
        "overall_sentiment": overall_label,
        "sentiment_score": overall_score,
        "is_outlier": is_outlier,
        "outlier_score": outlier_score
    }

    record = feedback_repo.create_feedback(feedback_data, aspects)
    return record

@router.post("/batch", response_model=List[FeedbackResponse], status_code=status.HTTP_201_CREATED)
def create_batch_feedback(
    payload: FeedbackBatchRequest,
    db: Session = Depends(get_db)
):
    """Batch ingestion endpoint for bulk course evaluation uploads."""
    feedback_repo = FeedbackRepository(db)
    created_records = []

    for item in payload.comments:
        cleaned = clean_text(item.raw_text, redact_pii=True)
        lang, conf, script = detect_language(cleaned)
        overall_label, overall_score, aspects = aspect_analyzer.analyze_aspects(cleaned, primary_topic="TOPIC_1")
        primary_topic = aspects[0]["topic_code"] if aspects else "TOPIC_1"
        is_outlier = primary_topic.startswith("DRIFT_")
        outlier_score = 0.75 if is_outlier else 0.15

        data = {
            "comment_id": str(uuid.uuid4()),
            "timestamp": item.timestamp or datetime.now(timezone.utc),
            "academic_term": item.academic_term,
            "course_code": item.course_code,
            "instructor_id": item.instructor_id,
            "raw_text": item.raw_text,
            "cleaned_text": cleaned,
            "detected_language": lang,
            "lang_confidence": conf,
            "script_type": script,
            "primary_topic_code": primary_topic,
            "overall_sentiment": overall_label,
            "sentiment_score": overall_score,
            "is_outlier": is_outlier,
            "outlier_score": outlier_score
        }
        rec = feedback_repo.create_feedback(data, aspects)
        created_records.append(rec)

    return created_records

@router.get("", response_model=FeedbackListResponse)
def list_feedback(
    academic_term: Optional[str] = Query(None, description="Filter by semester"),
    course_code: Optional[str] = Query(None, description="Filter by course"),
    instructor_id: Optional[str] = Query(None, description="Filter by instructor"),
    primary_topic_code: Optional[str] = Query(None, description="Filter by topic code"),
    detected_language: Optional[str] = Query(None, description="Filter by language"),
    overall_sentiment: Optional[str] = Query(None, description="Filter by overall sentiment"),
    is_outlier: Optional[bool] = Query(None, description="Filter by outlier status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Queries feedback records with optional multi-attribute filters."""
    feedback_repo = FeedbackRepository(db)
    items = feedback_repo.query_feedback(
        academic_term=academic_term,
        course_code=course_code,
        instructor_id=instructor_id,
        primary_topic_code=primary_topic_code,
        detected_language=detected_language,
        overall_sentiment=overall_sentiment,
        is_outlier=is_outlier,
        limit=limit,
        offset=offset
    )
    total_count = feedback_repo.get_feedback_count()
    return FeedbackListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        items=items
    )

@router.get("/{comment_id}", response_model=FeedbackResponse)
def get_feedback_detail(comment_id: str, db: Session = Depends(get_db)):
    """Retrieves detailed feedback record and aspect sentiments by UUID."""
    feedback_repo = FeedbackRepository(db)
    record = feedback_repo.get_feedback_by_id(comment_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Feedback comment '{comment_id}' not found.")
    return record

"""
Topic Taxonomy and Versioning API Router.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.repository import TopicRepository, FeedbackRepository
from src.api.schemas import (
    TopicItemResponse,
    TopicVersionResponse,
    ExemplarItem
)

router = APIRouter(prefix="/topics", tags=["Topic Taxonomy & Versioning"])

@router.get("", response_model=List[TopicItemResponse])
def get_active_topics(db: Session = Depends(get_db)):
    """Returns the catalog of active institutional topics under the current model version."""
    topic_repo = TopicRepository(db)
    topics = topic_repo.get_active_topics()
    return topics

@router.get("/versions", response_model=List[TopicVersionResponse])
def get_all_topic_versions(db: Session = Depends(get_db)):
    """Returns all historical and active topic model version snapshots."""
    topic_repo = TopicRepository(db)
    versions = topic_repo.get_all_versions()
    return versions

@router.get("/{topic_code}/exemplars", response_model=List[ExemplarItem])
def get_topic_exemplars(
    topic_code: str,
    top_k: int = 3,
    db: Session = Depends(get_db)
):
    """
    Returns top representative student feedback quotes for a specific topic,
    ranked by semantic centrality to the topic cluster centroid.
    """
    feedback_repo = FeedbackRepository(db)
    records = feedback_repo.query_feedback(primary_topic_code=topic_code, limit=top_k)
    if not records:
        # Fallback to general comments if no exact match
        records = feedback_repo.query_feedback(limit=top_k)

    exemplars = []
    for r in records:
        exemplars.append(ExemplarItem(
            comment_id=r.comment_id,
            raw_text=r.raw_text,
            language=r.detected_language,
            similarity_score=round(float(1.0 - r.outlier_score), 3),
            sentiment=r.overall_sentiment
        ))
    return exemplars

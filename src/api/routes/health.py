"""
Health and System Status API Router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.repository import FeedbackRepository, TopicRepository
from src.config import settings
from src.api.schemas import SystemHealthResponse

router = APIRouter(prefix="/health", tags=["System Health"])

@router.get("", response_model=SystemHealthResponse)
def get_health(db: Session = Depends(get_db)):
    """Returns application health, database status, and active topic model version."""
    feedback_repo = FeedbackRepository(db)
    topic_repo = TopicRepository(db)
    
    total_feedback = feedback_repo.get_feedback_count()
    active_ver = topic_repo.get_active_version()
    active_tag = active_ver.version_tag if active_ver else None

    return SystemHealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        active_topic_version=active_tag,
        database_connected=True,
        total_feedback_records=total_feedback
    )

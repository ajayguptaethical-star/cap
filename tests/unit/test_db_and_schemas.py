"""
Unit tests for Deliverable 2: Database Models, Repositories, and Pydantic Schemas.
"""

import json
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import ValidationError

from src.database.models import Base
from src.database.repository import FeedbackRepository, TopicRepository, DriftRepository
from src.api.schemas import (
    FeedbackCreateRequest,
    AnalyzeRequest,
    GovernanceActionRequest,
    RollbackRequest,
    AspectSentimentItem
)

def utc_now():
    return datetime.now(timezone.utc)

@pytest.fixture
def test_db():
    """In-memory SQLite session for fast, isolated testing."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_feedback_repository_lifecycle(test_db):
    """Verify insertion and querying of feedback with aspect sentiments."""
    repo = FeedbackRepository(test_db)
    
    feedback_data = {
        "comment_id": "test-uuid-1",
        "timestamp": utc_now(),
        "academic_term": "Spring 2026",
        "course_code": "DS101",
        "instructor_id": "INST_01",
        "raw_text": "Teaching was great but lab was poor.",
        "cleaned_text": "Teaching was great but lab was poor.",
        "detected_language": "en",
        "lang_confidence": 0.99,
        "script_type": "Latin",
        "primary_topic_code": "TOPIC_1",
        "overall_sentiment": "neutral",
        "sentiment_score": 0.0,
        "is_outlier": False,
        "outlier_score": 0.12
    }
    aspects = [
        {"topic_code": "TOPIC_1", "sentiment_label": "positive", "sentiment_score": 0.85, "confidence": 0.95},
        {"topic_code": "TOPIC_5", "sentiment_label": "negative", "sentiment_score": -0.80, "confidence": 0.92}
    ]

    record = repo.create_feedback(feedback_data, aspects)
    assert record.comment_id == "test-uuid-1"
    assert len(record.aspect_sentiments) == 2

    # Query by term
    results = repo.query_feedback(academic_term="Spring 2026")
    assert len(results) == 1
    assert results[0].course_code == "DS101"

    # Verify counts
    assert repo.get_feedback_count() == 1
    assert repo.get_term_counts() == {"Spring 2026": 1}
    assert repo.get_language_distribution() == {"en": 1}

def test_topic_versioning_and_archival(test_db):
    """Verify topic versioning and state transitions (ACTIVE -> ARCHIVED)."""
    topic_repo = TopicRepository(test_db)

    # Create v1.0.0
    v1 = topic_repo.create_version("v1.0.0", json.dumps({"version": "1.0.0"}), "admin")
    assert v1.status == "ACTIVE"

    topics_data = [
        {"topic_code": "TOPIC_1", "topic_name": "Pedagogy", "top_keywords": "teach, lecture", "comment_count": 50},
        {"topic_code": "TOPIC_2", "topic_name": "Assignments", "top_keywords": "homework, load", "comment_count": 45}
    ]
    topic_repo.add_topics_to_version(v1.version_id, topics_data)
    active_topics = topic_repo.get_active_topics()
    assert len(active_topics) == 2

    # Create v1.1.0 and verify v1.0.0 is archived
    v2 = topic_repo.create_version("v1.1.0", json.dumps({"version": "1.1.0"}), "admin")
    assert v2.status == "ACTIVE"
    test_db.refresh(v1)
    assert v1.status == "ARCHIVED"

def test_drift_candidate_lifecycle(test_db):
    """Verify drift candidate staging and administrative status updates."""
    drift_repo = DriftRepository(test_db)

    candidate_data = {
        "cluster_hash": "hash123",
        "detected_at": utc_now(),
        "academic_term": "Summer 2026",
        "proposed_name": "genai_chatgpt_policy",
        "top_keywords": "chatgpt, ai tool, policy",
        "sample_size": 25,
        "coherence_score": 0.58,
        "status": "PENDING_REVIEW"
    }
    candidate = drift_repo.stage_candidate(candidate_data)
    assert candidate.candidate_id is not None
    assert candidate.status == "PENDING_REVIEW"

    # Fetch pending
    pending = drift_repo.get_pending_candidates()
    assert len(pending) == 1

    # Approve candidate
    updated = drift_repo.update_candidate_status(
        candidate.candidate_id,
        new_status="APPROVED",
        reviewed_by="dr_sharma",
        review_notes="Approved as new official topic"
    )
    assert updated.status == "APPROVED"
    assert updated.reviewed_by == "dr_sharma"
    assert len(drift_repo.get_pending_candidates()) == 0

def test_pydantic_schema_validation():
    """Verify input validation rules in Pydantic data contracts."""
    # Valid feedback create
    req = FeedbackCreateRequest(
        raw_text="Great course and well explained!",
        academic_term="Fall 2025",
        course_code="DS101",
        instructor_id="INST_01"
    )
    assert req.course_code == "DS101"

    # Invalid course code pattern
    with pytest.raises(ValidationError):
        FeedbackCreateRequest(
            raw_text="Too short",
            academic_term="Fall 2025",
            course_code="invalid-course-code",
            instructor_id="INST_01"
        )

    # Invalid sentiment range
    with pytest.raises(ValidationError):
        AspectSentimentItem(
            topic_code="TOPIC_1",
            sentiment_label="positive",
            sentiment_score=5.0,  # Must be between -1.0 and 1.0
            confidence=0.9
        )

    # Governance action validation
    gov_req = GovernanceActionRequest(
        candidate_id=1,
        action="APPROVE",
        approved_name="GenAI Policy",
        admin_notes="Approved for upcoming academic year",
        reviewed_by="dr_sharma"
    )
    assert gov_req.action == "APPROVE"

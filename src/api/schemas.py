"""
Pydantic v2 Data Contracts and Request/Response Schemas for FastAPI.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

def utc_now():
    return datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# Feedback Ingestion & Query Schemas
# ---------------------------------------------------------------------------
class FeedbackCreateRequest(BaseModel):
    raw_text: str = Field(..., min_length=5, max_length=1000, description="Raw student feedback comment")
    academic_term: str = Field(..., description="e.g. Fall 2025, Spring 2026, Summer 2026, Fall 2026")
    course_code: str = Field(..., pattern=r"^[A-Z]{2,4}[0-9]{3}$", description="Course code (e.g. DS101, ML202)")
    instructor_id: str = Field(..., description="Anonymized faculty identifier (e.g. INST_01)")
    timestamp: Optional[datetime] = Field(default_factory=utc_now, description="Submission timestamp")

class FeedbackBatchRequest(BaseModel):
    comments: List[FeedbackCreateRequest] = Field(..., min_length=1, max_length=5000, description="Batch list of feedback records")

class AspectSentimentItem(BaseModel):
    topic_code: str
    sentiment_label: Literal["positive", "negative", "neutral"]
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_span: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FeedbackResponse(BaseModel):
    comment_id: str
    timestamp: datetime
    academic_term: str
    course_code: str
    instructor_id: str
    raw_text: str
    cleaned_text: str
    detected_language: str
    lang_confidence: float
    script_type: str
    primary_topic_code: str
    overall_sentiment: str
    sentiment_score: float
    is_outlier: bool
    outlier_score: float
    aspect_sentiments: List[AspectSentimentItem] = []

    model_config = ConfigDict(from_attributes=True)

class FeedbackListResponse(BaseModel):
    total_count: int
    offset: int
    limit: int
    items: List[FeedbackResponse]

# ---------------------------------------------------------------------------
# Topic Taxonomy & Versioning Schemas
# ---------------------------------------------------------------------------
class TopicItemResponse(BaseModel):
    topic_id: int
    version_id: int
    topic_code: str
    topic_name: str
    description: Optional[str] = None
    top_keywords: str
    comment_count: int
    is_emergent: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TopicVersionResponse(BaseModel):
    version_id: int
    version_tag: str
    created_at: datetime
    status: str
    created_by: str
    topics: List[TopicItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ExemplarItem(BaseModel):
    comment_id: str
    raw_text: str
    language: str
    similarity_score: float
    sentiment: str

# ---------------------------------------------------------------------------
# Real-Time Sandbox Inference Schemas
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=1000, description="Student comment to analyze")

class AnalyzeResponse(BaseModel):
    original_text: str
    cleaned_text: str
    detected_language: str
    lang_confidence: float
    script_type: str
    primary_topic_code: str
    primary_topic_name: str
    overall_sentiment: str
    sentiment_score: float
    aspect_sentiments: List[AspectSentimentItem]
    is_outlier: bool
    outlier_score: float

# ---------------------------------------------------------------------------
# Innovation Layer & HITL Governance Schemas
# ---------------------------------------------------------------------------
class DriftCandidateResponse(BaseModel):
    candidate_id: int
    cluster_hash: str
    detected_at: datetime
    academic_term: str
    proposed_name: str
    top_keywords: str
    sample_size: int
    coherence_score: float
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class GovernanceActionRequest(BaseModel):
    candidate_id: int
    action: Literal["APPROVE", "MERGE", "DISCARD"]
    approved_name: Optional[str] = Field(None, description="Approved official title if action=APPROVE")
    merge_into_topic_code: Optional[str] = Field(None, description="Existing topic code if action=MERGE")
    admin_notes: str = Field(..., min_length=5, description="Auditable justification for committee records")
    reviewed_by: str = Field("dr_sharma", description="Admin username")

class RollbackRequest(BaseModel):
    target_version_tag: str = Field(..., description="Target version snapshot to restore, e.g. v1.0.0")
    admin_notes: str = Field(..., min_length=5, description="Auditable rationale for rolling back topic taxonomy")
    reviewed_by: str = Field("dr_sharma", description="Admin username")

class SystemHealthResponse(BaseModel):
    status: str = "healthy"
    app_name: str
    environment: str
    active_topic_version: Optional[str] = None
    database_connected: bool = True
    total_feedback_records: int

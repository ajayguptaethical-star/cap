"""
SQLAlchemy ORM models representing the feedback database schema.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

def utc_now():
    return datetime.now(timezone.utc)

Base = declarative_base()

class TopicVersionModel(Base):
    __tablename__ = "topic_versions"

    version_id = Column(Integer, primary_key=True, autoincrement=True)
    version_tag = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, ARCHIVED
    created_by = Column(String(50), default="system", nullable=False)
    snapshot_json = Column(Text, nullable=False)

    topics = relationship("TopicModel", back_populates="version", cascade="all, delete-orphan")


class TopicModel(Base):
    __tablename__ = "topics"

    topic_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("topic_versions.version_id"), nullable=False)
    topic_code = Column(String(30), nullable=False, index=True)
    topic_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    top_keywords = Column(Text, nullable=False)  # Comma-separated
    comment_count = Column(Integer, default=0, nullable=False)
    is_emergent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    version = relationship("TopicVersionModel", back_populates="topics")
    aspect_sentiments = relationship("AspectSentimentModel", back_populates="topic")


class FeedbackModel(Base):
    __tablename__ = "feedback"

    comment_id = Column(String(36), primary_key=True, index=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    academic_term = Column(String(20), nullable=False, index=True)
    course_code = Column(String(10), nullable=False, index=True)
    instructor_id = Column(String(15), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=False)
    detected_language = Column(String(10), nullable=False, index=True)
    lang_confidence = Column(Float, default=1.0, nullable=False)
    script_type = Column(String(15), nullable=False)  # Latin, Devanagari
    primary_topic_id = Column(Integer, ForeignKey("topics.topic_id"), nullable=True)
    primary_topic_code = Column(String(30), nullable=False, index=True)
    overall_sentiment = Column(String(10), nullable=False, index=True)  # positive, negative, neutral
    sentiment_score = Column(Float, default=0.0, nullable=False)
    is_outlier = Column(Boolean, default=False, nullable=False, index=True)
    outlier_score = Column(Float, default=0.0, nullable=False)

    aspect_sentiments = relationship("AspectSentimentModel", back_populates="feedback", cascade="all, delete-orphan")


class AspectSentimentModel(Base):
    __tablename__ = "aspect_sentiments"

    aspect_id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(36), ForeignKey("feedback.comment_id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.topic_id"), nullable=True)
    topic_code = Column(String(30), nullable=False, index=True)
    sentiment_label = Column(String(10), nullable=False)  # positive, negative, neutral
    sentiment_score = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    evidence_span = Column(Text, nullable=True)

    feedback = relationship("FeedbackModel", back_populates="aspect_sentiments")
    topic = relationship("TopicModel", back_populates="aspect_sentiments")


class DriftCandidateModel(Base):
    __tablename__ = "drift_candidates"

    candidate_id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_hash = Column(String(64), unique=True, nullable=False)
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    academic_term = Column(String(20), nullable=False)
    proposed_name = Column(String(100), nullable=False)
    top_keywords = Column(Text, nullable=False)
    sample_size = Column(Integer, nullable=False)
    coherence_score = Column(Float, default=0.0, nullable=False)
    status = Column(String(20), default="PENDING_REVIEW", nullable=False, index=True)  # PENDING_REVIEW, APPROVED, MERGED, DISCARDED
    reviewed_by = Column(String(50), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

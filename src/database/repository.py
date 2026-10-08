"""
CRUD Repository layer providing database access functions for feedback, topics, and drift candidates.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.database.models import (
    FeedbackModel,
    TopicModel,
    TopicVersionModel,
    AspectSentimentModel,
    DriftCandidateModel
)

class FeedbackRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_feedback(self, feedback_data: Dict[str, Any], aspects: Optional[List[Dict[str, Any]]] = None) -> FeedbackModel:
        """Inserts a single feedback record and its associated aspect sentiments."""
        record = FeedbackModel(**feedback_data)
        self.db.add(record)
        self.db.flush()

        if aspects:
            for asp in aspects:
                aspect_record = AspectSentimentModel(
                    comment_id=record.comment_id,
                    topic_id=asp.get("topic_id"),
                    topic_code=asp.get("topic_code", record.primary_topic_code),
                    sentiment_label=asp.get("sentiment_label", "neutral"),
                    sentiment_score=asp.get("sentiment_score", 0.0),
                    confidence=asp.get("confidence", 1.0),
                    evidence_span=asp.get("evidence_span")
                )
                self.db.add(aspect_record)

        self.db.commit()
        self.db.refresh(record)
        return record

    def get_feedback_by_id(self, comment_id: str) -> Optional[FeedbackModel]:
        return self.db.query(FeedbackModel).filter(FeedbackModel.comment_id == comment_id).first()

    def query_feedback(
        self,
        academic_term: Optional[str] = None,
        course_code: Optional[str] = None,
        instructor_id: Optional[str] = None,
        primary_topic_code: Optional[str] = None,
        detected_language: Optional[str] = None,
        overall_sentiment: Optional[str] = None,
        is_outlier: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FeedbackModel]:
        """Queries feedback records with optional multi-attribute filters."""
        query = self.db.query(FeedbackModel)
        if academic_term:
            query = query.filter(FeedbackModel.academic_term == academic_term)
        if course_code:
            query = query.filter(FeedbackModel.course_code == course_code)
        if instructor_id:
            query = query.filter(FeedbackModel.instructor_id == instructor_id)
        if primary_topic_code:
            query = query.filter(FeedbackModel.primary_topic_code == primary_topic_code)
        if detected_language:
            query = query.filter(FeedbackModel.detected_language == detected_language)
        if overall_sentiment:
            query = query.filter(FeedbackModel.overall_sentiment == overall_sentiment)
        if is_outlier is not None:
            query = query.filter(FeedbackModel.is_outlier == is_outlier)

        return query.order_by(desc(FeedbackModel.timestamp)).offset(offset).limit(limit).all()

    def get_feedback_count(self) -> int:
        return self.db.query(func.count(FeedbackModel.comment_id)).scalar() or 0

    def get_term_counts(self) -> Dict[str, int]:
        results = self.db.query(FeedbackModel.academic_term, func.count(FeedbackModel.comment_id))\
                         .group_by(FeedbackModel.academic_term).all()
        return {term: count for term, count in results}

    def get_language_distribution(self) -> Dict[str, int]:
        results = self.db.query(FeedbackModel.detected_language, func.count(FeedbackModel.comment_id))\
                         .group_by(FeedbackModel.detected_language).all()
        return {lang: count for lang, count in results}

    def get_sentiment_distribution(self) -> Dict[str, int]:
        results = self.db.query(FeedbackModel.overall_sentiment, func.count(FeedbackModel.comment_id))\
                         .group_by(FeedbackModel.overall_sentiment).all()
        return {sent: count for sent, count in results}

    def get_topic_distribution(self) -> Dict[str, int]:
        results = self.db.query(FeedbackModel.primary_topic_code, func.count(FeedbackModel.comment_id))\
                         .group_by(FeedbackModel.primary_topic_code).all()
        return {topic: count for topic, count in results if topic}

    def get_term_topic_distribution(self) -> List[Dict[str, Any]]:
        results = self.db.query(FeedbackModel.academic_term, FeedbackModel.primary_topic_code, func.count(FeedbackModel.comment_id))\
                         .group_by(FeedbackModel.academic_term, FeedbackModel.primary_topic_code).all()
        return [{"term": term, "topic_code": topic, "count": count} for term, topic, count in results if topic]

    def get_topic_aspect_sentiment_distribution(self) -> List[Dict[str, Any]]:
        results = self.db.query(AspectSentimentModel.topic_code, AspectSentimentModel.sentiment_label, func.count(AspectSentimentModel.aspect_id))\
                         .group_by(AspectSentimentModel.topic_code, AspectSentimentModel.sentiment_label).all()
        return [{"topic_code": topic, "sentiment_label": sent, "count": count} for topic, sent, count in results if topic]

    def get_exemplar_comments(self, topic_code: str, limit: int = 5) -> List[FeedbackModel]:
        return self.db.query(FeedbackModel)\
                      .filter(FeedbackModel.primary_topic_code == topic_code)\
                      .filter(FeedbackModel.is_outlier == False)\
                      .order_by(desc(FeedbackModel.timestamp))\
                      .limit(limit).all()


class TopicRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_version(self, version_tag: str, snapshot_json: str, created_by: str = "admin") -> TopicVersionModel:
        """Creates a new topic version snapshot, archiving previous active versions."""
        self.db.query(TopicVersionModel).filter(TopicVersionModel.status == "ACTIVE").update({"status": "ARCHIVED"})
        new_version = TopicVersionModel(
            version_tag=version_tag,
            snapshot_json=snapshot_json,
            created_by=created_by,
            status="ACTIVE"
        )
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        return new_version

    def get_active_version(self) -> Optional[TopicVersionModel]:
        return self.db.query(TopicVersionModel).filter(TopicVersionModel.status == "ACTIVE").first()

    def get_all_versions(self) -> List[TopicVersionModel]:
        return self.db.query(TopicVersionModel).order_by(desc(TopicVersionModel.created_at)).all()

    def add_topics_to_version(self, version_id: int, topics_data: List[Dict[str, Any]]) -> List[TopicModel]:
        topics = []
        for t in topics_data:
            topic = TopicModel(
                version_id=version_id,
                topic_code=t["topic_code"],
                topic_name=t["topic_name"],
                description=t.get("description"),
                top_keywords=t["top_keywords"],
                comment_count=t.get("comment_count", 0),
                is_emergent=t.get("is_emergent", False)
            )
            self.db.add(topic)
            topics.append(topic)
        self.db.commit()
        return topics

    def get_topics_for_version(self, version_id: int) -> List[TopicModel]:
        return self.db.query(TopicModel).filter(TopicModel.version_id == version_id).all()

    def get_active_topics(self) -> List[TopicModel]:
        active_ver = self.get_active_version()
        if not active_ver:
            return []
        return self.get_topics_for_version(active_ver.version_id)

    def seed_default_topics(self, version_tag: str = "v1.0.0") -> TopicVersionModel:
        """Seeds the canonical 6 institutional topics if not already present."""
        existing = self.db.query(TopicVersionModel).filter(TopicVersionModel.version_tag == version_tag).first()
        if existing:
            return existing

        default_topics = [
            {
                "topic_code": "TOPIC_1",
                "topic_name": "Pedagogy & Lecture Delivery",
                "description": "Pacing, slide clarity, and conceptual explanations",
                "top_keywords": "lecture, professor, clarify, slide, pacing",
                "comment_count": 0,
                "is_emergent": False
            },
            {
                "topic_code": "TOPIC_2",
                "topic_name": "Assignments & Workload",
                "description": "Homework load, deadlines, and problem difficulty",
                "top_keywords": "assignment, workload, problem set, deadline, submit",
                "comment_count": 0,
                "is_emergent": False
            },
            {
                "topic_code": "TOPIC_3",
                "topic_name": "Grading Fairness & Feedback",
                "description": "Marking transparency, rubric consistency, and TA feedback",
                "top_keywords": "rubric, transparent, grading, penalty, assessment",
                "comment_count": 0,
                "is_emergent": False
            },
            {
                "topic_code": "TOPIC_4",
                "topic_name": "Faculty Support & Availability",
                "description": "Office hours availability, responsiveness, and guidance",
                "top_keywords": "approachable, office hours, doubt, responsive, mentor",
                "comment_count": 0,
                "is_emergent": False
            },
            {
                "topic_code": "TOPIC_5",
                "topic_name": "Lab & Technical Infrastructure",
                "description": "Workstations, GPU servers, WiFi, and software environment",
                "top_keywords": "gpu, workstation, server crash, wifi, lab machine",
                "comment_count": 0,
                "is_emergent": False
            },
            {
                "topic_code": "TOPIC_6",
                "topic_name": "Curriculum Depth & Relevance",
                "description": "Syllabus modernness, theoretical vs applied balance",
                "top_keywords": "curriculum, prerequisite, practical, real-world, industry",
                "comment_count": 0,
                "is_emergent": False
            }
        ]
        import json
        snapshot = {
            "version": version_tag,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "n_topics": len(default_topics),
            "topics": {t["topic_code"]: t for t in default_topics}
        }
        ver = self.create_version(version_tag, json.dumps(snapshot, indent=2), "system_seed")
        self.add_topics_to_version(ver.version_id, default_topics)
        return ver


class DriftRepository:
    def __init__(self, db: Session):
        self.db = db

    def stage_candidate(self, candidate_data: Dict[str, Any]) -> DriftCandidateModel:
        candidate = DriftCandidateModel(**candidate_data)
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def get_pending_candidates(self) -> List[DriftCandidateModel]:
        return self.db.query(DriftCandidateModel)\
                      .filter(DriftCandidateModel.status == "PENDING_REVIEW")\
                      .order_by(desc(DriftCandidateModel.detected_at)).all()

    def get_candidate_by_id(self, candidate_id: int) -> Optional[DriftCandidateModel]:
        return self.db.query(DriftCandidateModel).filter(DriftCandidateModel.candidate_id == candidate_id).first()

    def update_candidate_status(
        self,
        candidate_id: int,
        new_status: str,
        reviewed_by: str,
        review_notes: str
    ) -> Optional[DriftCandidateModel]:
        candidate = self.get_candidate_by_id(candidate_id)
        if candidate:
            candidate.status = new_status
            candidate.reviewed_by = reviewed_by
            candidate.review_notes = review_notes
            candidate.reviewed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(candidate)
        return candidate

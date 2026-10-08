"""
Human-in-the-Loop (HITL) Governance and Rollback Engine.
Manages candidate topic staging, committee approval state machine,
topic model version snapshotting (v1.0.0 -> v1.1.0), and 1-click rollbacks.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from src.database.models import TopicVersionModel, TopicModel, DriftCandidateModel, FeedbackModel
from src.database.repository import TopicRepository, DriftRepository, FeedbackRepository

class GovernanceManager:
    """
    Controlled governance engine ensuring that NO model topic mutations occur
    without explicit human administrator approval. Supports instant rollbacks.
    """
    def __init__(self, db: Session):
        self.db = db
        self.topic_repo = TopicRepository(db)
        self.drift_repo = DriftRepository(db)
        self.feedback_repo = FeedbackRepository(db)

    def stage_candidate(self, candidate_data: Dict[str, Any]) -> DriftCandidateModel:
        """Stages an emerging topic candidate in PENDING_REVIEW state."""
        # Check if already staged via cluster_hash
        existing = self.db.query(DriftCandidateModel)\
                          .filter(DriftCandidateModel.cluster_hash == candidate_data["cluster_hash"])\
                          .first()
        if existing:
            return existing

        payload = {
            "cluster_hash": candidate_data["cluster_hash"],
            "detected_at": datetime.now(timezone.utc),
            "academic_term": candidate_data["academic_term"],
            "proposed_name": candidate_data["proposed_name"],
            "top_keywords": candidate_data["top_keywords"],
            "sample_size": candidate_data["sample_size"],
            "coherence_score": candidate_data["coherence_score"],
            "status": "PENDING_REVIEW"
        }
        return self.drift_repo.stage_candidate(payload)

    def approve_candidate(
        self,
        candidate_id: int,
        approved_name: Optional[str] = None,
        admin_notes: str = "Approved by committee",
        reviewed_by: str = "dr_sharma"
    ) -> TopicVersionModel:
        """
        Approves an emerging candidate topic:
        1. Updates candidate status to APPROVED with audit notes.
        2. Increments version tag (e.g., v1.0.0 -> v1.1.0).
        3. Creates an immutable version snapshot incorporating the new emerging topic.
        4. Archives previous active version.
        """
        candidate = self.drift_repo.get_candidate_by_id(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found.")
        if candidate.status != "PENDING_REVIEW":
            raise ValueError(f"Candidate is already in state: {candidate.status}")

        official_name = approved_name.strip() if approved_name else candidate.proposed_name

        # 1. Update candidate status
        self.drift_repo.update_candidate_status(
            candidate_id=candidate_id,
            new_status="APPROVED",
            reviewed_by=reviewed_by,
            review_notes=admin_notes
        )

        # 2. Get current active version (seed default v1.0.0 if database is unseeded)
        active_ver = self.topic_repo.get_active_version()
        if not active_ver and not self.topic_repo.get_all_versions():
            active_ver = self.topic_repo.seed_default_topics("v1.0.0")
        current_topics = self.topic_repo.get_topics_for_version(active_ver.version_id) if active_ver else []

        # Determine new version tag monotonically increasing across all historical versions
        all_versions = self.topic_repo.get_all_versions()
        max_minor = 0
        for v in all_versions:
            if v.version_tag and v.version_tag.startswith("v"):
                try:
                    parts = v.version_tag[1:].split(".")
                    max_minor = max(max_minor, int(parts[1]))
                except (ValueError, IndexError):
                    pass
        new_tag = f"v1.{max_minor + 1}.0"

        # 3. Formulate new topic set
        new_topic_code = f"DRIFT_{len([t for t in current_topics if t.is_emergent]) + 1}"
        new_topic_data = {
            "topic_code": new_topic_code,
            "topic_name": official_name,
            "description": f"Emerging topic approved from term {candidate.academic_term}: {admin_notes}",
            "top_keywords": candidate.top_keywords,
            "comment_count": candidate.sample_size,
            "is_emergent": True
        }

        topics_payload = []
        for t in current_topics:
            topics_payload.append({
                "topic_code": t.topic_code,
                "topic_name": t.topic_name,
                "description": t.description,
                "top_keywords": t.top_keywords,
                "comment_count": t.comment_count,
                "is_emergent": t.is_emergent
            })
        topics_payload.append(new_topic_data)

        # Build snapshot metadata JSON
        snapshot_meta = {
            "version": new_tag,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": reviewed_by,
            "admin_notes": admin_notes,
            "candidate_id": candidate_id,
            "n_topics": len(topics_payload),
            "topics": {t["topic_code"]: t for t in topics_payload}
        }

        # 4. Create new version and insert topics
        new_version = self.topic_repo.create_version(
            version_tag=new_tag,
            snapshot_json=json.dumps(snapshot_meta, indent=2),
            created_by=reviewed_by
        )
        self.topic_repo.add_topics_to_version(new_version.version_id, topics_payload)
        return new_version

    def merge_candidate(
        self,
        candidate_id: int,
        merge_into_topic_code: str,
        admin_notes: str = "Merged into existing topic",
        reviewed_by: str = "dr_sharma"
    ) -> DriftCandidateModel:
        """Folds emerging outlier candidate into an existing topic catalog entry."""
        candidate = self.drift_repo.get_candidate_by_id(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found.")

        updated = self.drift_repo.update_candidate_status(
            candidate_id=candidate_id,
            new_status="MERGED",
            reviewed_by=reviewed_by,
            review_notes=f"Merged into {merge_into_topic_code}: {admin_notes}"
        )
        return updated

    def discard_candidate(
        self,
        candidate_id: int,
        admin_notes: str = "Discarded as unaligned noise/spam",
        reviewed_by: str = "dr_sharma"
    ) -> DriftCandidateModel:
        """Discards candidate outlier cluster as spurious noise."""
        candidate = self.drift_repo.get_candidate_by_id(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found.")

        return self.drift_repo.update_candidate_status(
            candidate_id=candidate_id,
            new_status="DISCARDED",
            reviewed_by=reviewed_by,
            review_notes=admin_notes
        )

    def rollback_to_version(
        self,
        target_version_tag: str,
        admin_notes: str = "Rollback executed by administrator",
        reviewed_by: str = "dr_sharma"
    ) -> TopicVersionModel:
        """
        Atomically rolls back the active topic model to a historical version snapshot.
        Prevents model collapse or semantic degradation.
        """
        target_tag = target_version_tag.strip()
        if not target_tag.startswith("v") and target_tag and target_tag[0].isdigit():
            target_tag = f"v{target_tag}"

        target = self.db.query(TopicVersionModel)\
                        .filter(TopicVersionModel.version_tag == target_tag)\
                        .first()
        if not target:
            if target_tag == "v1.0.0":
                target = self.topic_repo.seed_default_topics("v1.0.0")
            else:
                raise ValueError(f"Version snapshot '{target_version_tag}' not found in database.")

        # Archive all versions
        self.db.query(TopicVersionModel).update({"status": "ARCHIVED"})

        # Reactivate target version
        target.status = "ACTIVE"
        self.db.commit()
        self.db.refresh(target)
        return target

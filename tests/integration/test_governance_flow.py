"""
Integration test for the complete Human-in-the-Loop (HITL) Governance and 1-Click Rollback Flow.
Tests candidate staging -> committee approval -> version increment (v1.0.0 -> v1.1.0) -> instant rollback (v1.1.0 -> v1.0.0).
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from src.api.app import app
import src.database.connection as conn
from src.database.repository import DriftRepository, TopicRepository
from src.innovation.governance import GovernanceManager

def test_full_governance_lifecycle_and_rollback(api_client):
    """
    Simulates real-world academic committee review:
    1. Innovation engine stages an emergent outlier topic candidate.
    2. Committee inspects pending review queue.
    3. Committee approves candidate -> version increments to v1.1.0.
    4. Active topic catalog updates.
    5. Committee tests emergency 1-click rollback -> version restores to v1.0.0.
    """
    db = conn.SessionLocal()
    try:
        gov = GovernanceManager(db)
        drift_repo = DriftRepository(db)
        topic_repo = TopicRepository(db)

        import uuid
        unique_hash = f"test_cluster_{uuid.uuid4().hex[:8]}"
        candidate_data = {
            "cluster_hash": unique_hash,
            "academic_term": "Spring 2026",
            "proposed_name": "ai_tool_guidelines",
            "top_keywords": "chatgpt, ai tool, copilot, prompt, homework",
            "sample_size": 28,
            "coherence_score": 0.6125
        }
        cand = gov.stage_candidate(candidate_data)
        assert cand.candidate_id is not None
        assert cand.status == "PENDING_REVIEW"
        cand_id = cand.candidate_id

        # 2. Check pending candidates endpoint
        res_pending = api_client.get("/api/v1/drift/pending")
        assert res_pending.status_code == 200
        pending_list = res_pending.json()
        assert any(p["candidate_id"] == cand_id for p in pending_list)

        # 3. Approve candidate via Governance API
        approval_payload = {
            "candidate_id": cand_id,
            "action": "APPROVE",
            "approved_name": "Generative AI Policy & Integrity",
            "admin_notes": "Approved by Academic Senate for 2026-2027 curriculum",
            "reviewed_by": "dr_sharma"
        }
        res_approve = api_client.post("/api/v1/governance/approve", json=approval_payload)
        assert res_approve.status_code == 200
        new_version_data = res_approve.json()
        assert new_version_data["version_tag"].startswith("v1.")
        assert new_version_data["status"] == "ACTIVE"

        # 4. Verify active catalog now includes the approved emergent topic
        res_topics = api_client.get("/api/v1/topics")
        assert res_topics.status_code == 200
        active_topics = res_topics.json()
        emergent_topics = [t for t in active_topics if t.get("is_emergent")]
        assert len(emergent_topics) >= 1
        assert any(t["topic_name"] == "Generative AI Policy & Integrity" for t in emergent_topics)

        # 5. Execute 1-Click Rollback back to v1.0.0
        rollback_payload = {
            "target_version_tag": "v1.0.0",
            "admin_notes": "Emergency test rollback executed during integration validation",
            "reviewed_by": "dr_sharma"
        }
        res_rollback = api_client.post("/api/v1/governance/rollback", json=rollback_payload)
        assert res_rollback.status_code == 200
        restored_ver = res_rollback.json()
        assert restored_ver["version_tag"] == "v1.0.0"
        assert restored_ver["status"] == "ACTIVE"

        # 6. Verify restored catalog only has the original baseline topics
        res_restored_topics = api_client.get("/api/v1/topics")
        assert res_restored_topics.status_code == 200
        restored_topics = res_restored_topics.json()
        assert all(t["is_emergent"] is False for t in restored_topics)

    finally:
        db.close()

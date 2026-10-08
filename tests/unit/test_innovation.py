"""
Unit tests for Milestone 4: Graded Innovation Layer (Topic Drift, Emerging Clusterer, and HITL Governance).
"""

import json
import pytest
import numpy as np
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, TopicVersionModel, DriftCandidateModel
from src.database.repository import TopicRepository, DriftRepository, FeedbackRepository
from src.innovation.drift_detector import AdvancedDriftDetector, BaselineVocabularyDivergence
from src.innovation.emerging_clusterer import EmergingTopicClusterer
from src.innovation.governance import GovernanceManager

def utc_now():
    return datetime.now(timezone.utc)

@pytest.fixture
def memory_db():
    """Isolated in-memory SQLite session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

# ---------------------------------------------------------------------------
# Outlier & Drift Detection Tests
# ---------------------------------------------------------------------------
def test_pointwise_outlier_scoring():
    """Verify that embeddings distant from cluster centroids are flagged as outliers."""
    detector = AdvancedDriftDetector()
    
    # 2 centroids in 4D space
    centroids = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0]
    ])

    # Sample 1: Close to Centroid 0
    # Sample 2: Orthogonal / far from both centroids (novel signal)
    test_embeddings = np.array([
        [0.98, 0.05, 0.0, 0.0],
        [0.0, 0.0, 0.85, 0.52]
    ])

    scores, is_outlier = detector.score_outliers(test_embeddings, centroids)
    assert len(scores) == 2
    assert scores[0] < 0.20
    assert is_outlier[0] == False

    assert scores[1] > 0.80
    assert is_outlier[1] == True

def test_population_stability_index_shift():
    """Verify PSI identifies stable distributions vs significant structural drift."""
    detector = AdvancedDriftDetector(psi_threshold=0.25)

    ref_proportions = {"TOPIC_1": 0.20, "TOPIC_2": 0.20, "TOPIC_3": 0.20, "TOPIC_4": 0.20, "TOPIC_5": 0.20}
    
    # Case A: Minor shift (Stable)
    stable_proportions = {"TOPIC_1": 0.21, "TOPIC_2": 0.19, "TOPIC_3": 0.20, "TOPIC_4": 0.21, "TOPIC_5": 0.19}
    res_stable = detector.compute_psi(ref_proportions, stable_proportions)
    assert res_stable["status"] == "STABLE"
    assert res_stable["psi"] < 0.10
    assert res_stable["is_alert"] == False

    # Case B: Significant shift (new emerging topic taking 35% of volume)
    drifted_proportions = {"TOPIC_1": 0.10, "TOPIC_2": 0.10, "TOPIC_3": 0.15, "TOPIC_4": 0.10, "TOPIC_5": 0.20, "DRIFT_1": 0.35}
    res_drift = detector.compute_psi(ref_proportions, drifted_proportions)
    assert res_drift["status"] == "SIGNIFICANT_DRIFT"
    assert res_drift["psi"] >= 0.25
    assert res_drift["is_alert"] == True

def test_baseline_vocabulary_divergence():
    """Verify baseline rolling-window vocabulary divergence computes Jaccard and Cosine divergence."""
    baseline = BaselineVocabularyDivergence(top_k=50)
    ref_texts = [
        "The professor explains derivations clearly.",
        "Lectures are well structured and interactive.",
        "Homework assignments are clear and helpful."
    ] * 5

    # Case A: Similar vocabulary
    curr_texts_similar = [
        "The professor gives clear explanations in lectures.",
        "Interactive lectures and helpful homework assignments."
    ] * 5
    res_sim = baseline.compute_divergence(ref_texts, curr_texts_similar)
    assert 0.0 <= res_sim["jaccard_distance"] <= 1.0
    assert 0.0 <= res_sim["cosine_divergence"] <= 1.0

    # Case B: Completely disparate vocabulary
    curr_texts_novel = [
        "ChatGPT AI plagiarism detector flags student python code erroneously.",
        "Copyleaks false positives on computer programming homework submissions."
    ] * 5
    res_novel = baseline.compute_divergence(ref_texts, curr_texts_novel)
    assert res_novel["cosine_divergence"] > res_sim["cosine_divergence"]

def test_wasserstein_drift_distance():
    """Verify Earth Mover's Distance between topic histograms."""
    detector = AdvancedDriftDetector()
    hist_a = [100, 100, 100, 100]
    hist_b = [100, 100, 100, 100]
    hist_c = [0, 0, 200, 200]

    dist_identical = detector.compute_wasserstein_drift(hist_a, hist_b)
    dist_shifted = detector.compute_wasserstein_drift(hist_a, hist_c)

    assert dist_identical == 0.0
    assert dist_shifted > 0.0

# ---------------------------------------------------------------------------
# Emerging Clusterer Tests
# ---------------------------------------------------------------------------
def test_emerging_topic_clusterer():
    """Verify that outlier comments are aggregated and surfaced as candidate topics."""
    clusterer = EmergingTopicClusterer(min_cluster_size=6, min_coherence=-0.50)

    # 12 outlier texts about GenAI
    outlier_texts = [
        "ChatGPT gave false positive plagiarism flags on my python code.",
        "AI detector tool wrongly flagged my original programming assignment.",
        "Unfair penalties because automated AI copy checker reported cheating.",
        "Is using ChatGPT allowed for assignment debugging or not?",
        "Clear guidelines needed for Generative AI tools in coding homework.",
        "AI copy checker tool is broken and accuses students of plagiarism."
    ] * 2

    # Fake dense embeddings
    rng = np.random.RandomState(42)
    embeddings = rng.randn(len(outlier_texts), 16)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    candidates = clusterer.discover_candidates(outlier_texts, embeddings, academic_term="Summer 2026")
    assert len(candidates) >= 1
    c = candidates[0]
    assert c["sample_size"] >= 6
    assert "chatgpt" in c["top_keywords"].lower() or "ai" in c["top_keywords"].lower() or "plagiarism" in c["top_keywords"].lower()
    assert len(c["cluster_hash"]) == 64

# ---------------------------------------------------------------------------
# HITL Governance State Machine & Rollback Tests
# ---------------------------------------------------------------------------
def test_governance_staging_and_approval_lifecycle(memory_db):
    """Verify candidate staging, approval, version increment (v1.0.0 -> v1.1.0), and rollback."""
    gov = GovernanceManager(memory_db)
    topic_repo = TopicRepository(memory_db)

    # Initialize v1.0.0
    v1 = topic_repo.create_version("v1.0.0", json.dumps({"version": "v1.0.0"}), "system")
    initial_topics = [
        {"topic_code": "TOPIC_1", "topic_name": "Pedagogy", "top_keywords": "teach, lecture", "comment_count": 50},
        {"topic_code": "TOPIC_2", "topic_name": "Assignments", "top_keywords": "homework, load", "comment_count": 45}
    ]
    topic_repo.add_topics_to_version(v1.version_id, initial_topics)

    # 1. Stage Candidate
    candidate_data = {
        "cluster_hash": "testhash1234567890",
        "academic_term": "Summer 2026",
        "proposed_name": "genai_chatgpt_policy",
        "top_keywords": "chatgpt, ai tool, plagiarism, detector",
        "sample_size": 28,
        "coherence_score": 0.584
    }
    staged = gov.stage_candidate(candidate_data)
    assert staged.status == "PENDING_REVIEW"

    # 2. Approve Candidate -> should create v1.1.0
    new_version = gov.approve_candidate(
        candidate_id=staged.candidate_id,
        approved_name="GenAI & Academic Integrity Policy",
        admin_notes="Approved for Fall 2026 onboarding",
        reviewed_by="dr_sharma"
    )
    assert new_version.version_tag == "v1.1.0"
    assert new_version.status == "ACTIVE"

    # Check that previous version v1.0.0 is archived
    memory_db.refresh(v1)
    assert v1.status == "ARCHIVED"

    # Verify that v1.1.0 contains 3 topics (2 original + 1 emergent)
    active_topics = topic_repo.get_active_topics()
    assert len(active_topics) == 3
    emergent_topic = next(t for t in active_topics if t.is_emergent)
    assert emergent_topic.topic_name == "GenAI & Academic Integrity Policy"
    assert emergent_topic.topic_code == "DRIFT_1"

    # 3. 1-Click Rollback -> revert to v1.0.0
    restored = gov.rollback_to_version(
        target_version_tag="v1.0.0",
        admin_notes="Rollback requested due to curriculum committee review",
        reviewed_by="dr_sharma"
    )
    assert restored.version_tag == "v1.0.0"
    assert restored.status == "ACTIVE"

    memory_db.refresh(new_version)
    assert new_version.status == "ARCHIVED"

    # Verify active topics restored to original 2 topics
    restored_topics = topic_repo.get_active_topics()
    assert len(restored_topics) == 2
    assert all(not t.is_emergent for t in restored_topics)

def test_governance_merge_and_discard(memory_db):
    """Verify merge and discard actions on candidates."""
    gov = GovernanceManager(memory_db)
    candidate_data = {
        "cluster_hash": "mergehash123",
        "academic_term": "Fall 2026",
        "proposed_name": "assignment_late_submissions",
        "top_keywords": "late, deadline, grace, submission",
        "sample_size": 15,
        "coherence_score": 0.45
    }
    staged = gov.stage_candidate(candidate_data)
    
    # Merge into TOPIC_2
    merged = gov.merge_candidate(
        candidate_id=staged.candidate_id,
        merge_into_topic_code="TOPIC_2",
        admin_notes="Fold into assignments topic",
        reviewed_by="dr_sharma"
    )
    assert merged.status == "MERGED"

    # Discard candidate
    candidate_data2 = {
        "cluster_hash": "discardhash456",
        "academic_term": "Fall 2026",
        "proposed_name": "cafeteria_coffee_machine",
        "top_keywords": "coffee, canteen, machine, tea",
        "sample_size": 8,
        "coherence_score": 0.15
    }
    staged2 = gov.stage_candidate(candidate_data2)
    discarded = gov.discard_candidate(
        candidate_id=staged2.candidate_id,
        admin_notes="Irrelevant non-course grievance",
        reviewed_by="dr_sharma"
    )
    assert discarded.status == "DISCARDED"

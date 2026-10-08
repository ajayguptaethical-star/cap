"""
Integration tests for FastAPI REST endpoints (Milestone 5).
Validates health, topics, feedback ingestion/query, live sentiment analysis, and drift metrics.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app


def test_api_root_and_health(api_client):
    """Verify root and health endpoints return 200 OK and expected structure."""
    # Root
    res_root = api_client.get("/")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root["status"] == "operational"
    assert "/docs" in data_root["docs"]

    # Health
    res_health = api_client.get("/api/v1/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "healthy"
    assert data_health["database_connected"] is True
    assert data_health["total_feedback_records"] >= 0

def test_topics_endpoints(api_client):
    """Verify active topic retrieval and topic version history."""
    # Active topics
    res_topics = api_client.get("/api/v1/topics")
    assert res_topics.status_code == 200
    topics = res_topics.json()
    assert isinstance(topics, list)
    assert len(topics) >= 1
    assert any(t["topic_code"] == "TOPIC_1" for t in topics)

    # Topic versions
    res_ver = api_client.get("/api/v1/topics/versions")
    assert res_ver.status_code == 200
    versions = res_ver.json()
    assert isinstance(versions, list)
    assert any(v["version_tag"] == "v1.0.0" for v in versions)

def test_feedback_query_and_single_ingest(api_client):
    """Verify querying existing feedback and ingesting a new multilingual comment."""
    # Query list
    res_list = api_client.get("/api/v1/feedback?limit=10")
    assert res_list.status_code == 200
    feedback_data = res_list.json()
    assert "items" in feedback_data
    assert "total_count" in feedback_data
    assert len(feedback_data["items"]) <= 10

    # Ingest single comment (Hinglish)
    payload = {
        "raw_text": "Sir bohot acche se explain karte hain par assignments ka workload bohot zyada hai!",
        "academic_term": "Spring 2026",
        "course_code": "CS201",
        "instructor_id": "INST_04"
    }
    res_create = api_client.post("/api/v1/feedback", json=payload)
    assert res_create.status_code == 201
    created = res_create.json()
    assert created["course_code"] == "CS201"
    assert created["detected_language"] in ["hi-en", "hinglish", "hi", "en"]
    assert "aspect_sentiments" in created
    assert len(created["aspect_sentiments"]) >= 1

def test_live_analyze_endpoint(api_client):
    """Verify live sandbox inference endpoint across multilingual text with aspect evidence spans."""
    payload = {
        "text": "The lectures were engaging and clear, but practical lab wifi was terrible and servers crashed constantly.",
        "primary_topic": "TOPIC_1"
    }
    res_analyze = api_client.post("/api/v1/analyze", json=payload)
    assert res_analyze.status_code == 200
    data = res_analyze.json()
    assert data["detected_language"] == "en"
    assert data["script_type"] == "Latin"
    assert "aspect_sentiments" in data
    assert len(data["aspect_sentiments"]) >= 1
    
    # Evidence spans must be present
    has_spans = any(a.get("evidence_span") is not None for a in data["aspect_sentiments"])
    assert has_spans

def test_drift_metrics_endpoint(api_client):
    """Verify cross-semester Population Stability Index (PSI) computation."""
    res_drift = api_client.get("/api/v1/drift/metrics?ref_term=Fall 2024&curr_term=Spring 2026")
    assert res_drift.status_code == 200
    drift_data = res_drift.json()
    assert "psi" in drift_data
    assert "status" in drift_data
    assert drift_data["status"] in ["STABLE", "MODERATE_SHIFT", "SIGNIFICANT_DRIFT"]
    assert isinstance(drift_data["topic_contributions"], dict)

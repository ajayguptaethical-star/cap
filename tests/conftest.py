"""
Pytest configuration and shared fixtures for unit and integration testing.
Provides guaranteed test database isolation and baseline state seeding.
"""

import os
import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database.models import Base
from src.database.connection import get_db
from src.database.repository import TopicRepository
from src.api.app import app


@pytest.fixture(scope="session")
def raw_dataset_path():
    path = os.path.join("data", "raw", "synthetic_feedback_1000.csv")
    assert os.path.exists(path), f"Raw dataset not found at {path}"
    return path


@pytest.fixture(scope="session")
def raw_dataset(raw_dataset_path):
    return pd.read_csv(raw_dataset_path)


@pytest.fixture(scope="session")
def train_dataset():
    path = os.path.join("data", "processed", "train.csv")
    assert os.path.exists(path), f"Train dataset not found at {path}"
    return pd.read_csv(path)


@pytest.fixture(scope="session")
def val_dataset():
    path = os.path.join("data", "processed", "val.csv")
    assert os.path.exists(path), f"Val dataset not found at {path}"
    return pd.read_csv(path)


@pytest.fixture(scope="session")
def test_dataset():
    path = os.path.join("data", "processed", "test.csv")
    assert os.path.exists(path), f"Test dataset not found at {path}"
    return pd.read_csv(path)


@pytest.fixture(autouse=True)
def isolated_test_database(tmp_path, monkeypatch):
    """
    Quality Bar / Test Isolation Fix (Finding #2):
    Creates an isolated temporary SQLite database for each test, initializes schemas,
    and seeds baseline institutional topics (v1.0.0). Overrides FastAPI get_db dependency
    and patches SessionLocal to prevent cross-test database mutation bleeding.
    """
    db_file = tmp_path / "test_course_feedback.db"
    db_url = f"sqlite:///{db_file}"
    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Seed baseline topics into isolated database
    seed_session = TestingSession()
    try:
        topic_repo = TopicRepository(seed_session)
        topic_repo.seed_default_topics("v1.0.0")
    finally:
        seed_session.close()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    # Apply FastAPI dependency override
    app.dependency_overrides[get_db] = override_get_db

    # Monkeypatch global database connections
    monkeypatch.setattr("src.database.connection.SessionLocal", TestingSession)
    monkeypatch.setattr("src.database.connection.engine", test_engine)
    monkeypatch.setattr("src.database.connection.init_db", lambda target_engine=None: None)

    yield TestingSession

    app.dependency_overrides.clear()


@pytest.fixture
def api_client():
    """Provides a TestClient bound to the isolated test database."""
    with TestClient(app) as client:
        yield client

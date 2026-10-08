"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables or .env file.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "Multilingual Course Feedback Intelligence"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PORT: int = 8000
    DASHBOARD_PORT: int = 8501

    # Database & Storage
    DATABASE_URL: str = "sqlite:///./course_feedback.db"
    MLFLOW_TRACKING_URI: str = "sqlite:///./mlflow.db"

    # NLP & Model Hyperparameters
    EMBEDDING_MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"
    MIN_TOPIC_SIZE: int = 10
    OUTLIER_THRESHOLD: float = 0.40  # Empirically calibrated optimal operating point from scripts/evaluate.py
    CENTROID_COSINE_SIM_THRESHOLD: float = 0.60  # 1.0 - OUTLIER_THRESHOLD
    POPULATION_STABILITY_INDEX_THRESHOLD: float = 0.25

    # Governance & Safety
    AUTO_APPROVAL_ENABLED: bool = False
    MAX_CANDIDATE_TOPICS_PER_BATCH: int = 5
    PII_ANONYMIZATION_ENABLED: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

# Global singleton instance
settings = Settings()

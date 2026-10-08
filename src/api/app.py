"""
FastAPI Application Entrypoint and Router Orchestration.
Exposes interactive OpenAPI / Swagger documentation at /docs.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config import settings
from src.database.connection import init_db
from src.api.routes import health, feedback, topics, sentiment, drift, governance

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema on application startup."""
    init_db()
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title="Multilingual Course Feedback Intelligence API",
        description=(
            "Enterprise-grade NLP API for higher-education course evaluations. "
            "Features script-aware multilingual processing (EN, HI, MR, Hinglish, Marathlish), "
            "topic modeling, Aspect-Based Sentiment Analysis (ABSA), "
            "and an Innovation Layer for Outlier Topic Drift and Human-in-the-Loop Governance."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Enable CORS for Streamlit dashboard and external integrations
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers under /api/v1 prefix
    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(feedback.router, prefix=api_prefix)
    app.include_router(topics.router, prefix=api_prefix)
    app.include_router(sentiment.router, prefix=api_prefix)
    app.include_router(drift.router, prefix=api_prefix)
    app.include_router(governance.router, prefix=api_prefix)

    @app.get("/", tags=["Root"])
    def root():
        return {
            "message": "Multilingual Course Feedback Intelligence API is running.",
            "docs": "/docs",
            "version": "1.0.0",
            "status": "operational"
        }

    return app

app = create_app()

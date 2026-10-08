"""
Dashboard utilities: DB access, Plotly figure styling, and UI badge helpers.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session

from src.database.connection import SessionLocal
from src.database.repository import FeedbackRepository, TopicRepository, DriftRepository
from src.database.models import FeedbackModel, TopicModel, TopicVersionModel, DriftCandidateModel

# Curated palette for consistent multilingual feedback visual design
COLOR_PALETTE = {
    "positive": "#10B981",    # Emerald
    "neutral": "#94A3B8",     # Slate
    "negative": "#EF4444",    # Crimson
    "primary": "#6366F1",     # Indigo
    "secondary": "#06B6D4",   # Cyan
    "accent": "#F59E0B",      # Amber
    "card_bg": "#1E293B",     # Dark Slate
    "languages": {
        "en": "#3B82F6",
        "hi": "#F59E0B",
        "mr": "#EC4899",
        "hinglish": "#8B5CF6",
        "marathlish": "#06B6D4"
    }
}

def get_db_session() -> Session:
    """Yields a database session."""
    return SessionLocal()

def apply_chart_theme(fig: go.Figure, title: Optional[str] = None) -> go.Figure:
    """Applies a clean, modern dark card aesthetic to Plotly figures."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, family="Inter, system-ui, sans-serif", color="#F8FAFC")) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color="#CBD5E1"),
        margin=dict(l=20, r=20, t=40 if title else 20, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color="#E2E8F0")
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="#334155", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#334155", zeroline=False)
    return fig

def render_badge(text: str, badge_type: str = "primary") -> str:
    """Renders HTML badge tag for markdown blocks."""
    colors = {
        "positive": ("#065F46", "#34D399"),
        "neutral": ("#334155", "#94A3B8"),
        "negative": ("#7F1D1D", "#F87171"),
        "primary": ("#312E81", "#818CF8"),
        "warning": ("#78350F", "#FBBF24"),
        "info": ("#164E63", "#22D3EE"),
    }
    bg, fg = colors.get(badge_type, ("#334155", "#CBD5E1"))
    return f'<span style="background-color: {bg}; color: {fg}; padding: 3px 10px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; display: inline-block; margin: 2px;">{text}</span>'

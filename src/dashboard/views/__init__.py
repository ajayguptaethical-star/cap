"""
Dashboard view modules.
"""
from src.dashboard.views.overview import render_overview
from src.dashboard.views.topic_explorer import render_topic_explorer
from src.dashboard.views.trend_drift import render_trend_drift
from src.dashboard.views.admin_governance import render_admin_governance
from src.dashboard.views.single_predict import render_single_predict

__all__ = [
    "render_overview",
    "render_topic_explorer",
    "render_trend_drift",
    "render_admin_governance",
    "render_single_predict"
]

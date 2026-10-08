"""
Main Streamlit application entrypoint for Multilingual Course Feedback Intelligence.
"""

import sys

# Ensure UTF-8 output encoding on Windows consoles to prevent cp1252 charmap crashes
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st
from src.dashboard.views import (
    render_overview,
    render_topic_explorer,
    render_trend_drift,
    render_admin_governance,
    render_single_predict
)

# Page configuration
st.set_page_config(
    page_title="Course Feedback Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics and clean typography
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top padding reduction */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #6366F1;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-weight: 500;
        font-size: 0.85rem;
    }
    div[data-testid="stMetricValue"] {
        color: #F8FAFC;
        font-weight: 700;
        font-size: 1.6rem;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def main():
    # Sidebar
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <h2 style="color: #6366F1; margin: 0;">🎓 FeedbackIQ</h2>
                <div style="color: #94A3B8; font-size: 0.8rem; font-weight: 500; margin-top: 4px;">
                    Multilingual Course Intelligence & Topic Drift
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")
        
        view_selection = st.radio(
            "Navigation Menu",
            [
                "📊 Executive KPI Dashboard",
                "🔍 Topic Deep-Dive Explorer",
                "📈 Longitudinal Trend & Drift",
                "🛡️ HITL Governance Cockpit",
                "🧪 Live Inference Sandbox"
            ],
            index=0
        )

        st.markdown("---")
        
        st.markdown(
            """
            <div style="background-color: #1E293B; padding: 12px; border-radius: 8px; font-size: 0.78rem; color: #94A3B8;">
                <p style="margin: 2px 0;"><b>Stack:</b> FastAPI + Streamlit</p>
                <p style="margin: 2px 0;"><b>NLP:</b> Devanagari NFC, LID, c-TF-IDF</p>
                <p style="margin: 2px 0;"><b>Innovation:</b> PSI & HITL Rollback</p>
                <p style="margin: 2px 0;"><b>Academic Cohort:</b> 2024–2026</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Route navigation
    if view_selection == "📊 Executive KPI Dashboard":
        render_overview()
    elif view_selection == "🔍 Topic Deep-Dive Explorer":
        render_topic_explorer()
    elif view_selection == "📈 Longitudinal Trend & Drift":
        render_trend_drift()
    elif view_selection == "🛡️ HITL Governance Cockpit":
        render_admin_governance()
    elif view_selection == "🧪 Live Inference Sandbox":
        render_single_predict()

if __name__ == "__main__":
    main()

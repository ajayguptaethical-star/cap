"""
View 3: Longitudinal Trend & Drift Monitor.
Visualizes topic dynamics across academic terms, computes Population Stability Index (PSI),
and alerts on significant curriculum or student sentiment drift.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.database.connection import SessionLocal
from src.database.repository import FeedbackRepository, TopicRepository
from src.innovation.drift_detector import calculate_psi
from src.dashboard.utils import apply_chart_theme, COLOR_PALETTE, render_badge

def render_trend_drift():
    st.markdown("## 📈 Longitudinal Trend & Topic Drift Monitor")
    st.markdown("Track term-over-term semantic shifts, monitor Population Stability Index (PSI), and detect emerging student concerns.")

    db = SessionLocal()
    try:
        feedback_repo = FeedbackRepository(db)
        topic_repo = TopicRepository(db)

        active_topics = topic_repo.get_active_topics()
        topic_name_map = {t.topic_code: t.topic_name for t in active_topics}

        # Load longitudinal data
        trend_records = feedback_repo.get_term_topic_distribution()
        if not trend_records:
            st.info("No longitudinal feedback distribution records found.")
            return

        df_trends = pd.DataFrame(trend_records)
        df_trends["topic_name"] = df_trends["topic_code"].map(lambda c: topic_name_map.get(c, c))

        # Chronological term ordering
        term_order = ["Fall 2024", "Spring 2025", "Fall 2025", "Spring 2026"]
        available_terms = [t for t in term_order if t in df_trends["term"].unique()]
        # Add any other terms not in term_order
        for t in df_trends["term"].unique():
            if t not in available_terms:
                available_terms.append(t)

        df_trends["term"] = pd.Categorical(df_trends["term"], categories=available_terms, ordered=True)
        df_trends = df_trends.sort_values(by="term")

        # Longitudinal Trend Chart
        st.subheader("📊 Term-over-Term Topic Volume Distribution")
        fig_trend = px.area(
            df_trends,
            x="term",
            y="count",
            color="topic_name",
            labels={"term": "Academic Term", "count": "Feedback Mentions", "topic_name": "Topic"},
            line_group="topic_name"
        )
        apply_chart_theme(fig_trend)
        st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("---")

        # Drift Calculation Section (PSI)
        st.subheader("🔬 Population Stability Index (PSI) Drift Gauge")
        st.markdown(
            """
            The **Population Stability Index (PSI)** measures semantic divergence between reference (baseline) and target evaluation cohorts:
            $$\\text{PSI} = \\sum_{i=1}^k (P_i - Q_i) \\times \\ln\\left(\\frac{P_i}{Q_i}\\right)$$
            - **PSI < 0.10**: Stable distribution (no significant drift)
            - **0.10 ≤ PSI < 0.25**: Moderate shift (monitoring recommended)
            - **PSI ≥ 0.25**: Actionable drift alert (triggers HITL review workflow)
            """
        )

        col_base, col_target = st.columns(2)
        with col_base:
            base_term = st.selectbox("Reference (Baseline) Term:", available_terms, index=0)
        with col_target:
            target_term = st.selectbox("Target (Evaluation) Term:", available_terms, index=len(available_terms) - 1)

        if base_term == target_term:
            st.warning("Please select distinct terms for reference and target evaluation.")
            return

        # Prepare vector distributions for PSI calculation
        all_topic_codes = sorted(list(topic_name_map.keys()))
        
        base_counts = {t: 0 for t in all_topic_codes}
        target_counts = {t: 0 for t in all_topic_codes}

        for row in trend_records:
            if row["term"] == base_term and row["topic_code"] in base_counts:
                base_counts[row["topic_code"]] = row["count"]
            elif row["term"] == target_term and row["topic_code"] in target_counts:
                target_counts[row["topic_code"]] = row["count"]

        total_base = sum(base_counts.values()) or 1
        total_target = sum(target_counts.values()) or 1

        eps = 1e-4
        p_vec = np.array([base_counts[t] / total_base for t in all_topic_codes])
        q_vec = np.array([target_counts[t] / total_target for t in all_topic_codes])

        psi_val = calculate_psi(p_vec, q_vec, eps=eps)

        # Gauge & Metric
        if psi_val < 0.10:
            status_text = "STABLE"
            status_color = "#10B981"
            status_desc = "Topic distributions are statistically consistent. No intervention required."
        elif psi_val < 0.25:
            status_text = "MODERATE SHIFT"
            status_color = "#F59E0B"
            status_desc = "Mild topic volume reallocation detected. Advise monitoring upcoming terms."
        else:
            status_text = "SIGNIFICANT DRIFT ALERT"
            status_color = "#EF4444"
            status_desc = "Severe semantic shift detected. Triggers Stage 2 HITL candidate review."

        col_gauge, col_interp = st.columns([2, 3])
        with col_gauge:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=psi_val,
                title={"text": f"PSI ({base_term} → {target_term})", "font": {"size": 16, "color": "#F8FAFC"}},
                gauge={
                    "axis": {"range": [0, 0.6], "tickwidth": 1, "tickcolor": "#94A3B8"},
                    "bar": {"color": status_color},
                    "steps": [
                        {"range": [0, 0.10], "color": "rgba(16, 185, 129, 0.2)"},
                        {"range": [0.10, 0.25], "color": "rgba(245, 158, 11, 0.2)"},
                        {"range": [0.25, 0.6], "color": "rgba(239, 68, 68, 0.2)"}
                    ],
                    "threshold": {
                        "line": {"color": "#EF4444", "width": 4},
                        "thickness": 0.75,
                        "value": 0.25
                    }
                }
            ))
            apply_chart_theme(fig_gauge)
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_interp:
            st.markdown(
                f"""
                <div style="background-color: #1E293B; padding: 20px; border-radius: 12px; border-left: 5px solid {status_color}; margin-top: 15px;">
                    <h3 style="color: {status_color}; margin-top: 0;">Status: {status_text}</h3>
                    <p style="color: #F8FAFC; font-size: 1.1rem; margin-bottom: 6px;">
                        Computed PSI: <b>{psi_val:.4f}</b>
                    </p>
                    <p style="color: #94A3B8; font-size: 0.95rem; margin-bottom: 12px;">{status_desc}</p>
                    <div style="font-size: 0.85rem; color: #CBD5E1;">
                        Evaluated across <b>{len(all_topic_codes)}</b> topic buckets comparing {base_term} (N={total_base}) against {target_term} (N={total_target}).
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Detailed PSI Component Breakdown Table
        st.subheader("📋 Topic Divergence Component Decomposition")
        psi_details = []
        for i, code in enumerate(all_topic_codes):
            p_i = (p_vec[i] + eps) / (1 + eps * len(p_vec))
            q_i = (q_vec[i] + eps) / (1 + eps * len(q_vec))
            contrib = (p_i - q_i) * np.log(p_i / q_i)
            psi_details.append({
                "Topic Code": code,
                "Topic Name": topic_name_map.get(code, code),
                f"{base_term} %": f"{p_vec[i] * 100:.1f}%",
                f"{target_term} %": f"{q_vec[i] * 100:.1f}%",
                "Shift (Δ)": f"{(q_vec[i] - p_vec[i]) * 100:+.1f}%",
                "PSI Contribution": round(float(contrib), 4)
            })

        df_psi = pd.DataFrame(psi_details).sort_values(by="PSI Contribution", ascending=False)
        st.dataframe(df_psi, use_container_width=True, hide_index=True)

    finally:
        db.close()

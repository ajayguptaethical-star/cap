"""
View 1: Executive KPI Dashboard.
Provides high-level metrics, language diversity breakdown, topic distribution, and live feedback stream.
Includes 5-second Live Dataset Ingestion and auto-refresh using st.fragment.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone

from src.database.connection import SessionLocal
from src.database.repository import FeedbackRepository, TopicRepository
from src.dashboard.utils import apply_chart_theme, COLOR_PALETTE, render_badge
from src.dashboard.live_stream import generate_live_feedback

def render_overview():
    st.markdown("## Executive Feedback Intelligence Dashboard")
    st.markdown("Real-time aggregated analytics across multilingual student feedback, institutional topics, and live 5-second ingestion.")

    if "live_enabled" not in st.session_state:
        st.session_state.live_enabled = True

    if "last_ingested_comment" not in st.session_state:
        st.session_state.last_ingested_comment = None

    if "stream_limit" not in st.session_state:
        st.session_state.stream_limit = 50

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 1.5, 1.5])
    with ctrl_col1:
        st.session_state.live_enabled = st.toggle(
            "Enable 5-Second Live Dataset Auto-Update & Chart Refresh",
            value=st.session_state.live_enabled,
            help="Automatically inserts 1 new student feedback every 5 seconds and updates all charts."
        )
    with ctrl_col2:
        st.session_state.stream_limit = st.selectbox(
            "Stream Visible Count",
            options=[10, 25, 50, 100, 200],
            index=2,
            help="Number of recent feedback items displayed in the live stream."
        )
    with ctrl_col3:
        manual_click = st.button("Ingest Sample Now")

    if manual_click:
        db_manual = SessionLocal()
        try:
            new_rec = generate_live_feedback(db_manual)
            st.session_state.last_ingested_comment = new_rec
            st.toast(f"Ingested 1 sample ({new_rec['comment_id']})", icon="?")
        finally:
            db_manual.close()

    if st.session_state.live_enabled:
        last_info = ""
        if st.session_state.last_ingested_comment:
            c = st.session_state.last_ingested_comment
            last_info = f" | Latest record: <b>{c['comment_id']}</b> ({c['lang'].upper()} - {c['sentiment'].capitalize()} for {c['course']})"
        
        st.markdown(
            f"<div style='background-color: #064E3B; border: 1px solid #10B981; padding: 10px 16px; border-radius: 8px; color: #A7F3D0; font-size: 0.9rem; margin-bottom: 15px;'><b>LIVE INGESTION ACTIVE</b>: Inserting new multilingual feedback into database every 5 seconds. {last_info}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='background-color: #334155; border: 1px solid #64748B; padding: 10px 16px; border-radius: 8px; color: #CBD5E1; font-size: 0.9rem; margin-bottom: 15px;'><b>LIVE INGESTION PAUSED</b>: Toggle switch above to resume 5-second live dataset stream.</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    run_interval = 5 if st.session_state.live_enabled else None

    @st.fragment(run_every=run_interval)
    def live_dashboard_content():
        db = SessionLocal()
        try:
            if st.session_state.live_enabled:
                new_rec = generate_live_feedback(db)
                st.session_state.last_ingested_comment = new_rec

            feedback_repo = FeedbackRepository(db)
            topic_repo = TopicRepository(db)

            total_feedback = feedback_repo.get_feedback_count()
            lang_dist = feedback_repo.get_language_distribution()
            sent_dist = feedback_repo.get_sentiment_distribution()
            topic_dist = feedback_repo.get_topic_distribution()
            active_version = topic_repo.get_active_version()
            active_topics = topic_repo.get_active_topics()

            non_en_count = sum(count for lang, count in lang_dist.items() if lang != "en")
            multilingual_pct = (non_en_count / total_feedback * 100) if total_feedback > 0 else 0.0

            pos_count = sent_dist.get("positive", 0)
            neg_count = sent_dist.get("negative", 0)
            pos_pct = (pos_count / total_feedback * 100) if total_feedback > 0 else 0.0
            neg_pct = (neg_count / total_feedback * 100) if total_feedback > 0 else 0.0

            now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            st.markdown(
                f"<div style='text-align: right; color: #94A3B8; font-size: 0.8rem; margin-bottom: 10px;'>Last Refreshed: <b>{now_str}</b> (Auto-refreshes every 5s)</div>",
                unsafe_allow_html=True
            )

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.metric("Total Feedback Analyzed", f"{total_feedback:,}", delta="+1 live record")
            with kpi2:
                st.metric("Multilingual Coverage", f"{multilingual_pct:.1f}%", delta="Non-English %")
            with kpi3:
                st.metric("Active Topics Catalog", f"{len(active_topics)} Topics", delta=f"Version {active_version.version_tag if active_version else 'v1.0.0'}")
            with kpi4:
                st.metric("Positive Sentiment Rate", f"{pos_pct:.1f}%", delta=f"-{neg_pct:.1f}% Negative", delta_color="normal")

            st.markdown("<br>", unsafe_allow_html=True)

            col_lang, col_sent = st.columns(2)
            
            with col_lang:
                st.subheader("Language & Script Diversity")
                if lang_dist:
                    lang_df = pd.DataFrame([
                        {"Language": lang.upper(), "Count": count} for lang, count in lang_dist.items()
                    ])
                    fig_lang = px.pie(
                        lang_df,
                        names="Language",
                        values="Count",
                        hole=0.45,
                        color="Language",
                        color_discrete_map={
                            "EN": COLOR_PALETTE["languages"]["en"],
                            "HI": COLOR_PALETTE["languages"]["hi"],
                            "MR": COLOR_PALETTE["languages"]["mr"],
                            "HINGLISH": COLOR_PALETTE["languages"]["hinglish"],
                            "MARATHLISH": COLOR_PALETTE["languages"]["marathlish"]
                        }
                    )
                    fig_lang.update_traces(textposition="inside", textinfo="percent+label")
                    apply_chart_theme(fig_lang)
                    st.plotly_chart(fig_lang, use_container_width=True, key=f"pie_lang_{total_feedback}")
                else:
                    st.info("No language distribution data available.")

            with col_sent:
                st.subheader("Sentiment Distribution")
                if sent_dist:
                    sent_df = pd.DataFrame([
                        {"Sentiment": k.capitalize(), "Count": v} for k, v in sent_dist.items()
                    ])
                    fig_sent = px.bar(
                        sent_df,
                        x="Sentiment",
                        y="Count",
                        color="Sentiment",
                        color_discrete_map={
                            "Positive": COLOR_PALETTE["positive"],
                            "Neutral": COLOR_PALETTE["neutral"],
                            "Negative": COLOR_PALETTE["negative"]
                        },
                        text="Count"
                    )
                    fig_sent.update_traces(textposition="outside")
                    apply_chart_theme(fig_sent)
                    st.plotly_chart(fig_sent, use_container_width=True, key=f"bar_sent_{total_feedback}")
                else:
                    st.info("No sentiment distribution data available.")

            st.subheader("Topic Volume Distribution")
            if topic_dist and active_topics:
                topic_name_map = {t.topic_code: t.topic_name for t in active_topics}
                topic_data = []
                for code, count in topic_dist.items():
                    topic_data.append({
                        "Topic Code": code,
                        "Topic Name": topic_name_map.get(code, code),
                        "Feedback Count": count
                    })
                topic_df = pd.DataFrame(topic_data).sort_values(by="Feedback Count", ascending=True)

                fig_topic = px.bar(
                    topic_df,
                    x="Feedback Count",
                    y="Topic Name",
                    orientation="h",
                    color="Feedback Count",
                    color_continuous_scale="Viridis",
                    text="Feedback Count"
                )
                fig_topic.update_traces(textposition="outside")
                apply_chart_theme(fig_topic)
                st.plotly_chart(fig_topic, use_container_width=True, key=f"bar_topic_{total_feedback}")

            limit_val = st.session_state.stream_limit
            recent = feedback_repo.query_feedback(limit=limit_val)
            
            latest_id = st.session_state.last_ingested_comment["comment_id"] if st.session_state.last_ingested_comment else (recent[0].comment_id if recent else "")

            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 25px; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="background-color: #EF4444; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 800; letter-spacing: 1px; box-shadow: 0 0 10px rgba(239, 68, 68, 0.4);">LIVE STREAM</span>
                        <span style="font-size: 1.3rem; font-weight: 700; color: #F8FAFC;">Feedback Submissions Stream</span>
                    </div>
                    <div style="color: #94A3B8; font-size: 0.85rem; font-weight: 600;">
                        Showing <b>{len(recent)}</b> of <b>{total_feedback:,}</b> entries
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if recent:
                with st.container(height=480):
                    for idx, r in enumerate(recent):
                        is_latest = (r.comment_id == latest_id) or (idx == 0)
                        
                        badge_sent_type = "positive" if r.overall_sentiment == "positive" else ("negative" if r.overall_sentiment == "negative" else "neutral")
                        lang_badge = render_badge(r.detected_language.upper(), "info")
                        topic_badge = render_badge(r.primary_topic_code, "primary")
                        sent_badge = render_badge(r.overall_sentiment.capitalize(), badge_sent_type)
                        term_badge = render_badge(r.academic_term, "neutral")

                        if is_latest and st.session_state.live_enabled:
                            live_badge = '<span style="background-color: #10B981; color: #042F2E; padding: 3px 10px; border-radius: 12px; font-weight: 800; font-size: 0.72rem; letter-spacing: 0.5px;">JUST INGESTED LIVE</span>'
                            card_style = "background-color: #064E3B22; border: 1.5px solid #10B981; border-left: 6px solid #10B981; box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);"
                        else:
                            live_badge = '<span style="background-color: #334155; color: #38BDF8; padding: 2px 8px; border-radius: 10px; font-weight: 600; font-size: 0.7rem;">LIVE FEED</span>'
                            card_style = "background-color: #1E293B; border: 1px solid #334155; border-left: 4px solid #6366F1;"

                        st.markdown(
                            f"""
                            <div style="{card_style} padding: 14px 18px; border-radius: 10px; margin-bottom: 12px;">
                                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                                    <div>
                                        {live_badge} {lang_badge} {topic_badge} {sent_badge} {term_badge}
                                    </div>
                                    <div style="color: #94A3B8; font-size: 0.8rem;">
                                        ID: <b style="color: #CBD5E1;">{r.comment_id}</b> | Course: <b style="color: #818CF8;">{r.course_code}</b> | Inst: <b style="color: #F472B6;">{r.instructor_id}</b>
                                    </div>
                                </div>
                                <div style="color: #F8FAFC; font-size: 0.96rem; font-style: italic; line-height: 1.4;">
                                    &quot;{r.cleaned_text}&quot;
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            else:
                st.info("No recent feedback found in database.")

        finally:
            db.close()

    live_dashboard_content()

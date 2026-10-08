"""
View 2: Topic Deep-Dive Explorer.
Inspects individual topics, c-TF-IDF keywords, aspect sentiment distributions, and representative exemplar quotes.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.database.connection import SessionLocal
from src.database.repository import FeedbackRepository, TopicRepository
from src.dashboard.utils import apply_chart_theme, COLOR_PALETTE, render_badge

def render_topic_explorer():
    st.markdown("## 🔍 Topic Deep-Dive & Aspect Sentiment Explorer")
    st.markdown("Examine discovered themes, c-TF-IDF keyword signatures, aspect-specific sentiment breakdowns, and representative student quotes.")

    db = SessionLocal()
    try:
        topic_repo = TopicRepository(db)
        feedback_repo = FeedbackRepository(db)

        active_topics = topic_repo.get_active_topics()
        if not active_topics:
            st.warning("No active topics found. Run the topic pipeline first.")
            return

        # Topic Selector Dropdown
        topic_options = {f"{t.topic_code} - {t.topic_name}": t for t in active_topics}
        selected_label = st.selectbox("Select Topic to Inspect:", list(topic_options.keys()))
        selected_topic = topic_options[selected_label]

        # Topic Header Card
        emergent_badge = render_badge("EMERGENT (DRIFT)", "warning") if selected_topic.is_emergent else render_badge("CORE CATALOG", "primary")
        st.markdown(
            f"""
            <div style="background-color: #1E293B; padding: 20px; border-radius: 12px; margin-bottom: 20px; border-top: 4px solid #06B6D4;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #F8FAFC;">{selected_topic.topic_name} ({selected_topic.topic_code})</h3>
                    <div>{emergent_badge}</div>
                </div>
                <p style="color: #94A3B8; margin-top: 8px; margin-bottom: 12px;">{selected_topic.description or 'No description available.'}</p>
                <div style="color: #CBD5E1; font-size: 0.9rem;">
                    <b>Sample Feedback Volume:</b> {selected_topic.comment_count} comments
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # c-TF-IDF Keywords Chips
        st.subheader("🏷️ c-TF-IDF Discriminative Keyword Signature")
        keywords = [k.strip() for k in (selected_topic.top_keywords or "").split(",") if k.strip()]
        if keywords:
            chips_html = " ".join([render_badge(kw, "info") for kw in keywords])
            st.markdown(f"<div style='margin-bottom: 24px;'>{chips_html}</div>", unsafe_allow_html=True)
        else:
            st.info("No keywords defined for this topic.")

        # Aspect Sentiment Breakdown for this topic
        col_chart, col_stats = st.columns([3, 2])

        # Fetch aspect sentiments for this topic
        aspect_dist = feedback_repo.get_topic_aspect_sentiment_distribution()
        topic_aspects = [a for a in aspect_dist if a["topic_code"] == selected_topic.topic_code]

        with col_chart:
            st.subheader("📊 Aspect Sentiment Breakdown")
            if topic_aspects:
                asp_df = pd.DataFrame(topic_aspects)
                fig_asp = px.bar(
                    asp_df,
                    x="sentiment_label",
                    y="count",
                    color="sentiment_label",
                    color_discrete_map={
                        "positive": COLOR_PALETTE["positive"],
                        "neutral": COLOR_PALETTE["neutral"],
                        "negative": COLOR_PALETTE["negative"]
                    },
                    labels={"sentiment_label": "Aspect Polarity", "count": "Mentions"},
                    text="count"
                )
                fig_asp.update_traces(textposition="outside")
                apply_chart_theme(fig_asp)
                st.plotly_chart(fig_asp, use_container_width=True)
            else:
                st.info("No aspect sentiment records found specifically for this topic.")

        with col_stats:
            st.subheader("📈 Polarity Metrics")
            if topic_aspects:
                total_mentions = sum(a["count"] for a in topic_aspects)
                pos = sum(a["count"] for a in topic_aspects if a["sentiment_label"] == "positive")
                neg = sum(a["count"] for a in topic_aspects if a["sentiment_label"] == "negative")
                neu = sum(a["count"] for a in topic_aspects if a["sentiment_label"] == "neutral")

                pos_ratio = (pos / total_mentions * 100) if total_mentions else 0
                neg_ratio = (neg / total_mentions * 100) if total_mentions else 0
                net_promoter = pos_ratio - neg_ratio

                st.markdown(
                    f"""
                    <div style="background-color: #0F172A; padding: 16px; border-radius: 10px; border: 1px solid #334155;">
                        <p style="margin: 4px 0; color: #94A3B8;">Total Aspect Mentions: <b style="color: #F8FAFC;">{total_mentions}</b></p>
                        <p style="margin: 4px 0; color: #10B981;">Positive Rate: <b>{pos_ratio:.1f}%</b> ({pos})</p>
                        <p style="margin: 4px 0; color: #94A3B8;">Neutral Rate: <b>{(neu / total_mentions * 100) if total_mentions else 0:.1f}%</b> ({neu})</p>
                        <p style="margin: 4px 0; color: #EF4444;">Negative Rate: <b>{neg_ratio:.1f}%</b> ({neg})</p>
                        <hr style="border-color: #334155; margin: 10px 0;">
                        <p style="margin: 4px 0; font-size: 1.05rem; color: {'#10B981' if net_promoter >= 0 else '#EF4444'};">
                            Net Topic Sentiment: <b>{net_promoter:+.1f} pts</b>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Representative Exemplar Quotes
        st.subheader("💬 Representative Exemplar Feedback")
        st.markdown("Verbatim student comments exhibiting high thematic alignment with this topic:")
        exemplars = feedback_repo.get_exemplar_comments(selected_topic.topic_code, limit=5)

        if exemplars:
            for ex in exemplars:
                sent_type = "positive" if ex.overall_sentiment == "positive" else ("negative" if ex.overall_sentiment == "negative" else "neutral")
                b_lang = render_badge(ex.detected_language.upper(), "info")
                b_sent = render_badge(ex.overall_sentiment.capitalize(), sent_type)
                b_term = render_badge(ex.academic_term, "neutral")

                st.markdown(
                    f"""
                    <div style="background-color: #1E293B; padding: 14px; border-radius: 8px; margin-bottom: 10px; border-left: 3px solid #38BDF8;">
                        <div style="margin-bottom: 6px;">
                            {b_lang} {b_sent} {b_term}
                            <span style="color: #94A3B8; font-size: 0.8rem; margin-left: 8px;">Course: <b>{ex.course_code}</b> | Outlier Score: {ex.outlier_score:.3f}</span>
                        </div>
                        <div style="color: #F1F5F9; font-size: 0.95rem;">
                            "{ex.cleaned_text}"
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No exemplar comments recorded for this topic.")

    finally:
        db.close()

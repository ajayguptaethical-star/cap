"""
View 5: Live Feedback Inference Sandbox.
Provides an interactive real-time analysis console for testing open-ended multilingual feedback.
Computes language identification, topic assignment, aspect-based sentiment with evidence spans, and novelty outlier scores.
"""

import streamlit as st
import pandas as pd

from src.database.connection import SessionLocal
from src.database.repository import TopicRepository
from src.preprocessing.normalizer import normalize_multilingual_text
from src.preprocessing.lang_detector import detect_language
from src.topic_modeling.bertopic_engine import MultilingualTopicEngine
from src.sentiment.aspect_sentiment import AspectSentimentAnalyzer
from src.innovation.drift_detector import compute_outlier_score
from src.dashboard.utils import render_badge

SAMPLE_TEXTS = {
    "English - Mixed Feedback": "The lectures were clear and engaging, but the lab assignments were far too difficult and servers crashed constantly.",
    "Hindi - Pedagogy & Workload": "प्रोफेसर बहुत अच्छे से पढ़ाते हैं लेकिन असाइनमेंट का लोड बहुत ज्यादा है।",
    "Marathi - Lab Infrastructure": "शिकवण्याची पद्धत अतिशय उत्कृष्ट होती, पण प्रॅक्टिकल लॅबमध्ये संगणक नीट चालत नाहीत.",
    "Hinglish - Connectivity & Tech": "Teaching standard was decent but Wi-Fi connection bilkul bekar tha and lab machines hung ho rahi thi.",
    "Marathlish - Attendance & Policy": "Sir khoop chaan samjavtat pan projector nehamich band padto aani attendance rule khup strict aahe.",
    "Emergent Drift - GenAI Policy": "ChatGPT policies are totally confusing, can we use AI tools for our homework coding assignments or not?"
}

import time
import requests
import xml.etree.ElementTree as ET
import random

def fetch_google_data():
    """Fetches random text from Google News RSS for course feedback to simulate live data."""
    try:
        url = "https://news.google.com/rss/search?q=student+feedback+university+course&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, timeout=1.0)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item/title')
            if items:
                # Clean up title (remove publisher suffix)
                title = random.choice(items).text
                return title.rsplit(" - ", 1)[0]
    except Exception:
        pass
    
    # Fallback to simulate a stream of Google-like reviews
    reviews = [
        "The course structure was a bit confusing but the instructor was amazing.",
        "Worst experience ever, the wifi in the lab never works.",
        "I really enjoyed the assignments, they were challenging but fair.",
        "Prof. Smith's lectures are incredibly boring and the exams are too long.",
        "Loved the hybrid classes! Camera quality was top notch.",
        "TAs are very unapproachable and grading is unfair.",
        "Maza aagaya padh ke, the concepts are crystal clear now.",
        "Lॅबमध्ये इंटरनेट खूप स्लो आहे, काहीच काम होत नाही."
    ]
    return random.choice(reviews)

from sqlalchemy import text

@st.cache_resource
def get_cached_engines():
    """Initializes and caches NLP engines for responsive dashboard inference."""
    try:
        topic_engine = MultilingualTopicEngine.load("model.joblib")
    except Exception:
        # Fallback if model not saved yet
        db = SessionLocal()
        try:
            records = db.execute(text("SELECT cleaned_text FROM feedback LIMIT 300")).fetchall()
            texts = [r[0] for r in records if r[0]]
        except Exception:
            texts = []
        finally:
            db.close()
            
        if len(texts) < 10:
            texts = list(SAMPLE_TEXTS.values()) * 3 # Duplicate to satisfy min_df=2
            
        topic_engine = MultilingualTopicEngine(n_topics=6)
        if len(texts) < 10:
            topic_engine.vectorizer.min_df = 1
            
        topic_engine.fit(texts)
        # Try saving for future fast loads
        try:
            topic_engine.save("model.joblib")
        except Exception:
            pass
    
    sentiment_engine = AspectSentimentAnalyzer()
    return topic_engine, sentiment_engine

def render_single_predict():
    # Inject Custom CSS for Animations
    st.markdown("""
        <style>
        @keyframes glowBox {
            0% { box-shadow: 0 0 5px rgba(99, 102, 241, 0.2); border-color: #334155; }
            50% { box-shadow: 0 0 25px rgba(99, 102, 241, 0.7); border-color: #818CF8; }
            100% { box-shadow: 0 0 5px rgba(99, 102, 241, 0.2); border-color: #334155; }
        }
        .animated-title {
            text-align: center;
            border: 2px solid #334155;
            padding: 15px;
            border-radius: 12px;
            margin-bottom: 25px;
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            animation: glowBox 2.5s infinite alternate;
            color: #F8FAFC;
        }
        @keyframes pulseEmoji {
            0% { transform: scale(1) rotate(0deg); }
            50% { transform: scale(1.2) rotate(10deg); }
            100% { transform: scale(1) rotate(0deg); }
        }
        .pulse-emoji {
            display: inline-block;
            animation: pulseEmoji 2s infinite ease-in-out;
        }
        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .result-container {
            animation: fadeSlideUp 0.6s ease-out forwards;
            padding: 10px 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 class='animated-title'><span class='pulse-emoji'>⚡</span> Live Feedback Inference Sandbox <span class='pulse-emoji'>🧠</span></h2>", unsafe_allow_html=True)

    topic_engine, sentiment_engine = get_cached_engines()
    db = SessionLocal()
    try:
        topic_repo = TopicRepository(db)
        active_topics = topic_repo.get_active_topics()
        topic_name_map = {t.topic_code: t.topic_name for t in active_topics}

        live_mode = st.toggle("📡 Enable Live Stream (Auto-Fetch)")
        
        if live_mode:
            st.markdown("<div style='color:#EF4444; font-weight:600; margin-bottom: 10px;'><span class='pulse-emoji'>🔴</span> Live mode active: Streaming data...</div>", unsafe_allow_html=True)
            
        with st.container(border=True):
            if live_mode:
                input_text = fetch_google_data()
                st.text_area("📝 Enter Feedback:", value=input_text, height=100, disabled=True)
            else:
                input_text = st.text_area("📝 Enter Feedback:", height=100)

            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                analyze_clicked = st.button("🚀 Analyze Feedback", use_container_width=True)

            if live_mode or analyze_clicked or (input_text and input_text.strip()):
                if not input_text.strip():
                    st.warning("⚠️ Please enter feedback text to analyze.")
                    return

                with st.spinner("⏳ Processing..."):
                    cleaned_text = normalize_multilingual_text(input_text)
                    lang_code, _, _ = detect_language(input_text)
                    
                    LANG_MAP = {'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi', 'hinglish': 'Hinglish', 'marathlish': 'Marathlish'}
                    full_lang = LANG_MAP.get(lang_code.lower(), lang_code.upper())

                    topic_indices, max_sims, _ = topic_engine.transform([cleaned_text])
                    topic_code = f"TOPIC_{topic_indices[0] + 1}"
                    topic_name = topic_name_map.get(topic_code, topic_code)

                    aspect_res = sentiment_engine.analyze(cleaned_text, primary_topic=topic_code)
                    overall_sentiment = aspect_res['overall_sentiment'].capitalize()
                    
                    sentiment_emoji = "😃" if overall_sentiment == "Positive" else ("😡" if overall_sentiment == "Negative" else "😐")

                    aspects = aspect_res.get("aspects", [])
                    aspect_names = []
                    for a in aspects:
                        t_name = topic_name_map.get(a["topic_code"], a["topic_code"])
                        if t_name not in aspect_names:
                            aspect_names.append(t_name)
                    
                    if not aspect_names:
                        aspect_names = [topic_name]

                st.markdown("---")
                st.markdown("<div class='result-container'>", unsafe_allow_html=True)
                st.markdown(f"**🌐 Language:** {full_lang}")
                st.markdown(f"**{sentiment_emoji} Sentiment:** {overall_sentiment}")
                
                st.markdown("<br>**🎯 Aspects:**", unsafe_allow_html=True)
                for a in aspect_names:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✨ {a}")
                    
                st.markdown("<br>**📌 Topics:**", unsafe_allow_html=True)
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🏷️ {topic_name}")
                for a in aspect_names:
                    if a != topic_name:
                         st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🏷️ {a}")
                st.markdown("</div>", unsafe_allow_html=True)
                         
        if live_mode:
            time.sleep(1.5)
            st.rerun()

    finally:
        db.close()

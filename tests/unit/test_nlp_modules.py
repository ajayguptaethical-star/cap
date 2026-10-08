"""
Unit tests for Milestone 3: NLP Preprocessing, Language ID, Topic Modeling, and Aspect Sentiment.
"""

import pytest
import numpy as np

from src.preprocessing.normalizer import clean_text, normalize_devanagari, sanitize_pii, detect_script
from src.preprocessing.lang_detector import detect_language
from src.topic_modeling.baseline_lda import BaselineLDAModel
from src.topic_modeling.bertopic_engine import MultilingualTopicEngine
from src.topic_modeling.coherence import compute_topic_coherence
from src.sentiment.baseline_lexicon import analyze_lexicon_sentiment
from src.sentiment.aspect_sentiment import AspectSentimentAnalyzer

# ---------------------------------------------------------------------------
# Preprocessing & Normalization Tests
# ---------------------------------------------------------------------------
def test_devanagari_normalization():
    """Verify zero-width characters are removed and NFC normalization is applied."""
    raw_with_zwj = "विद्या\u200Cर्थी"  # Contains invisible zero-width non-joiner
    cleaned = normalize_devanagari(raw_with_zwj)
    assert "\u200C" not in cleaned
    assert len(cleaned) < len(raw_with_zwj)

def test_pii_sanitization():
    """Verify student roll numbers, emails, and phone numbers are redacted."""
    text = "My roll number is 2023BDS1042 and email is student@univ.edu. Call 9820012345."
    sanitized = sanitize_pii(text)
    assert "[REDACTED_STUDENT_ID]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "student@univ.edu" not in sanitized
    assert "9820012345" not in sanitized

def test_script_detection():
    """Verify script identification for Latin and Devanagari texts."""
    assert detect_script("The professor is great.") == "Latin"
    assert detect_script("प्राध्यापक खूप छान शिकवतात.") == "Devanagari"
    assert detect_script("प्रोफेसर बहुत अच्छा पढ़ाते हैं.") == "Devanagari"

# ---------------------------------------------------------------------------
# Language Identification Tests
# ---------------------------------------------------------------------------
def test_multilingual_language_detection():
    """Verify language classifier identifies all 5 target language categories."""
    # English
    lang_en, conf_en, script_en = detect_language("The lecture was clear, structured, and very helpful.")
    assert lang_en == "en"
    assert script_en == "Latin"
    assert conf_en > 0.80

    # Hindi Devanagari
    lang_hi, conf_hi, script_hi = detect_language("प्रोफेसर बहुत ही सहजता और गहराई से पढ़ाते हैं, कक्षा बहुत अच्छी रही।")
    assert lang_hi == "hi"
    assert script_hi == "Devanagari"
    assert conf_hi > 0.70

    # Marathi Devanagari
    lang_mr, conf_mr, script_mr = detect_language("प्राध्यापक प्रत्येक संकल्पना अत्यंत सोप्या भाषेत समजावून सांगतात, खूप छान शिकवले.")
    assert lang_mr == "mr"
    assert script_mr == "Devanagari"
    assert conf_mr > 0.70

    # Hinglish
    lang_hien, conf_hien, script_hien = detect_language("Prof ke explanations bohot acche the, samajh aa gaya maza aa gaya.")
    assert lang_hien == "hi-en"
    assert script_hien == "Latin"
    assert conf_hien > 0.70

    # Marathlish
    lang_mren, conf_mren, script_mren = detect_language("Shikavnyacha speed khup fast ahe, kahi note karta yet nahi pan changle ahe.")
    assert lang_mren == "mr-en"
    assert script_mren == "Latin"
    assert conf_mren > 0.70

# ---------------------------------------------------------------------------
# Topic Modeling Tests
# ---------------------------------------------------------------------------
def test_baseline_lda_and_advanced_topic_engine():
    """Verify LDA baseline and Advanced Multilingual Topic Engine training and keyword extraction."""
    sample_docs = [
        "The professor explains mathematical derivations with exceptional clarity.",
        "Pacing is perfect; complex concepts are broken down into intuitive examples.",
        "Assignment workload is unmanageable alongside other core courses.",
        "Problem set descriptions are extremely ambiguous with conflicting deadlines.",
        "Lab workstations crashed continuously during machine learning model training.",
        "Campus Wi-Fi drops constantly during timed lab practical exams.",
        "Grading rubrics were transparent, fair, and distributed before submissions.",
        "TA feedback on exam papers was detailed, constructive, and prompt.",
        "Syllabus is modern, comprehensive, and aligns with modern data industry standards.",
        "The instructor is dismissive during doubt sessions and rarely answers emails.",
        "प्रोफेसर बहुत ही सहजता और गहराई से हर विषय समझाते हैं।",
        "असाइनमेंट का बोझ बहुत अधिक है, पूरा करने का समय ही नहीं मिलता।",
        "संगणक प्रयोगशाळेतील उपकरणे आणि जीपीयूपी सुविधा अतिशय आधुनिक आहेत.",
        "Grading bohot arbitrary aur unfair lagti hai, TAs ke mood pe depend karta hai."
    ] * 3  # Duplicate to provide enough samples

    # Baseline LDA
    lda = BaselineLDAModel(n_topics=3, random_state=42)
    lda.fit(sample_docs)
    lda_keywords = lda.get_topic_keywords(top_n=5)
    assert len(lda_keywords) == 3
    lda_preds = lda.predict(sample_docs[:2])
    assert len(lda_preds) == 2

    # Advanced Multilingual Engine
    engine = MultilingualTopicEngine(n_topics=3, random_state=42)
    engine.fit(sample_docs)
    adv_keywords = engine.get_topic_keywords()
    assert len(adv_keywords) == 3
    
    indices, sims, outliers = engine.transform(sample_docs[:2])
    assert len(indices) == 2
    assert len(sims) == 2
    assert len(outliers) == 2
    assert all(0.0 <= s <= 1.0 for s in sims)
    assert all(0.0 <= o <= 1.0 for o in outliers)

    # Exemplars
    exemplars = engine.get_exemplars(topic_id=0, top_k=2)
    assert len(exemplars) <= 2
    if exemplars:
        assert isinstance(exemplars[0][0], str)
        assert isinstance(exemplars[0][1], float)

    # Coherence Evaluation
    coherence = compute_topic_coherence(adv_keywords, sample_docs, top_n=5)
    assert "mean_coherence" in coherence
    assert isinstance(coherence["mean_coherence"], float)

# ---------------------------------------------------------------------------
# Aspect Sentiment Analysis Tests
# ---------------------------------------------------------------------------
def test_sentiment_baseline_with_negation():
    """Verify rule-based lexicon handles positive, negative, and negated polarity."""
    pos_res = analyze_lexicon_sentiment("The lecture was clear, structured, and helpful.")
    assert pos_res["sentiment_label"] == "positive"
    assert pos_res["sentiment_score"] > 0.20

    neg_res = analyze_lexicon_sentiment("Lab systems crashed and the grading was terrible.")
    assert neg_res["sentiment_label"] == "negative"
    assert neg_res["sentiment_score"] < -0.20

    # Negation inversion: 'not good' must be negative!
    negated_res = analyze_lexicon_sentiment("The lecture was not good and explanations were confusing.")
    assert negated_res["sentiment_label"] == "negative"

def test_aspect_sentiment_compound_extraction():
    """Verify ABSA attributes contrasting sentiments to multiple topics within the same comment."""
    compound_comment = "Prof explains derivations clearly and teaching was great, but lab machines crash constantly!"
    analyzer = AspectSentimentAnalyzer()
    overall_label, overall_score, aspects = analyzer.analyze_aspects(compound_comment, primary_topic="TOPIC_1")

    # Should detect both TOPIC_1 (Pedagogy) and TOPIC_5 (Lab)
    topic_codes = [a["topic_code"] for a in aspects]
    assert "TOPIC_1" in topic_codes
    assert "TOPIC_5" in topic_codes

    # TOPIC_1 should be positive, TOPIC_5 should be negative
    topic_1_asp = next(a for a in aspects if a["topic_code"] == "TOPIC_1")
    topic_5_asp = next(a for a in aspects if a["topic_code"] == "TOPIC_5")

    assert topic_1_asp["sentiment_label"] == "positive"
    assert topic_5_asp["sentiment_label"] == "negative"
    assert topic_5_asp["evidence_span"] is not None

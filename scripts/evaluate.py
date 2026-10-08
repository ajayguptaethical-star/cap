"""
Comprehensive Evaluation Suite for Course Feedback Intelligence.
Computes ground-truth verified metrics across:
1. Language Identification (LID)
2. Aspect-Based Sentiment Analysis (ABSA)
3. Outlier / Novelty Threshold (tau) Ablation Sweep
4. Topic Coherence Comparison (Baseline LDA vs Advanced Multilingual Engine)

Persists all computed results to evaluation_results.json.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
    precision_recall_fscore_support
)

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.preprocessing.normalizer import clean_text
from src.preprocessing.lang_detector import detect_language
from src.sentiment.aspect_sentiment import AspectSentimentAnalyzer
from src.topic_modeling.baseline_lda import BaselineLDAModel
from src.topic_modeling.bertopic_engine import MultilingualTopicEngine
from src.topic_modeling.coherence import compute_topic_coherence


def evaluate_language_id(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates Language Identification against true_language ground truth.
    """
    print("\n" + "=" * 60)
    print("1. EVALUATING LANGUAGE IDENTIFICATION (LID)")
    print("=" * 60)

    y_true = df["true_language"].astype(str).tolist()
    y_pred = []
    confidences = []

    for text in df["raw_text"]:
        c_text = clean_text(text, redact_pii=True)
        lang, conf, _ = detect_language(c_text)
        y_pred.append(lang)
        confidences.append(conf)

    labels = sorted(list(set(y_true).union(set(y_pred))))
    cls_report_dict = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    cls_report_str = classification_report(y_true, y_pred, labels=labels, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))

    print(cls_report_str)
    print(f"Overall Accuracy: {acc:.4f} ({acc:.1%})")
    print(f"Macro-F1:         {macro_f1:.4f}")

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "labels": labels,
        "confusion_matrix": cm,
        "classification_report": cls_report_dict,
        "mean_confidence": float(np.mean(confidences))
    }


def evaluate_absa(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates Aspect-Based Sentiment Analysis against aspect_sentiment JSON ground truth.
    """
    print("\n" + "=" * 60)
    print("2. EVALUATING ASPECT-BASED SENTIMENT ANALYSIS (ABSA)")
    print("=" * 60)

    analyzer = AspectSentimentAnalyzer()

    matched_true = []
    matched_pred = []

    all_gt_true = []
    all_gt_pred = []

    topic_specific: Dict[str, Dict[str, list]] = {}
    doc_true = df["overall_sentiment"].astype(str).tolist()
    doc_pred = []

    for _, row in df.iterrows():
        c_text = clean_text(row["raw_text"], redact_pii=True)
        gt_aspects = json.loads(row["aspect_sentiment"])
        ov_label, _, pred_aspect_list = analyzer.analyze_aspects(c_text, primary_topic=row["primary_topic"])
        doc_pred.append(ov_label)

        pred_dict = {a["topic_code"]: a["sentiment_label"] for a in pred_aspect_list}

        for topic, true_sent in gt_aspects.items():
            all_gt_true.append(true_sent)
            pred_sent = pred_dict.get(topic, "unassigned")
            all_gt_pred.append(pred_sent)

            if topic not in topic_specific:
                topic_specific[topic] = {"true": [], "pred": []}
            topic_specific[topic]["true"].append(true_sent)
            topic_specific[topic]["pred"].append(pred_sent)

            if topic in pred_dict:
                matched_true.append(true_sent)
                matched_pred.append(pred_dict[topic])

    # Metrics on aspects where topic was predicted
    matched_labels = ["negative", "neutral", "positive"]
    matched_report_dict = classification_report(matched_true, matched_pred, labels=matched_labels, output_dict=True, zero_division=0)
    matched_acc = float(accuracy_score(matched_true, matched_pred))
    matched_macro_f1 = float(f1_score(matched_true, matched_pred, average="macro", zero_division=0))

    # Metrics on all ground truth aspect occurrences
    all_labels = ["negative", "neutral", "positive", "unassigned"]
    all_report_dict = classification_report(all_gt_true, all_gt_pred, labels=all_labels, output_dict=True, zero_division=0)
    all_acc = float(accuracy_score(all_gt_true, all_gt_pred))
    all_macro_f1 = float(f1_score(all_gt_true, all_gt_pred, average="macro", zero_division=0))

    # Per-topic summary
    topic_summary = {}
    for topic, data in sorted(topic_specific.items()):
        t_f1 = float(f1_score(data["true"], data["pred"], average="macro", zero_division=0))
        t_acc = float(accuracy_score(data["true"], data["pred"]))
        topic_summary[topic] = {
            "support": len(data["true"]),
            "accuracy": t_acc,
            "macro_f1": t_f1
        }

    # Document-level overall sentiment metrics
    doc_labels = ["negative", "neutral", "positive"]
    doc_report_dict = classification_report(doc_true, doc_pred, labels=doc_labels, output_dict=True, zero_division=0)
    doc_acc = float(accuracy_score(doc_true, doc_pred))
    doc_macro_f1 = float(f1_score(doc_true, doc_pred, average="macro", zero_division=0))

    print(f"Total Ground-Truth Aspect Occurrences: {len(all_gt_true)}")
    print(f"Matched Aspect Occurrences:           {len(matched_true)} ({len(matched_true)/len(all_gt_true):.1%})")
    print(f"Matched Aspect Accuracy:              {matched_acc:.4f}")
    print(f"Matched Aspect Macro-F1:              {matched_macro_f1:.4f}")
    print(f"All-Aspect Accuracy (with unassigned):{all_acc:.4f}")
    print(f"All-Aspect Macro-F1:                  {all_macro_f1:.4f}")
    print(f"Document-level Overall Accuracy:      {doc_acc:.4f}")
    print(f"Document-level Macro-F1:              {doc_macro_f1:.4f}")

    return {
        "total_aspect_occurrences": len(all_gt_true),
        "matched_aspect_occurrences": len(matched_true),
        "coverage_rate": float(len(matched_true) / len(all_gt_true)),
        "matched_aspects": {
            "accuracy": matched_acc,
            "macro_f1": matched_macro_f1,
            "classification_report": matched_report_dict
        },
        "all_aspects_including_unassigned": {
            "accuracy": all_acc,
            "macro_f1": all_macro_f1,
            "classification_report": all_report_dict
        },
        "per_topic_performance": topic_summary,
        "document_level_sentiment": {
            "accuracy": doc_acc,
            "macro_f1": doc_macro_f1,
            "classification_report": doc_report_dict
        }
    }


def evaluate_outlier_ablation(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs actual threshold ablation sweep for outlier / drift detection against is_emergent_drift.
    """
    print("\n" + "=" * 60)
    print("3. RUNNING OUTLIER NOVELTY THRESHOLD (tau) ABLATION SWEEP")
    print("=" * 60)

    cleaned_texts = [clean_text(t, redact_pii=True) for t in df["raw_text"]]
    y_true = df["is_emergent_drift"].astype(bool).values

    engine = MultilingualTopicEngine(n_topics=6, random_state=42)
    engine.fit(cleaned_texts)
    _, _, outlier_scores = engine.transform(cleaned_texts)
    outlier_scores = np.array(outlier_scores)

    thresholds = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
    sweep_results = []
    best_tau = None
    best_f1 = -1.0

    print(f"{'Threshold (tau)':<16} | {'Precision':<10} | {'Recall':<8} | {'F1-Score':<8} | {'TP':<4} | {'FP':<5} | {'FN':<5}")
    print("-" * 72)

    for tau in thresholds:
        y_pred = outlier_scores >= tau
        p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
        tp = int(np.sum((y_pred == True) & (y_true == True)))
        fp = int(np.sum((y_pred == True) & (y_true == False)))
        fn = int(np.sum((y_pred == False) & (y_true == True)))
        tn = int(np.sum((y_pred == False) & (y_true == False)))

        sweep_results.append({
            "threshold": tau,
            "precision": float(round(p, 4)),
            "recall": float(round(r, 4)),
            "f1_score": float(round(f1, 4)),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn
        })

        if f1 > best_f1:
            best_f1 = f1
            best_tau = tau

        print(f"tau = {tau:<10.2f} | {p:<10.4f} | {r:<8.4f} | {f1:<8.4f} | {tp:<4} | {fp:<5} | {fn:<5}")

    print(f"\nEmpirical Optimal Operating Point: tau = {best_tau:.2f} (F1 = {best_f1:.4f})")

    return {
        "sweep": sweep_results,
        "optimal_threshold": best_tau,
        "optimal_f1": float(round(best_f1, 4)),
        "total_samples": len(df),
        "total_drift_positives": int(y_true.sum())
    }


def evaluate_topic_coherence(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes topic coherence comparison: Baseline LDA vs Advanced Multilingual Engine.
    """
    print("\n" + "=" * 60)
    print("4. EVALUATING TOPIC COHERENCE (NPMI)")
    print("=" * 60)

    cleaned_texts = [clean_text(t, redact_pii=True) for t in df["raw_text"]]

    # Baseline LDA
    lda = BaselineLDAModel(n_topics=6, random_state=42)
    lda.fit(cleaned_texts)
    lda_keywords = lda.get_topic_keywords(top_n=8)
    lda_coherence = compute_topic_coherence(lda_keywords, cleaned_texts)

    # Advanced Multilingual Engine
    adv = MultilingualTopicEngine(n_topics=6, random_state=42)
    adv.fit(cleaned_texts)
    adv_keywords = adv.get_topic_keywords()
    adv_coherence = compute_topic_coherence(adv_keywords, cleaned_texts)

    lda_mean = float(lda_coherence["mean_coherence"])
    adv_mean = float(adv_coherence["mean_coherence"])
    delta = float(adv_mean - lda_mean)

    print(f"Baseline LDA Mean Coherence:        {lda_mean:+.4f}")
    print(f"Advanced Multilingual Engine Mean:  {adv_mean:+.4f}")
    print(f"Net Coherence Gain:                 {delta:+.4f}")

    return {
        "baseline_lda": {
            "mean_coherence": lda_mean,
            "per_topic_coherence": {str(k): float(v) for k, v in lda_coherence["per_topic_coherence"].items()},
            "topic_keywords": {str(k): v for k, v in lda_keywords.items()}
        },
        "advanced_multilingual_engine": {
            "mean_coherence": adv_mean,
            "per_topic_coherence": {str(k): float(v) for k, v in adv_coherence["per_topic_coherence"].items()},
            "topic_keywords": {str(k): v for k, v in adv_keywords.items()}
        },
        "coherence_gain": delta
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Multilingual Course Feedback Intelligence System")
    parser.add_argument("--input-file", default="data/raw/synthetic_feedback_1000.csv", help="Input dataset path")
    parser.add_argument("--output-json", default="evaluation_results.json", help="Path to persist results JSON")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f"Input file not found at {args.input_file}")

    print("=" * 70)
    print("STARTING VERIFIED GROUND-TRUTH SYSTEM EVALUATION")
    print(f"Input File:  {args.input_file}")
    print(f"Output JSON: {args.output_json}")
    print("=" * 70)

    df = pd.read_csv(args.input_file)
    print(f"Loaded {len(df)} records from {args.input_file}.")

    lid_results = evaluate_language_id(df)
    absa_results = evaluate_absa(df)
    ablation_results = evaluate_outlier_ablation(df)
    coherence_results = evaluate_topic_coherence(df)

    results = {
        "metadata": {
            "dataset": args.input_file,
            "sample_count": len(df),
            "random_state": 42
        },
        "language_identification": lid_results,
        "aspect_based_sentiment_analysis": absa_results,
        "outlier_threshold_ablation": ablation_results,
        "topic_coherence": coherence_results
    }

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"ALL EVALUATIONS COMPLETE. Saved results to {args.output_json}")
    print("=" * 70)


if __name__ == "__main__":
    main()

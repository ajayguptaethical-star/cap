"""
Unit tests for Deliverable 5: Dataset Package Integrity & Leakage Verification.
"""

import json
import pytest
import pandas as pd

EXPECTED_COLUMNS = [
    "comment_id",
    "timestamp",
    "academic_term",
    "course_code",
    "instructor_id",
    "raw_text",
    "true_language",
    "script_type",
    "primary_topic",
    "secondary_topic",
    "aspect_sentiment",
    "overall_sentiment",
    "is_emergent_drift"
]

VALID_LANGUAGES = {"en", "hi", "mr", "hi-en", "mr-en"}
VALID_SCRIPTS = {"Latin", "Devanagari"}
VALID_SENTIMENTS = {"positive", "negative", "neutral"}
VALID_TERMS = {"Fall 2025", "Spring 2026", "Summer 2026", "Fall 2026"}

def test_raw_dataset_schema_and_size(raw_dataset):
    """Verify raw dataset has exactly 1,000 rows and strictly matches data dictionary columns."""
    assert len(raw_dataset) == 1000, f"Expected 1000 records, got {len(raw_dataset)}"
    for col in EXPECTED_COLUMNS:
        assert col in raw_dataset.columns, f"Missing expected column: {col}"

def test_required_columns_non_null(raw_dataset):
    """Ensure essential operational columns have zero null values."""
    required_cols = [
        "comment_id",
        "timestamp",
        "academic_term",
        "course_code",
        "instructor_id",
        "raw_text",
        "true_language",
        "script_type",
        "primary_topic",
        "aspect_sentiment",
        "overall_sentiment",
        "is_emergent_drift"
    ]
    for col in required_cols:
        null_count = raw_dataset[col].isnull().sum()
        assert null_count == 0, f"Column '{col}' has {null_count} null values"

def test_value_domain_constraints(raw_dataset):
    """Verify categorical columns only contain values within specified allowed sets."""
    assert set(raw_dataset["true_language"].unique()).issubset(VALID_LANGUAGES)
    assert set(raw_dataset["script_type"].unique()).issubset(VALID_SCRIPTS)
    assert set(raw_dataset["overall_sentiment"].unique()).issubset(VALID_SENTIMENTS)
    assert set(raw_dataset["academic_term"].unique()).issubset(VALID_TERMS)

def test_aspect_sentiment_json_parsing(raw_dataset):
    """Ensure aspect_sentiment column contains well-formed JSON matching valid topics and sentiments."""
    sample_rows = raw_dataset.sample(50, random_state=42)
    for _, row in sample_rows.iterrows():
        aspect_dict = json.loads(row["aspect_sentiment"])
        assert isinstance(aspect_dict, dict)
        assert len(aspect_dict) >= 1
        for topic, sent in aspect_dict.items():
            assert topic.startswith("TOPIC_") or topic.startswith("DRIFT_")
            assert sent in VALID_SENTIMENTS

def test_zero_leakage_between_splits(train_dataset, val_dataset, test_dataset):
    """Quality Bar: Prove mathematically that train, validation, and test splits have ZERO ID overlap."""
    train_ids = set(train_dataset["comment_id"])
    val_ids = set(val_dataset["comment_id"])
    test_ids = set(test_dataset["comment_id"])

    assert len(train_ids.intersection(val_ids)) == 0, "Data leakage found between train and validation sets!"
    assert len(train_ids.intersection(test_ids)) == 0, "Data leakage found between train and test sets!"
    assert len(val_ids.intersection(test_ids)) == 0, "Data leakage found between validation and test sets!"

def test_split_proportions(train_dataset, val_dataset, test_dataset, raw_dataset):
    """Verify train is ~70%, val is ~15%, and test is ~15%."""
    total = len(raw_dataset)
    assert len(train_dataset) == 700
    assert len(val_dataset) == 150
    assert len(test_dataset) == 150
    assert len(train_dataset) + len(val_dataset) + len(test_dataset) == total

def test_multilingual_representation_in_splits(train_dataset, val_dataset, test_dataset):
    """Verify that every language is represented in all three splits."""
    for split_name, df in [("train", train_dataset), ("val", val_dataset), ("test", test_dataset)]:
        present_langs = set(df["true_language"].unique())
        assert present_langs == VALID_LANGUAGES, f"Missing languages in {split_name} split: {VALID_LANGUAGES - present_langs}"

def test_temporal_drift_seeding(raw_dataset):
    """Verify emergent drift topics are absent from Terms 1 and 2, but present in Terms 3 and 4."""
    term1_drift = raw_dataset[raw_dataset["academic_term"] == "Fall 2025"]["is_emergent_drift"].sum()
    term2_drift = raw_dataset[raw_dataset["academic_term"] == "Spring 2026"]["is_emergent_drift"].sum()
    term3_drift = raw_dataset[raw_dataset["academic_term"] == "Summer 2026"]["is_emergent_drift"].sum()
    term4_drift = raw_dataset[raw_dataset["academic_term"] == "Fall 2026"]["is_emergent_drift"].sum()

    assert term1_drift == 0, f"Term 1 should have zero drift, got {term1_drift}"
    assert term2_drift == 0, f"Term 2 should have zero drift, got {term2_drift}"
    assert term3_drift > 0, "Term 3 must contain seeded drift comments"
    assert term4_drift > 0, "Term 4 must contain seeded drift comments"

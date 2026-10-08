"""
Topic Drift and Emerging Signal Metrics API Router.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.repository import DriftRepository, FeedbackRepository
from src.innovation.drift_detector import AdvancedDriftDetector
from src.api.schemas import DriftCandidateResponse

router = APIRouter(prefix="/drift", tags=["Topic Drift & Emerging Signals"])
drift_detector = AdvancedDriftDetector()

@router.get("/metrics")
def get_drift_metrics(
    ref_term: str = Query("Fall 2025", description="Baseline semester"),
    curr_term: str = Query("Fall 2026", description="Comparison semester"),
    db: Session = Depends(get_db)
):
    """
    Computes Population Stability Index (PSI) and distribution shift
    between a reference academic semester and the current evaluation cohort.
    """
    feedback_repo = FeedbackRepository(db)
    
    # Query topic distributions for both terms
    ref_records = feedback_repo.query_feedback(academic_term=ref_term, limit=1000)
    curr_records = feedback_repo.query_feedback(academic_term=curr_term, limit=1000)

    def calc_proportions(records):
        counts = {}
        for r in records:
            counts[r.primary_topic_code] = counts.get(r.primary_topic_code, 0) + 1
        total = len(records) if records else 1
        return {k: v / total for k, v in counts.items()}

    ref_props = calc_proportions(ref_records)
    curr_props = calc_proportions(curr_records)

    psi_result = drift_detector.compute_psi(ref_props, curr_props)
    
    # Outlier counts
    curr_outliers = sum(1 for r in curr_records if r.is_outlier)
    ref_outliers = sum(1 for r in ref_records if r.is_outlier)

    return {
        "reference_term": ref_term,
        "current_term": curr_term,
        "ref_sample_size": len(ref_records),
        "curr_sample_size": len(curr_records),
        "ref_outlier_count": ref_outliers,
        "curr_outlier_count": curr_outliers,
        "psi": psi_result["psi"],
        "status": psi_result["status"],
        "is_drift_alert": psi_result.get("is_alert", False),
        "topic_contributions": psi_result.get("details", {})
    }

@router.get("/pending", response_model=List[DriftCandidateResponse])
def get_pending_drift_candidates(db: Session = Depends(get_db)):
    """Returns candidate emerging topics currently awaiting human committee review."""
    drift_repo = DriftRepository(db)
    candidates = drift_repo.get_pending_candidates()
    return candidates

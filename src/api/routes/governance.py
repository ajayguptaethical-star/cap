"""
Human-in-the-Loop (HITL) Governance and Rollback API Router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.innovation.governance import GovernanceManager
from src.api.schemas import (
    GovernanceActionRequest,
    RollbackRequest,
    TopicVersionResponse,
    DriftCandidateResponse
)

router = APIRouter(prefix="/governance", tags=["HITL Governance & Rollback"])

@router.post("/approve", response_model=TopicVersionResponse, status_code=status.HTTP_200_OK)
def approve_candidate_topic(
    payload: GovernanceActionRequest,
    db: Session = Depends(get_db)
):
    """
    Committee Approval Gate:
    Promotes a pending emerging topic candidate to official active status,
    increments topic model version (v1.0.0 -> v1.1.0), and creates an immutable snapshot.
    """
    gov = GovernanceManager(db)
    try:
        new_version = gov.approve_candidate(
            candidate_id=payload.candidate_id,
            approved_name=payload.approved_name,
            admin_notes=payload.admin_notes,
            reviewed_by=payload.reviewed_by
        )
        return new_version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/merge", response_model=DriftCandidateResponse, status_code=status.HTTP_200_OK)
def merge_candidate_topic(
    payload: GovernanceActionRequest,
    db: Session = Depends(get_db)
):
    """Folds an emerging candidate cluster into an existing official topic."""
    if not payload.merge_into_topic_code:
        raise HTTPException(status_code=400, detail="merge_into_topic_code is required for MERGE action.")

    gov = GovernanceManager(db)
    try:
        updated = gov.merge_candidate(
            candidate_id=payload.candidate_id,
            merge_into_topic_code=payload.merge_into_topic_code,
            admin_notes=payload.admin_notes,
            reviewed_by=payload.reviewed_by
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/discard", response_model=DriftCandidateResponse, status_code=status.HTTP_200_OK)
def discard_candidate_topic(
    payload: GovernanceActionRequest,
    db: Session = Depends(get_db)
):
    """Rejects and discards an outlier cluster as noise/spam."""
    gov = GovernanceManager(db)
    try:
        discarded = gov.discard_candidate(
            candidate_id=payload.candidate_id,
            admin_notes=payload.admin_notes,
            reviewed_by=payload.reviewed_by
        )
        return discarded
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rollback", response_model=TopicVersionResponse, status_code=status.HTTP_200_OK)
def rollback_topic_version(
    payload: RollbackRequest,
    db: Session = Depends(get_db)
):
    """
    1-Click Emergency Rollback:
    Restores the active topic model to a historical version snapshot (e.g. v1.0.0)
    to recover from semantic degradation without downtime.
    """
    gov = GovernanceManager(db)
    try:
        restored = gov.rollback_to_version(
            target_version_tag=payload.target_version_tag,
            admin_notes=payload.admin_notes,
            reviewed_by=payload.reviewed_by
        )
        return restored
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

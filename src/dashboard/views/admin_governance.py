"""
View 4: HITL Drift Governance Cockpit.
Provides an administrative control interface for reviewing staged drift candidates,
approving/merging/discarding new topic proposals, and executing 1-click model version rollbacks.
"""

import json
import streamlit as st
import pandas as pd

from src.database.connection import SessionLocal
from src.database.repository import TopicRepository, DriftRepository
from src.database.models import DriftCandidateModel
from src.innovation.governance import GovernanceManager
from src.dashboard.utils import render_badge

def render_admin_governance():
    st.markdown("## 🛡️ HITL Topic Drift Governance Cockpit")
    st.markdown("Institutional audit surface ensuring supervised control over emerging feedback topics, snapshot versioning, and instant rollbacks.")

    db = SessionLocal()
    try:
        topic_repo = TopicRepository(db)
        drift_repo = DriftRepository(db)
        gov_manager = GovernanceManager(db)

        active_version = topic_repo.get_active_version()
        all_versions = topic_repo.get_all_versions()
        pending_candidates = drift_repo.get_pending_candidates()

        # Active Version Header Card
        ver_tag = active_version.version_tag if active_version else "v1.0.0"
        active_topics = topic_repo.get_active_topics()
        num_topics = len(active_topics)
        num_emergent = len([t for t in active_topics if t.is_emergent])

        st.markdown(
            f"""
            <div style="background-color: #1E293B; padding: 18px; border-radius: 12px; margin-bottom: 24px; border: 1px solid #334155;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: #F8FAFC;">Active Model Version: <span style="color: #6366F1;">{ver_tag}</span></h4>
                        <div style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">
                            Created by: <b>{active_version.created_by if active_version else 'system'}</b> | 
                            Active Topics: <b>{num_topics}</b> ({num_emergent} Emergent)
                        </div>
                    </div>
                    <div>
                        {render_badge("SYSTEM SECURED", "positive")}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Tabs for Pending Candidates, Version Snapshotting & Rollback, Audit Log
        tab_candidates, tab_rollback, tab_audit = st.tabs([
            f"📥 Staged Drift Candidates ({len(pending_candidates)})",
            "⏪ Model Version Snapshots & 1-Click Rollback",
            "📜 Governance Audit Trail"
        ])

        with tab_candidates:
            st.subheader("Staged Novelty Clusters Awaiting Academic Committee Action")
            if not pending_candidates:
                st.info("No candidate topics are currently awaiting review. Outlier streams are fully classified.")
            else:
                for cand in pending_candidates:
                    keywords_list = [k.strip() for k in cand.top_keywords.split(",") if k.strip()]
                    kw_badges = " ".join([render_badge(k, "info") for k in keywords_list])

                    st.markdown(
                        f"""
                        <div style="background-color: #0F172A; padding: 16px; border-radius: 10px; border: 1px solid #475569; margin-bottom: 14px;">
                            <div style="display: flex; justify-content: space-between;">
                                <h4 style="margin: 0; color: #F59E0B;">Candidate #{cand.candidate_id}: {cand.proposed_name}</h4>
                                <span>{render_badge(cand.academic_term, 'neutral')}</span>
                            </div>
                            <p style="color: #CBD5E1; margin: 8px 0; font-size: 0.9rem;">
                                <b>Sample Size:</b> {cand.sample_size} comments | 
                                <b>Topic Coherence (NPMI):</b> {cand.coherence_score:.4f}
                            </p>
                            <div style="margin: 6px 0;"><b>Extracted Keywords:</b> {kw_badges}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    col_act1, col_act2, col_act3 = st.columns(3)
                    with col_act1:
                        with st.popover(f"✅ Approve as Topic #{cand.candidate_id}"):
                            app_name = st.text_input("Official Catalog Name", value=cand.proposed_name, key=f"app_name_{cand.candidate_id}")
                            app_notes = st.text_input("Reviewer Notes", value="Approved by curriculum review committee", key=f"app_notes_{cand.candidate_id}")
                            reviewer = st.text_input("Admin ID", value="dr_sharma", key=f"app_rev_{cand.candidate_id}")
                            if st.button("Confirm Approval & Increment Version", key=f"btn_app_{cand.candidate_id}", type="primary"):
                                try:
                                    new_ver = gov_manager.approve_candidate(
                                        candidate_id=cand.candidate_id,
                                        approved_name=app_name,
                                        admin_notes=app_notes,
                                        reviewed_by=reviewer
                                    )
                                    st.success(f"Candidate #{cand.candidate_id} approved! Created version {new_ver.version_tag}.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Approval failed: {e}")

                    with col_act2:
                        with st.popover(f"🔄 Merge #{cand.candidate_id}"):
                            target_topic = st.selectbox(
                                "Merge into existing topic:",
                                options=[t.topic_code for t in active_topics],
                                format_func=lambda c: f"{c} - next(t.topic_name for t in active_topics if t.topic_code == c)",
                                key=f"merge_target_{cand.candidate_id}"
                            )
                            merge_notes = st.text_input("Merge Rationale", value="Subsumed into existing curriculum theme", key=f"merge_notes_{cand.candidate_id}")
                            if st.button("Confirm Merge", key=f"btn_merge_{cand.candidate_id}"):
                                try:
                                    gov_manager.merge_candidate(
                                        candidate_id=cand.candidate_id,
                                        merge_into_topic_code=target_topic,
                                        admin_notes=merge_notes
                                    )
                                    st.success(f"Candidate #{cand.candidate_id} merged into {target_topic}.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Merge failed: {e}")

                    with col_act3:
                        with st.popover(f"🗑️ Discard #{cand.candidate_id}"):
                            discard_notes = st.text_input("Discard Reason", value="Flagged as spam or unaligned noise", key=f"discard_notes_{cand.candidate_id}")
                            if st.button("Confirm Discard", key=f"btn_discard_{cand.candidate_id}", type="secondary"):
                                try:
                                    gov_manager.discard_candidate(
                                        candidate_id=cand.candidate_id,
                                        admin_notes=discard_notes
                                    )
                                    st.warning(f"Candidate #{cand.candidate_id} discarded.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Discard failed: {e}")

        with tab_rollback:
            st.subheader("Immutable Model Version Snapshots")
            st.markdown("Every committee approval creates an immutable version snapshot. If model degradation occurs, roll back instantly:")

            if all_versions:
                ver_rows = []
                for v in all_versions:
                    ver_rows.append({
                        "Version Tag": v.version_tag,
                        "Status": v.status,
                        "Created At": v.created_at.strftime("%Y-%m-%d %H:%M:%S") if v.created_at else "N/A",
                        "Created By": v.created_by
                    })
                st.dataframe(pd.DataFrame(ver_rows), use_container_width=True, hide_index=True)

                st.markdown("### ⏪ 1-Click Rollback Console")
                col_rb_select, col_rb_btn = st.columns([3, 1])
                archived_versions = [v.version_tag for v in all_versions if v.status != "ACTIVE"]

                if archived_versions:
                    with col_rb_select:
                        target_rb = st.selectbox("Select Target Version to Restore:", archived_versions)
                    with col_rb_btn:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("🚨 Execute Instant Rollback", type="primary"):
                            try:
                                restored = gov_manager.rollback_to_version(
                                    target_version_tag=target_rb,
                                    admin_notes=f"Emergency rollback to {target_rb}"
                                )
                                st.success(f"Rollback successful! Active version is now {restored.version_tag}.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Rollback failed: {e}")
                else:
                    st.info("No archived historical versions available for rollback yet (only initial baseline active).")

        with tab_audit:
            st.subheader("Administrative Decision Audit Trail")
            all_cand = db.query(DriftCandidateModel).order_by(DriftCandidateModel.detected_at.desc()).all()
            if all_cand:
                audit_rows = []
                for c in all_cand:
                    audit_rows.append({
                        "Candidate ID": c.candidate_id,
                        "Term": c.academic_term,
                        "Proposed Name": c.proposed_name,
                        "Status": c.status,
                        "Reviewed By": c.reviewed_by or "Pending",
                        "Reviewed At": c.reviewed_at.strftime("%Y-%m-%d %H:%M") if c.reviewed_at else "Pending",
                        "Notes": c.review_notes or "—"
                    })
                st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No candidates in audit history.")

    finally:
        db.close()

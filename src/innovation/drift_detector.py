"""
Topic Drift and Novelty Detection Engine.
Computes pointwise outlier novelty scores, Population Stability Index (PSI),
and compares against a classical sliding-window vocabulary divergence baseline.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy.spatial.distance import cosine
from scipy.stats import wasserstein_distance
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from src.config import settings

class BaselineVocabularyDivergence:
    """
    Classical Baseline: Naive Rolling-Window Vocabulary Divergence.
    Measures distribution shift by tracking the Jaccard distance and Cosine divergence
    of raw word frequency distributions between consecutive time windows (without semantic embeddings).
    """
    def __init__(self, top_k: int = 100):
        self.top_k = top_k
        self.vectorizer = CountVectorizer(
            max_features=top_k,
            token_pattern=r"(?u)\b[\w\u0900-\u097F\-]{2,}\b"
        )

    def compute_divergence(self, ref_texts: List[str], curr_texts: List[str]) -> Dict[str, float]:
        """
        Computes Jaccard distance and Cosine divergence between two text collections.
        """
        if not ref_texts or not curr_texts:
            return {"jaccard_distance": 0.0, "cosine_divergence": 0.0}

        # Fit on combined corpus to get shared vocabulary
        combined = ref_texts + curr_texts
        self.vectorizer.fit(combined)

        ref_counts = np.asarray(self.vectorizer.transform(ref_texts).sum(axis=0)).flatten()
        curr_counts = np.asarray(self.vectorizer.transform(curr_texts).sum(axis=0)).flatten()

        # Normalize to probability distributions
        ref_norm = ref_counts / (np.sum(ref_counts) if np.sum(ref_counts) > 0 else 1.0)
        curr_norm = curr_counts / (np.sum(curr_counts) if np.sum(curr_counts) > 0 else 1.0)

        # Cosine divergence: 1.0 - cosine_similarity
        cos_sim = float(np.dot(ref_norm, curr_norm) / (np.linalg.norm(ref_norm) * np.linalg.norm(curr_norm) + 1e-12))
        cos_div = float(1.0 - max(0.0, min(1.0, cos_sim)))

        # Jaccard distance on non-zero vocabulary sets
        ref_vocab = set(np.where(ref_counts > 0)[0])
        curr_vocab = set(np.where(curr_counts > 0)[0])
        intersection = len(ref_vocab.intersection(curr_vocab))
        union = len(ref_vocab.union(curr_vocab))
        jaccard_dist = float(1.0 - (intersection / union if union > 0 else 1.0))

        return {
            "jaccard_distance": round(jaccard_dist, 4),
            "cosine_divergence": round(cos_div, 4)
        }


class AdvancedDriftDetector:
    """
    Innovation Layer: Semantic Outlier Novelty & Temporal Drift Engine.
    Combines dense distance-to-centroid thresholding, Population Stability Index (PSI),
    and Wasserstein Earth Mover's Distance to reliably detect emergent topics and distribution shifts.
    """
    def __init__(
        self,
        outlier_threshold: float = settings.OUTLIER_THRESHOLD,
        psi_threshold: float = settings.POPULATION_STABILITY_INDEX_THRESHOLD
    ):
        self.outlier_threshold = outlier_threshold
        self.psi_threshold = psi_threshold

    def score_outliers(
        self,
        embeddings: np.ndarray,
        cluster_centroids: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes pointwise novelty / outlier scores:
        d_i = 1.0 - max_k cos(e_i, c_k)
        Returns:
          - outlier_scores: array of float scores in [0.0, 1.0]
          - is_outlier: boolean mask where outlier_score >= outlier_threshold
        """
        sim_matrix = cosine_similarity(embeddings, cluster_centroids)
        max_sims = np.max(sim_matrix, axis=1)
        # Novelty is distance from the closest cluster
        outlier_scores = np.clip(1.0 - max_sims, 0.0, 1.0)
        is_outlier = outlier_scores >= self.outlier_threshold
        return outlier_scores, is_outlier

    def compute_psi(
        self,
        ref_proportions: Dict[str, float],
        curr_proportions: Dict[str, float],
        eps: float = 1e-4
    ) -> Dict[str, Any]:
        """
        Computes Population Stability Index (PSI):
        PSI = sum_k (P_curr(k) - P_ref(k)) * ln((P_curr(k) + eps) / (P_ref(k) + eps))
        
        Interpretation Thresholds:
          - PSI < 0.10: Stable (No shift)
          - 0.10 <= PSI < 0.25: Moderate shift (Warning)
          - PSI >= 0.25: Significant structural shift (Alert)
        """
        all_topics = sorted(set(ref_proportions.keys()).union(set(curr_proportions.keys())))
        if not all_topics:
            return {"psi": 0.0, "status": "STABLE", "is_alert": False, "details": {}}

        psi_val = 0.0
        details = {}

        for topic in all_topics:
            p_ref = max(ref_proportions.get(topic, 0.0), eps)
            p_curr = max(curr_proportions.get(topic, 0.0), eps)
            delta = p_curr - p_ref
            ratio = np.log(p_curr / p_ref)
            contribution = float(delta * ratio)
            psi_val += contribution
            details[topic] = {
                "ref_prop": round(p_ref, 4),
                "curr_prop": round(p_curr, 4),
                "contribution": round(contribution, 4)
            }

        psi_val = max(0.0, float(psi_val))

        if psi_val < 0.10:
            status = "STABLE"
        elif psi_val < 0.25:
            status = "MODERATE_SHIFT"
        else:
            status = "SIGNIFICANT_DRIFT"

        return {
            "psi": round(psi_val, 4),
            "status": status,
            "is_alert": psi_val >= self.psi_threshold,
            "details": details
        }

    def compute_wasserstein_drift(
        self,
        ref_topic_counts: List[int],
        curr_topic_counts: List[int]
    ) -> float:
        """
        Computes Earth Mover's Distance (Wasserstein-1) between normalized topic histograms.
        """
        p_ref = np.array(ref_topic_counts, dtype=float)
        p_curr = np.array(curr_topic_counts, dtype=float)

        p_ref = p_ref / (np.sum(p_ref) if np.sum(p_ref) > 0 else 1.0)
        p_curr = p_curr / (np.sum(p_curr) if np.sum(p_curr) > 0 else 1.0)

        return float(wasserstein_distance(p_ref, p_curr))


def calculate_psi(p_vec: np.ndarray, q_vec: np.ndarray, eps: float = 1e-4) -> float:
    """
    Computes Population Stability Index (PSI) directly on two probability vectors:
    PSI = sum((q_i - p_i) * ln(q_i / p_i))
    """
    p = np.asarray(p_vec, dtype=float)
    q = np.asarray(q_vec, dtype=float)
    
    # Smooth with epsilon
    p_smooth = (p + eps) / (np.sum(p) + eps * len(p))
    q_smooth = (q + eps) / (np.sum(q) + eps * len(q))
    
    psi_val = np.sum((q_smooth - p_smooth) * np.log(q_smooth / p_smooth))
    return float(max(0.0, psi_val))


def compute_outlier_score(topic_prob: float, base_threshold: float = 0.55) -> float:
    """
    Computes an outlier novelty score based on model prediction confidence:
    novelty = 1.0 - confidence. Higher means higher novelty/drift.
    """
    return float(np.clip(1.0 - topic_prob, 0.0, 1.0))

"""
Emerging Clusterer Engine.
Aggregates outlier feedback comments, clusters them to discover emerging themes,
extracts candidate keywords via c-TF-IDF, and computes cluster coherence.
"""

import hashlib
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from src.topic_modeling.c_tfidf import ClassTFIDF
from src.topic_modeling.coherence import compute_topic_coherence

class EmergingTopicClusterer:
    """
    Discovers candidate emerging topics from an accumulated pool of outlier feedback.
    Applies density-based clustering, c-TF-IDF keyword extraction, and coherence filtering.
    """
    def __init__(
        self,
        min_cluster_size: int = 8,
        min_coherence: float = 0.20
    ):
        self.min_cluster_size = min_cluster_size
        self.min_coherence = min_coherence
        self.ctfidf = ClassTFIDF(top_n=8, min_df=1)

    def discover_candidates(
        self,
        outlier_texts: List[str],
        outlier_embeddings: np.ndarray,
        academic_term: str = "Summer 2026"
    ) -> List[Dict[str, Any]]:
        """
        Groups outlier feedback into candidate emerging topics.
        Returns a list of structured candidate dictionaries for human review.
        """
        n_samples = len(outlier_texts)
        if n_samples < self.min_cluster_size:
            return []

        # Determine number of clusters based on outlier volume (e.g., 1 to 3 candidate themes)
        n_clusters = max(1, min(3, n_samples // self.min_cluster_size))

        if n_clusters == 1:
            cluster_labels = np.zeros(n_samples, dtype=int)
        else:
            clusterer = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric="cosine",
                linkage="average"
            )
            cluster_labels = clusterer.fit_predict(outlier_embeddings)

        # Extract c-TF-IDF keywords per candidate cluster
        keywords_dict = self.ctfidf.fit_transform(outlier_texts, cluster_labels.tolist())

        candidates = []
        for cluster_id, kws in keywords_dict.items():
            cluster_mask = cluster_labels == cluster_id
            cluster_size = int(np.sum(cluster_mask))

            if cluster_size < self.min_cluster_size:
                continue

            cluster_docs = [outlier_texts[i] for i in range(n_samples) if cluster_mask[i]]
            
            # Compute coherence of candidate cluster
            coherence_res = compute_topic_coherence({0: kws}, cluster_docs, top_n=6)
            cluster_coherence = coherence_res["mean_coherence"]

            # Filter out incoherent noise
            if cluster_coherence < self.min_coherence and cluster_size < 15:
                continue

            # Generate proposed title from top 3 keywords
            clean_kws = [w for w in kws if len(w) > 2][:3]
            proposed_name = "_".join(clean_kws) if clean_kws else f"emerging_theme_{cluster_id+1}"

            # Compute unique deterministic cluster hash
            combined_sig = f"{academic_term}:{','.join(kws[:5])}:{cluster_size}"
            cluster_hash = hashlib.sha256(combined_sig.encode("utf-8")).hexdigest()

            candidates.append({
                "cluster_hash": cluster_hash,
                "academic_term": academic_term,
                "proposed_name": proposed_name,
                "top_keywords": ", ".join(kws),
                "sample_size": cluster_size,
                "coherence_score": round(float(cluster_coherence), 4),
                "exemplar_texts": cluster_docs[:3]
            })

        return candidates

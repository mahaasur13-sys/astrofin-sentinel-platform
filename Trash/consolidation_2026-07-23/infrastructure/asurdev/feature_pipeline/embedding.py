#!/usr/bin/env python3
"""
Node Embedding Layer — vector representations of nodes.
Used for: similarity clustering, anomaly detection, affinity-based scheduling.
"""
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from .schemas import NodeProfile, NodeRole

# =============================================================================
# EMBEDDING BUILDER
# =============================================================================

class NodeEmbeddingBuilder:
    """
    Builds fixed-size embedding vectors for cluster nodes.
    Combines: hardware profile + failure history + workload pattern.
    """

    def __init__(self):
        self.embedding_dim: int = 16

    def build_from_profile(self, profile: NodeProfile) -> np.ndarray:
        """
        Build embedding from hardware + historical profile.
        Produces a 16-dimensional vector.
        """
        hw_vec = profile.to_embedding_vector()  # 8 dims

        # Derived features
        failure_score = min(profile.historical_failure_rate / 10.0, 1.0)  # normalized
        latency_score = profile.avg_latency_ms / 1000.0  # normalized to seconds
        volatility_score = min(profile.queue_volatility / 10.0, 1.0)

        # Role encoding (one-hot, 5 dims)
        role_map = {NodeRole.GPU: 0, NodeRole.CPU: 1, NodeRole.ARM: 2, NodeRole.VPS: 3, NodeRole.UNKNOWN: 4}
        role_onehot = [0.0] * 5
        role_idx = role_map.get(profile.role, 4)
        role_onehot[role_idx] = 1.0

        # Composite scores (3 dims)
        composite = [
            failure_score,
            latency_score,
            volatility_score,
        ]

        # Pad to embedding_dim
        full_vec = hw_vec + role_onehot + composite
        full_vec = full_vec[:self.embedding_dim]  # truncate if needed
        while len(full_vec) < self.embedding_dim:
            full_vec.append(0.0)

        return np.array(full_vec, dtype=np.float32)

    def build_from_features(self, features: Dict[str, float]) -> np.ndarray:
        """
        Build embedding from a feature vector (24h aggregates).
        Maps raw features → condensed 16-dim representation.
        """
        vec = np.zeros(self.embedding_dim, dtype=np.float32)

        # Key features mapping (order matters)
        key_features = [
            "gpu_mean_5m", "gpu_std_5m", "gpu_slope_15m",
            "cpu_mean_5m", "mem_mean_5m",
            "queue_mean_5m", "queue_derivative_5m",
            "failure_count_1h", "failure_count_24h",
            "consecutive_failures",
            "overload_score", "health_score",
            "queue_volatility_5m",
            "ceph_util_mean_5m", "wg_latency_mean_1m",
        ]

        for i, feat_name in enumerate(key_features):
            if i >= self.embedding_dim:
                break
            vec[i] = features.get(feat_name, 0.0) / 100.0  # normalize to [0,1]

        return vec

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two embedding vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def find_similar_nodes(
        self,
        target_embedding: np.ndarray,
        all_embeddings: Dict[str, np.ndarray],
        top_k: int = 3
    ) -> List[tuple]:
        """
        Find top-k most similar nodes to target_embedding.
        Returns list of (node_id, similarity_score).
        """
        similarities = []
        for node_id, emb in all_embeddings.items():
            sim = self.cosine_similarity(target_embedding, emb)
            similarities.append((node_id, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def cluster_nodes(
        self,
        embeddings: Dict[str, np.ndarray],
        n_clusters: int = 3
    ) -> Dict[int, List[str]]:
        """
        Simple K-means clustering of nodes by embedding similarity.
        Returns {cluster_id: [node_ids]}.
        """
        try:
            from sklearn.cluster import KMeans
        except ImportError:
            return {0: list(embeddings.keys())}  # fallback: single cluster

        node_ids = list(embeddings.keys())
        X = np.array([embeddings[nid] for nid in node_ids])
        kmeans = KMeans(n_clusters=min(n_clusters, len(node_ids)), random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        result: Dict[int, List[str]] = {}
        for node_id, label in zip(node_ids, labels):
            result.setdefault(int(label), []).append(node_id)
        return result

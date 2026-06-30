#!/usr/bin/env python3
"""
Beam Pruner — K-best pruning to prevent candidate explosion.
Reduces O(N×M) to O(K×M) where K = beam_width.
"""
from typing import Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class PrunedCandidate:
    job_id: str
    node_id: str
    score: float
    ml_risk: float
    variance: float       # for regret-aware scoring
    prune_reason: str = ""


class BeamPruner:
    """
    Prunes candidate space using beam search with variance estimation.
    score = E[U] - lambda * sqrt(variance)   (regret-aware)
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.beam_width = self.config.get("beam_width", 10)
        self.regret_lambda = self.config.get("regret_lambda", 1.5)
        self._node_variance: dict[str, float] = {}

    def load_variance_from_tsd(self, node_id: str, var: float) -> None:
        self._node_variance[node_id] = var

    def prune(self, candidates: list, top_k: Optional[int] = None) -> list[PrunedCandidate]:
        k = top_k or self.beam_width
        scored = []
        for c in candidates:
            variance = self._node_variance.get(c.node_id, 0.1)
            regret_score = c.score - self.regret_lambda * np.sqrt(variance)
            scored.append(PrunedCandidate(c.job_id, c.node_id, regret_score, c.ml_risk, variance))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]

    def prune_by_job(self, candidates: list, max_per_job: int = 5) -> list:
        by_job = {}
        for c in candidates:
            by_job.setdefault(c.job_id, []).append(c)
        result = []
        for job_id, cs in by_job.items():
            cs.sort(key=lambda x: x.score, reverse=True)
            result.extend(cs[:max_per_job])
        return result

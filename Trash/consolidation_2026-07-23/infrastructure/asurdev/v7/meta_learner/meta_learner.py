#!/usr/bin/env python3
"""
Meta-Learner — learns which policy works best given workload + cluster state.
Policy_i → performance_i → meta_model → policy selection.
Input: regret history, workload type, cluster state class.
Output: best policy distribution π(P).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import numpy as np


@dataclass
class PolicyTrial:
    policy_id: str
    regret_history: list[float]
    workload_type: str   # "gpu_batch" | "cpu_batch" | "mixed" | "idle"
    cluster_state_class: str  # "healthy" | "degraded" | "critical"
    avg_regret: float
    win_rate: float


@dataclass
class PolicyRecommendation:
    policy_id: str
    weight: float   # probability of being best
    confidence: float
    reason: str


class MetaLearner:
    """
    Meta-learning over policy performance.
    Learns which policy to use given workload + cluster state.
    """

    def __init__(self, min_trials: int = 20):
        self.min_trials = min_trials
        self._trials: list[PolicyTrial] = []
        self._policy_scores: dict[str, list[float]] = {}

    def record_trial(self, trial: PolicyTrial) -> None:
        self._trials.append(trial)
        if trial.policy_id not in self._policy_scores:
            self._policy_scores[trial.policy_id] = []
        self._policy_scores[trial.policy_id].append(trial.avg_regret)

    def recommend(
        self,
        workload_type: str,
        cluster_state_class: str,
    ) -> list[PolicyRecommendation]:
        """
        Return ranked policy recommendations given current context.
        """
        relevant = [
            t for t in self._trials
            if t.workload_type == workload_type
            and t.cluster_state_class == cluster_state_class
        ]

        if len(relevant) < self.min_trials:
            # Fallback: use all-time best
            return self._all_time_best()

        # Score each policy by win rate in similar conditions
        policy_wins: dict[str, tuple[int, int]] = {}
        for t in relevant:
            if t.policy_id not in policy_wins:
                policy_wins[t.policy_id] = (0, 0)
            wins, total = policy_wins[t.policy_id]
            policy_wins[t.policy_id] = (wins + (1 if t.avg_regret < 0.3 else 0), total + 1)

        ranked = sorted(
            policy_wins.items(),
            key=lambda x: x[1][0] / max(x[1][1], 1),
            reverse=True,
        )

        total_weight = sum(wins / max(total, 1) for _, (wins, total) in ranked)
        recommendations = []
        for policy_id, (wins, total) in ranked:
            win_rate = wins / max(total, 1)
            recommendations.append(PolicyRecommendation(
                policy_id=policy_id,
                weight=win_rate / max(total_weight, 1e-9),
                confidence=min(total / self.min_trials, 1.0),
                reason=f"win_rate={win_rate:.2f} over {total} trials",
            ))

        return recommendations

    def _all_time_best(self) -> list[PolicyRecommendation]:
        """Fallback: simplest heuristic — lowest average regret."""
        if not self._trials:
            return [PolicyRecommendation(policy_id="default", weight=1.0, confidence=0.0, reason="no data")]

        avg_regrets = {pid: np.mean(scores) for pid, scores in self._policy_scores.items()}
        ranked = sorted(avg_regrets.items(), key=lambda x: x[1])
        best_pid = ranked[0][0]
        return [PolicyRecommendation(policy_id=best_pid, weight=1.0, confidence=0.1, reason="lowest avg regret")]

    def get_best_policy(self, workload_type: str, cluster_state_class: str) -> Optional[str]:
        recs = self.recommend(workload_type, cluster_state_class)
        return recs[0].policy_id if recs else None

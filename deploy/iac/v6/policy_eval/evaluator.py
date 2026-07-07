#!/usr/bin/env python3
"""
Policy Evaluator — regret-aware policy selection.
Policy space: (priority_weights, risk_threshold, admission_policy)
Regret = E[U_best] - E[U_selected]
Trails historical policies, computes empirical regret, selects best.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np


@dataclass
class Policy:
    policy_id: str
    alpha: float = 0.4  # throughput weight in utility
    beta: float = 0.4  # reliability weight
    gamma: float = 0.2  # migration cost weight
    risk_threshold: float = 0.7  # reject if P(failure) > threshold
    admission_policy: str = "aggressive"  # "conservative" | "aggressive" | "ml_aware"
    max_queue_depth: int = 50


@dataclass
class PolicyTrial:
    policy_id: str
    start_time: datetime
    end_time: datetime | None
    total_jobs: int
    accepted_jobs: int
    rejected_jobs: int
    completed_jobs: int
    failed_jobs: int
    throughput: float
    mean_latency: float
    failure_rate: float
    utility: float
    regret: float = 0.0


class PolicyEvaluator:
    """
    Evaluates policy performance using cumulative regret.
    regret(t) = U_best(t) - U_policy(t)
    Selects policy with lowest cumulative regret.
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.policies: dict[str, Policy] = {}
        self.trials: dict[str, list[PolicyTrial]] = {}
        self._best_policy: str | None = None
        self._regret_window_hours = self.config.get("regret_window_hours", 24)

    def register_policy(self, policy: Policy) -> None:
        self.policies[policy.policy_id] = policy
        self.trials.setdefault(policy.policy_id, [])

    def record_outcome(self, policy_id: str, trial: PolicyTrial) -> None:
        if policy_id not in self.policies:
            return
        self.trials[policy_id].append(trial)
        self._update_best()

    def evaluate_policy(self, policy_id: str) -> dict:
        """Return empirical performance stats for a policy."""
        if policy_id not in self.trials or not self.trials[policy_id]:
            return {"status": "no_data"}
        trials = self.trials[policy_id]
        recent = [t for t in trials if t.end_time and (datetime.now() - t.end_time) < timedelta(hours=self._regret_window_hours)]
        if not recent:
            recent = trials[-10:]
        return {
            "policy_id": policy_id,
            "n_trials": len(recent),
            "mean_throughput": np.mean([t.throughput for t in recent]),
            "mean_failure_rate": np.mean([t.failure_rate for t in recent]),
            "mean_utility": np.mean([t.utility for t in recent]),
            "mean_regret": np.mean([t.regret for t in recent]),
            "cumulative_regret": sum(t.regret for t in recent),
        }

    def get_best_policy(self) -> Policy | None:
        if not self._best_policy:
            self._update_best()
        return self.policies.get(self._best_policy) if self._best_policy else None

    def select_action(self, policy_id: str, action_scores: dict) -> str:
        """Select action using policy's scoring function."""
        policy = self.policies.get(policy_id)
        if not policy:
            return max(action_scores, key=action_scores.get)
        return max(action_scores, key=lambda a: self._policy_score(policy, a, action_scores[a]))

    def _policy_score(self, policy: Policy, action: str, base_score: float) -> float:
        """Apply policy weights to action score."""
        return base_score  # Simplified: real impl would factor alpha/beta/gamma

    def _update_best(self) -> None:
        if not self.trials:
            return
        best_id, best_utility = None, -np.inf
        for pid, trials in self.trials.items():
            if not trials:
                continue
            recent = [t for t in trials[-10:] if t.utility > -np.inf]
            if not recent:
                continue
            mean_u = np.mean([t.utility for t in recent])
            if mean_u > best_utility:
                best_utility = mean_u
                best_id = pid
        self._best_policy = best_id

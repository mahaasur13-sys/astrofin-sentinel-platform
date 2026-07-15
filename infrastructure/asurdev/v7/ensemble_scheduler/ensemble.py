#!/usr/bin/env python3
"""
Ensemble Scheduler — π = {P1, P2, P3}
final_action = argmax E[U(Pi)]
Reduces oscillation, stabilizes regret noise, enables exploration/exploitation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import numpy as np


@dataclass
class Policy:
    policy_id: str
    alpha: float
    beta: float
    gamma: float
    delta: float
    risk_threshold: float
    admission_policy: str
    weight: float = 1.0


@dataclass
class EnsembleDecision:
    selected_policy: str
    expected_utility: float
    confidence: float
    vote_distribution: dict[str, float]


class EnsembleScheduler:
    """
    Runs multiple policies simultaneously, selects best expected utility.
    """

    def __init__(self, policies: Optional[list[Policy]] = None):
        self.policies: list[Policy] = policies or [
            Policy(policy_id="P1_throughput", alpha=0.6, beta=0.2, gamma=0.1, delta=0.1, risk_threshold=0.2, admission_policy="aggressive"),
            Policy(policy_id="P2_balanced", alpha=0.4, beta=0.3, gamma=0.15, delta=0.15, risk_threshold=0.3, admission_policy="probabilistic"),
            Policy(policy_id="P3_reliable", alpha=0.2, beta=0.5, gamma=0.15, delta=0.15, risk_threshold=0.5, admission_policy="conservative"),
        ]
        self._performance_history: dict[str, list[float]] = {p.policy_id: [] for p in self.policies}

    def record_outcome(self, policy_id: str, utility: float) -> None:
        if policy_id in self._performance_history:
            self._performance_history[policy_id].append(utility)
            if len(self._performance_history[policy_id]) > 100:
                self._performance_history[policy_id] = self._performance_history[policy_id][-100:]

    def select(self, context: dict) -> EnsembleDecision:
        """
        Select best policy based on expected utility.
        final_action = argmax E[U(Pi)]
        """
        utilities = {}
        for p in self.policies:
            history = self._performance_history.get(p.policy_id, [])
            if len(history) < 5:
                # Use prior: balanced
                expected_u = 0.4 * p.alpha + 0.3 * p.beta + 0.15 * p.gamma + 0.15 * p.delta
            else:
                # Bayesian: posterior mean
                expected_u = float(np.mean(history))

            utilities[p.policy_id] = expected_u * p.weight

        best_pid = max(utilities, key=utilities.get)
        best_u = utilities[best_pid]

        # Confidence = how much better is best vs second-best
        sorted_utils = sorted(utilities.values(), reverse=True)
        if len(sorted_utils) >= 2 and sorted_utils[0] > 0:
            confidence = 1.0 - (sorted_utils[1] / sorted_utils[0])
        else:
            confidence = 0.5

        # Vote distribution
        total = sum(utilities.values())
        vote_dist = {pid: u / max(total, 1e-9) for pid, u in utilities.items()}

        return EnsembleDecision(
            selected_policy=best_pid,
            expected_utility=best_u,
            confidence=min(confidence, 1.0),
            vote_distribution=vote_dist,
        )

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        return next((p for p in self.policies if p.policy_id == policy_id), None)

    def update_weights(self, policy_id: str, new_weight: float) -> None:
        for p in self.policies:
            if p.policy_id == policy_id:
                p.weight = max(0.1, new_weight)

"""
SystemOptimizer v6.5 — Global optimization objective for ATOMFederationOS.

Problem:
  Each subsystem (Healer, Router, Metrics) optimizes locally.
  No global cost function exists.

Solution:
  J(system_state) = w_stability * stability_score
                  - w_cost   * operation_cost
                  - w_latency * avg_latency_ms
                  - w_violations * violation_penalty
                  - w_conflicts  * conflict_penalty

  Higher J = better system. We maximize J continuously.

Usage:
    optimizer = SystemOptimizer()
    J = optimizer.compute_J(snapshot=snap, action_cost=0.1)
    adjusted_weights = optimizer.gradient_descent_step(snapshot, action_history)
    # Use adjusted weights to reconfigure PolicyEngine priorities
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

__all__ = ["OptimizationResult", "SystemOptimizer"]


# ── Weights ───────────────────────────────────────────────────────────────────

@dataclass
class OptimizerWeights:
    w_stability: float = 0.40
    w_cost: float = 0.15
    w_latency: float = 0.20
    w_violations: float = 0.15
    w_conflicts: float = 0.10

    def to_dict(self) -> dict:
        return {
            "w_stability": self.w_stability,
            "w_cost": self.w_cost,
            "w_latency": self.w_latency,
            "w_violations": self.w_violations,
            "w_conflicts": self.w_conflicts,
        }


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class OptimizationResult:
    J: float                         # Composite objective value
    stability_contrib: float
    cost_penalty: float
    latency_penalty: float
    violation_penalty: float
    conflict_penalty: float
    weights_used: OptimizerWeights
    ts: float = field(default_factory=time.monotonic)

    @property
    def is_healthy(self) -> bool:
        return self.J > 0.5

    def to_dict(self) -> dict:
        return {
            "J": round(self.J, 4),
            "stability_contrib": round(self.stability_contrib, 4),
            "cost_penalty": round(self.cost_penalty, 4),
            "latency_penalty": round(self.latency_penalty, 4),
            "violation_penalty": round(self.violation_penalty, 4),
            "conflict_penalty": round(self.conflict_penalty, 4),
            "is_healthy": self.is_healthy,
            "weights": self.weights_used.to_dict(),
            "ts": round(self.ts, 4),
        }


# ── SystemOptimizer ────────────────────────────────────────────────────────────

class SystemOptimizer:
    """
    Global optimization objective for the ATOMFederationOS cluster.

    J = w_stability * stability_score
      - w_cost * operation_cost
      - w_latency * avg_latency_ms  (normalized to 0–1)
      - w_violations * violation_penalty
      - w_conflicts * conflict_penalty

    Gradient descent adjusts weights based on recent action outcomes:
      - If stability is high but latency is high → increase w_latency
      - If conflicts are frequent → increase w_conflicts
    """

    LATENCY_MAX_MS = 1000.0      # 1s = maximally bad latency
    VIOLATION_MAX_PER_MIN = 60.0 # 60/min = maximally bad violation rate

    def __init__(
        self,
        weights: OptimizerWeights | None = None,
        learning_rate: float = 0.05,
    ):
        self.weights = weights or OptimizerWeights()
        self.learning_rate = learning_rate
        self._history: list[tuple[float, dict]] = []  # (J, context)

    # ── Objective ────────────────────────────────────────────────────────────

    def compute_J(
        self,
        snapshot,
        action_cost: float = 0.0,
        avg_latency_ms: float = 0.0,
        conflict_count: int = 0,
    ) -> OptimizationResult:
        """
        Compute the global objective J for a given snapshot.

        Parameters:
          snapshot — StabilitySnapshot
          action_cost — cost of the last healing/routing action (0.0–1.0)
          avg_latency_ms — average peer latency in ms
          conflict_count — number of arbitration conflicts in last tick
        """
        # Stability contribution: positive (maximize)
        stability_contrib = self.weights.w_stability * snapshot.stability_score

        # Cost penalty: negative (minimize)
        cost_penalty = self.weights.w_cost * action_cost

        # Latency penalty: normalized 0–1, negative
        latency_norm = min(1.0, avg_latency_ms / self.LATENCY_MAX_MS)
        latency_penalty = self.weights.w_latency * latency_norm

        # Violation penalty: normalized 0–1, negative
        violation_rate = snapshot.violation_count_60s / self.VIOLATION_MAX_PER_MIN
        violation_penalty = self.weights.w_violations * min(1.0, violation_rate)

        # Conflict penalty: 0–1, negative
        conflict_penalty = self.weights.w_conflicts * min(1.0, conflict_count / 5.0)

        J = stability_contrib - cost_penalty - latency_penalty - violation_penalty - conflict_penalty
        J = max(-1.0, min(1.0, J))  # clamp to [-1, 1]

        return OptimizationResult(
            J=J,
            stability_contrib=stability_contrib,
            cost_penalty=cost_penalty,
            latency_penalty=latency_penalty,
            violation_penalty=violation_penalty,
            conflict_penalty=conflict_penalty,
            weights_used=self.weights,
        )

    # ── Gradient descent ────────────────────────────────────────────────────

    def gradient_descent_step(
        self,
        snapshot,
        action_history: list[dict],
    ) -> OptimizerWeights:
        """
        Adjust weights based on observed outcomes of recent actions.

        If stability improved → reduce w_stability (diminishing returns).
        If latency dominated failures → increase w_latency.
        If violations dominated failures → increase w_violations.
        If conflicts caused problems → increase w_conflicts.

        action_history: list of {
            "action": str,
            "target": str,
            "outcome": "success" | "failure",
            "latency_ms": float,
            "violations": int,
            "conflicts": int,
        }
        """
        if len(action_history) < 3:
            return self.weights  # Not enough data

        recent = action_history[-10:]  # last 10 actions

        # Compute outcome signals
        success_rate = sum(1 for a in recent if a.get("outcome") == "success") / len(recent)
        avg_lat = sum(a.get("latency_ms", 0) for a in recent) / len(recent)
        total_violations = sum(a.get("violations", 0) for a in recent)
        total_conflicts = sum(a.get("conflicts", 0) for a in recent)

        # Adaptive weight adjustment
        lr = self.learning_rate

        # If success rate is low and latency is high → prioritize latency
        if success_rate < 0.7 and avg_lat > 100:
            self.weights.w_latency = min(0.50, self.weights.w_latency + lr * 0.1)

        # If violations are high → prioritize stability
        if total_violations > 5:
            self.weights.w_stability = min(0.60, self.weights.w_stability + lr * 0.05)

        # If conflicts are high → increase conflict penalty weight
        if total_conflicts > 3:
            self.weights.w_conflicts = min(0.30, self.weights.w_conflicts + lr * 0.05)

        # If recovery rate is good → reduce cost weight (less healing needed)
        if snapshot.recovery_rate > 0.85:
            self.weights.w_cost = max(0.05, self.weights.w_cost - lr * 0.02)

        # Renormalize weights to sum to 1.0
        total = (
            self.weights.w_stability
            + self.weights.w_cost
            + self.weights.w_latency
            + self.weights.w_violations
            + self.weights.w_conflicts
        )
        if total > 0:
            scale = 1.0 / total
            self.weights.w_stability *= scale
            self.weights.w_cost *= scale
            self.weights.w_latency *= scale
            self.weights.w_violations *= scale
            self.weights.w_conflicts *= scale

        self._history.append(
            (self.compute_J(snapshot, 0.0, avg_lat, total_conflicts).J, {
                "success_rate": success_rate,
                "avg_lat": avg_lat,
                "violations": total_violations,
                "conflicts": total_conflicts,
            })
        )
        return self.weights

    # ── Introspection ───────────────────────────────────────────────────

    def get_weights(self) -> OptimizerWeights:
        return self.weights

    def dump(self) -> dict:
        return {
            "weights": self.weights.to_dict(),
            "learning_rate": self.learning_rate,
            "history_len": len(self._history),
            "last_J": self._history[-1][0] if self._history else None,
        }

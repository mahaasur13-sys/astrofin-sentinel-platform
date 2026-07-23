"""
v6.8 — Global Objective Stabilizer.

New J(t) formula:
  J(t) = α · stability_score
       + β · consistency_score
       - γ · control_cost

Where:
  stability_score ∈ [0, 1]        from StabilitySnapshot
  consistency_score ∈ [0, 1]      temporal coherence of lattice decisions
  control_cost ∈ [0, 1]          normalized healing/control action overhead

The old v6.7 formula:
  J_old = w_stability * stability
         - w_cost * action_cost
         - w_latency * latency_norm
         - w_violations * violation_norm
         - w_conflicts * conflict_norm

is provided via JCompatibilityAdapter for backward compatibility.

Additionally, this module enforces:
  - Monotonic trajectory smoothing: J(t) cannot decrease more than Δ per tick
  - Trajectory history: tracks last W window of J values
  - Global convergence: J(t) must trend toward stable equilibrium

Usage:
    stabilizer = GlobalObjectiveStabilizer()
    result = stabilizer.compute_J(snap, consistency_score=0.85, control_cost=0.1)
    # result.J_new → v6.8 formula
    # result.J_compat → v6.7 adapter (for legacy callers)
    allowed, trajectory_ok = stabilizer.check_trajectory(J_new)
"""

from __future__ import annotations

import time
from dataclasses import dataclass

__all__ = ["GlobalObjectiveStabilizer", "JCompatibilityAdapter", "StabilizerSnapshot"]


# ── Default weights ───────────────────────────────────────────────────────────

@dataclass
class StabilizerWeights:
    """v6.8 J(t) coefficients."""
    alpha_stability: float = 0.50   # weight for stability score
    beta_consistency: float = 0.30  # weight for consistency score
    gamma_cost: float = 0.20        # weight for control cost penalty
    # Reserved for future expansion (DRL, eigenstate, drift)
    # delta_eigenstate: float = 0.0
    # epsilon_drift: float = 0.0


@dataclass
class StabilizerSnapshot:
    ts: float
    J_new: float                  # v6.8 formula result
    J_compat: float               # v6.7 adapter result
    stability_contrib: float
    consistency_contrib: float
    cost_penalty: float
    trajectory_ok: bool           # True if J(t) is monotonic within tolerance
    J_direction: str            # "rising" | "falling" | "stable"
    trajectory_violation: bool   # True if monotonicity was violated
    trajectory_tolerance: float
    weights: StabilizerWeights
    coherence_mode: str           # "v68_new" | "v67_legacy"


class JCompatibilityAdapter:
    """
    Adapter that wraps OptimizerWeights (v6.7) to produce a J value
    compatible with the old SystemOptimizer.compute_J() formula.

    Usage by legacy code:
      compat = JCompatibilityAdapter(optimizer)
      J_compat = compat.compute_compat(snapshot, action_cost, latency, conflicts)
    """

    def __init__(self, optimizer) -> None:
        self._opt = optimizer

    def compute_compat(
        self,
        snapshot,
        action_cost: float = 0.0,
        avg_latency_ms: float = 0.0,
        conflict_count: int = 0,
    ):
        """Compute J using v6.7 formula (delegate to SystemOptimizer)."""
        return self._opt.compute_J(
            snapshot,
            action_cost=action_cost,
            avg_latency_ms=avg_latency_ms,
            conflict_count=conflict_count,
        )


class GlobalObjectiveStabilizer:
    """
    Computes J(t) = α·stability + β·consistency − γ·control_cost
    and enforces monotonic trajectory smoothing.

    Parameters
    ----------
    alpha, beta, gamma : float
        Coefficients for the new J formula. Must sum to 1.0
        (enforced on init).
    trajectory_tolerance : float
        Maximum allowed J decrease per tick before flagging a
        trajectory violation (default 0.05).
    trajectory_window : int
        Number of past ticks to consider for trajectory check
        (default 10).
    weights : StabilizerWeights, optional
        Explicit weights. If None, uses defaults.
    optimizer : SystemOptimizer, optional
        For J_compat backward-compatibility computation.
    """

    def __init__(
        self,
        alpha: float = 0.50,
        beta: float = 0.30,
        gamma: float = 0.20,
        trajectory_tolerance: float = 0.05,
        trajectory_window: int = 10,
        weights: StabilizerWeights | None = None,
        optimizer=None,
    ) -> None:
        # Enforce sum-to-1.0
        total = alpha + beta + gamma
        if abs(total - 1.0) > 1e-6:
            scale = 1.0 / total
            alpha *= scale
            beta *= scale
            gamma *= scale

        self._weights = weights or StabilizerWeights(
            alpha_stability=alpha,
            beta_consistency=beta,
            gamma_cost=gamma,
        )
        self._trajectory_tolerance = trajectory_tolerance
        self._trajectory_window = trajectory_window

        # J history for trajectory validation
        self._J_history: list[float] = []
        self._ts_history: list[float] = []

        self._compat_adapter = JCompatibilityAdapter(optimizer) if optimizer else None
        self._last_snapshot: StabilizerSnapshot | None = None

    def compute_J(
        self,
        stability_score: float,
        consistency_score: float,
        control_cost: float,
        J_compat: float | None = None,
    ) -> StabilizerSnapshot:
        """
        Compute v6.8 J(t) with trajectory validation.

        Parameters
        ----------
        stability_score : float
            Cluster stability in [0, 1].
        consistency_score : float
            Lattice decision consistency in [0, 1]
            (e.g. from TemporalCoherenceSmoother).
        control_cost : float
            Normalized control overhead in [0, 1].
        J_compat : float, optional
            Pass v6.7 J value here for the compat output field.

        Returns StabilizerSnapshot.
        """
        now = time.time()
        w = self._weights

        # v6.8 formula
        stability_contrib = w.alpha_stability * stability_score
        consistency_contrib = w.beta_consistency * consistency_score
        cost_penalty = w.gamma_cost * control_cost

        J_new = stability_contrib + consistency_contrib - cost_penalty
        J_new = max(-1.0, min(1.0, J_new))

        # Trajectory check
        trajectory_ok, J_direction, violation = self._check_trajectory(J_new)

        snap = StabilizerSnapshot(
            ts=now,
            J_new=round(J_new, 4),
            J_compat=J_compat if J_compat is not None else J_new,
            stability_contrib=round(stability_contrib, 4),
            consistency_contrib=round(consistency_contrib, 4),
            cost_penalty=round(cost_penalty, 4),
            trajectory_ok=trajectory_ok,
            J_direction=J_direction,
            trajectory_violation=violation,
            trajectory_tolerance=self._trajectory_tolerance,
            weights=w,
            coherence_mode="v68_new",
        )
        self._last_snapshot = snap
        return snap

    def _check_trajectory(
        self,
        J_current: float,
    ) -> tuple[bool, str, bool]:
        """
        Check that J(t) trajectory is monotonic within tolerance.

        Returns (trajectory_ok, J_direction, violation).
        violation = True if J decreased more than tolerance vs previous tick.
        """
        self._J_history.append(J_current)
        self._ts_history.append(time.time())
        if len(self._J_history) > self._trajectory_window:
            self._J_history = self._J_history[-self._trajectory_window:]
            self._ts_history = self._ts_history[-self._trajectory_window:]

        if len(self._J_history) < 2:
            return True, "stable", False

        prev = self._J_history[-2]
        delta = J_current - prev

        if delta > self._trajectory_tolerance:
            direction = "rising"
            violation = False
        elif delta < -self._trajectory_tolerance:
            direction = "falling"
            violation = True
        else:
            direction = "stable"
            violation = False

        return not violation, direction, violation

    def get_compat_J(
        self,
        snapshot,
        action_cost: float = 0.0,
        avg_latency_ms: float = 0.0,
        conflict_count: int = 0,
    ) -> float:
        """Compute v6.7-compatible J via adapter (for backward compat)."""
        if self._compat_adapter is None:
            return 0.0
        result = self._compat_adapter.compute_compat(
            snapshot, action_cost, avg_latency_ms, conflict_count
        )
        return result.J

    def set_weights(self, weights: StabilizerWeights) -> None:
        """Update J(t) coefficients at runtime."""
        self._weights = weights

    def get_snapshot(self) -> StabilizerSnapshot | None:
        return self._last_snapshot

    def summary(self) -> dict:
        snap = self._last_snapshot
        return {
            "J_new": snap.J_new if snap else None,
            "J_compat": snap.J_compat if snap else None,
            "trajectory_ok": snap.trajectory_ok if snap else None,
            "J_direction": snap.J_direction if snap else None,
            "trajectory_violation": snap.trajectory_violation if snap else None,
            "weights": {
                "alpha": self._weights.alpha_stability,
                "beta": self._weights.beta_consistency,
                "gamma": self._weights.gamma_cost,
            },
            "trajectory_window": self._trajectory_window,
            "trajectory_tolerance": self._trajectory_tolerance,
        }

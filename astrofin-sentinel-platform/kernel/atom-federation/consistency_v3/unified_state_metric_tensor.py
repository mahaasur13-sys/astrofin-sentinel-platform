"""
unified_state_metric_tensor.py
===============================
v7.2 — UnifiedStateMetricTensor: combines all divergence axes into one tensor metric.

Axes combined:
  [0] state_diff      — ||V_exec - V_replay||_2 in causal semantic space
  [1] temporal_drift  — wallclock_ns delta between exec and replay
  [2] rate_drift      — |R_exec - R_replay| (transitions per second)
  [3] causal_div      — |C_exec - C_replay| (causal depth difference)
  [4] fingerprint_div — Hamming distance of rolling SHA-256 fingerprints

The tensor is a rank-0 (scalar) metric: S_full = w · axis_vector
with learned or configured weights w = [w0..w4].

Divergence severity levels:
  0.0 - 0.1   : IDENTICAL         (within noise floor)
  0.1 - 1.0   : MINOR             (noise-level divergence)
  1.0 - 5.0   : MODERATE          (actionable)
  5.0 - 10.0  : SEVERE            (requires intervention)
  > 10.0      : CRITICAL          (systems are dynamically decoupled)

This is the single number that answers: "How bad is the divergence, overall?"
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# Axis labels
AXIS_STATE_DIFF = 0
AXIS_TEMPORAL_DRIFT = 1
AXIS_RATE_DRIFT = 2
AXIS_CAUSAL_DIV = 3
AXIS_FINGERPRINT_DIV = 4
AXIS_COUNT = 5

AXIS_LABELS = [
    "state_diff",
    "temporal_drift",
    "rate_drift",
    "causal_div",
    "fingerprint_div",
]

DEFAULT_WEIGHTS = [1.0, 0.3, 0.5, 0.7, 0.8]


@dataclass
class AxisVector:
    """
    Per-tick divergence vector across all 5 axes.

    Each axis is normalized to [0, +inf); raw values depend on scale of the system.
    """

    state_diff: float = 0.0
    temporal_drift: float = 0.0   # nanoseconds, normalized to ms
    rate_drift: float = 0.0        # transitions/sec delta
    causal_div: float = 0.0       # causal depth delta (absolute)
    fingerprint_div: float = 0.0  # Hamming distance of hex digest chars

    def to_vector(self) -> list[float]:
        return [
            self.state_diff,
            self.temporal_drift,
            self.rate_drift,
            self.causal_div,
            self.fingerprint_div,
        ]

    @classmethod
    def from_fingerprints(
        cls, fp_exec: str, fp_replay: str, **kwargs: float
    ) -> AxisVector:
        """Compute Hamming distance between two hex fingerprints."""
        fp_dist = _hamming_hex(fp_exec, fp_replay) if fp_exec and fp_replay else 0.0
        return cls(fingerprint_div=fp_dist, **kwargs)

    def magnitude(self) -> float:
        return math.sqrt(sum(x**2 for x in self.to_vector()))

    def weighted_sum(self, weights: list[float]) -> float:
        v = self.to_vector()
        return sum(w * x for w, x in zip(weights, v))


@dataclass
class UnifiedStateMetricTensor:
    """
    Single-score divergence metric combining all 5 axes.

    The full metric S_full = w · axis_vector, where:
      - axis_vector = [state_diff, temporal_drift, rate_drift, causal_div, fingerprint_div]
      - weights are configurable (DEFAULT_WEIGHTS used if not provided)

    Severity thresholds (S_full):
      0 - 0.1   : IDENTICAL
      0.1 - 1.0 : MINOR
      1.0 - 5.0 : MODERATE
      5.0 - 10. : SEVERE
      > 10.     : CRITICAL
    """

    domain: str
    weights: list[float] = field(default_factory=lambda: list(DEFAULT_WEIGHTS))

    _history: list[AxisVector] = field(default_factory=list)
    _window_size: int = 32

    # Previous tick data (for delta computation)
    _prev_fp_exec: str = ""
    _prev_fp_replay: str = ""
    _prev_transitions_exec: int = 0
    _prev_transitions_replay: int = 0
    _prev_wallclock_ns: int = 0
    _prev_c_depth_exec: int = 0
    _prev_c_depth_replay: int = 0

    def push(
        self,
        exec_state: dict[str, Any],
        replay_state: dict[str, Any],
        fp_exec: str,
        fp_replay: str,
        transitions_exec: int = 0,
        transitions_replay: int = 0,
        c_depth_exec: int = 0,
        c_depth_replay: int = 0,
        wallclock_ns: int | None = None,
    ) -> AxisVector:
        """
        Compute the per-axis divergence vector for the current tick and store it.
        """
        now_ns = wallclock_ns or int(_time_ns())
        prev_ns = self._prev_wallclock_ns or now_ns

        # state diff (L2 norm proxy)
        state_diff = _dict_l2_delta(exec_state, replay_state)

        # temporal drift
        temporal_drift = (now_ns - prev_ns) / 1_000_000  # normalize to ms

        # rate drift
        dt = max(1e-9, (now_ns - prev_ns) / 1e9)  # seconds
        rate_exec = (transitions_exec - self._prev_transitions_exec) / dt
        rate_replay = (transitions_replay - self._prev_transitions_replay) / dt
        rate_drift = abs(rate_exec - rate_replay)

        # causal div
        causal_div = abs(c_depth_exec - self._prev_c_depth_exec) + abs(
            c_depth_replay - self._prev_c_depth_replay
        )

        # fingerprint div
        axis_vec = AxisVector.from_fingerprints(
            fp_exec,
            fp_replay,
            state_diff=state_diff,
            temporal_drift=temporal_drift,
            rate_drift=rate_drift,
            causal_div=causal_div,
        )

        self._history.append(axis_vec)
        if len(self._history) > self._window_size:
            self._history = self._history[-self._window_size :]

        # Update prev tick trackers
        self._prev_fp_exec = fp_exec
        self._prev_fp_replay = fp_replay
        self._prev_transitions_exec = transitions_exec
        self._prev_transitions_replay = transitions_replay
        self._prev_wallclock_ns = now_ns
        self._prev_c_depth_exec = c_depth_exec
        self._prev_c_depth_replay = c_depth_replay

        return axis_vec

    def S_full(self, axis_vec: AxisVector | None = None) -> float:
        """
        Full scalar metric: weighted sum of axis vector.
        If axis_vec not provided, uses most recent.
        """
        if axis_vec is None:
            if not self._history:
                return 0.0
            axis_vec = self._history[-1]
        return axis_vec.weighted_sum(self.weights)

    def severity_level(self, axis_vec: AxisVector | None = None) -> str:
        """Human-readable severity level."""
        s = self.S_full(axis_vec)
        if s <= 0.1:
            return "IDENTICAL"
        elif s <= 1.0:
            return "MINOR"
        elif s <= 5.0:
            return "MODERATE"
        elif s <= 10.0:
            return "SEVERE"
        else:
            return "CRITICAL"

    def trajectory(self) -> list[float]:
        """S_full over the rolling window — for trend analysis."""
        return [self.S_full(v) for v in self._history]

    def to_dict(self) -> dict[str, Any]:
        traj = self.trajectory()
        current_vec = self._history[-1] if self._history else AxisVector()
        return {
            "domain": self.domain,
            "weights": self.weights,
            "S_full_current": self.S_full(),
            "severity": self.severity_level(),
            "axis_vector_current": current_vec.to_vector(),
            "axis_labels": AXIS_LABELS,
            "trajectory": traj,
            "history_size": len(self._history),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────


def _time_ns() -> int:
    import time
    return int(time.time_ns())


def _dict_l2_delta(a: dict[str, Any], b: dict[str, Any]) -> float:
    """L2 norm of the difference between two state dicts."""
    all_keys = set(a.keys()) | set(b.keys())
    squared = 0.0
    for k in all_keys:
        av = a.get(k)
        bv = b.get(k)
        if isinstance(av, (int, float)) and isinstance(bv, (int, float)):
            squared += (float(av) - float(bv)) ** 2
        elif isinstance(av, dict) and isinstance(bv, dict):
            squared += _dict_l2_delta(av, bv) ** 2
    return math.sqrt(squared)


def _hamming_hex(a: str, b: str) -> float:
    """Hamming distance between two equal-length hex strings."""
    if len(a) != len(b):
        return float(max(len(a), len(b)))  # max distance for unequal length
    return float(sum(c1 != c2 for c1, c2 in zip(a, b)))

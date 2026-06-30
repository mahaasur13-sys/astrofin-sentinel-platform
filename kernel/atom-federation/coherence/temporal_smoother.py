"""
v6.8 — Temporal Coherence Smoother.

Prevents oscillation between consecutive decisions by stabilizing
lattice transitions over time.

Uses an adaptive window W:
  W = base_window * (1 + volatility_index)

volatility_index is derived from:
  - DRL drop rate
  - Latency variance
  - SBS violation frequency

When volatility is high, the window widens to smooth more;
when the system is calm, the window shrinks for faster response.

The smoother tracks the history of lattice decisions and applies
exponential moving average (EMA) smoothing to the decision trajectory.
"""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

__all__ = ["SmootherSnapshot", "TemporalCoherenceSmoother"]


# ── Decision similarity ───────────────────────────────────────────────────────

# Map PolicyAction names to an integer for distance computation
_ACTION_RANK = {
    "NOOP": 0,
    "ADD_OBSERVATION": 1,
    "LOG_ONLY": 1,
    "ALERT_OPS": 2,
    "TRIGGER_SELF_HEAL": 3,
    "RECONFIGURE_QUORUM": 3,
    "RESTORE_NODE": 4,
    "DRAIN_NODE": 4,
    "TRIGGER_RE_ELECTION": 5,
    "EVICT_NODE": 6,
    "ISOLATE_BYZANTINE": 7,
}


def _decision_distance(action_a: str, action_b: str) -> float:
    """Normalized [0,1] distance between two actions by rank difference."""
    rank_a = _ACTION_RANK.get(action_a, 0)
    rank_b = _ACTION_RANK.get(action_b, 0)
    max_rank = max(_ACTION_RANK.values()) if _ACTION_RANK else 1
    return abs(rank_a - rank_b) / max_rank if max_rank > 0 else 0.0


@dataclass
class SmootherSnapshot:
    ts: float
    current_window: float           # adaptive W at this tick
    volatility_index: float        # current volatility
    smoothed_action: str           # EMA-smoothed action name
    raw_action: str                # most recent lattice action
    oscillation_strength: float    # 0=no oscillation, 1=strong oscillation
    transition_count: int          # number of smoothed transitions
    damping_applied: bool         # whether raw action was damped
    base_window: float
    lattice_stability_score: float  # 0..1, higher = more stable lattice


class TemporalCoherenceSmoother:
    """
    Stabilizes lattice transitions over time using adaptive exponential
    moving average (EMA) smoothing.

    The smoother:
      1. Maintains a rolling history of raw lattice decisions
      2. Computes volatility_index from DRL metrics + violation rate
      3. Adapts window W = base_window * (1 + volatility_index)
      4. Applies EMA smoothing weighted by adaptive window
      5. Returns a damped "smoothed_action" that prevents oscillation

    Parameters
    ----------
    base_window : int
        Minimum smoothing window in ticks (default 5).
    max_window : int
        Maximum smoothing window in ticks (default 30).
    volatility_scale : float
        Multiplier for volatility contribution to window expansion
        (default 2.0).
    """

    def __init__(
        self,
        base_window: int = 5,
        max_window: int = 30,
        volatility_scale: float = 2.0,
    ) -> None:
        self._base_window = base_window
        self._max_window = max_window
        self._volatility_scale = volatility_scale

        self._action_history: list[str] = []
        self._ema_value: float = 0.0          # continuous EMA state (0..1)
        self._ema_alpha: float = 0.3         # EMA coefficient (set by window)
        self._transition_count = 0
        self._damping_count = 0
        self._oscillation_strength = 0.0
        self._lattice_stability_score = 1.0

        # Volatility signal inputs (updated externally via ingest)
        self._drl_drop_rate = 0.0
        self._latency_variance = 0.0
        self._violation_rate = 0.0
        self._last_violation_count = 0

        self._last_snapshot: SmootherSnapshot | None = None

    def ingest(
        self,
        drl_drop_rate: float,
        latency_ms: float,
        latency_history_ms: list[float],
        violation_count: int,
    ) -> None:
        """
        Update volatility signals from DRL + SBS metrics.

        Called every tick before smooth() to prime the smoother
        with current volatility conditions.
        """
        self._drl_drop_rate = drl_drop_rate
        self._violation_rate = violation_count

        if len(latency_history_ms) >= 2:
            self._latency_variance = statistics.pstdev(latency_history_ms)
        elif latency_ms > 0:
            self._latency_variance = latency_ms * 0.1

    def smooth(self, raw_action: str) -> SmootherSnapshot:
        """
        Apply EMA smoothing to the raw lattice action.

        Returns SmootherSnapshot with:
          - smoothed_action: damped action (same as raw if oscillation is low)
          - damping_applied: True if raw was modified
          - oscillation_strength: measure of decision instability
        """
        now = time.monotonic()

        # ── Compute adaptive window ──────────────────────────────────────
        # volatility_index ∈ [0, 1]
        vi = self._compute_volatility_index()
        window = min(self._max_window, int(
            self._base_window * (1.0 + vi * self._volatility_scale)
        ))

        # ── Update EMA alpha based on window ────────────────────────────
        # Larger window → smaller alpha (more smoothing)
        self._ema_alpha = 2.0 / (window + 1)

        # ── Track action history ────────────────────────────────────────
        self._action_history.append(raw_action)
        if len(self._action_history) > self._max_window * 2:
            self._action_history = self._action_history[-(self._max_window * 2):]

        # ── Compute oscillation strength ─────────────────────────────────
        oscillation = self._detect_oscillation()
        self._oscillation_strength = oscillation

        # ── Update lattice stability score ───────────────────────────────
        # Penalize high oscillation, reward long runs of same action
        if len(self._action_history) >= window:
            recent_actions = self._action_history[-window:]
            unique = len(set(recent_actions))
            self._lattice_stability_score = max(0.0, 1.0 - (unique - 1) / max(unique, 1))

        # ── EMA smoothing on action rank ─────────────────────────────────
        current_rank = _ACTION_RANK.get(raw_action, 0)
        max_rank = max(_ACTION_RANK.values()) if _ACTION_RANK else 1
        normalized_rank = current_rank / max_rank if max_rank > 0 else 0.0

        self._ema_value = (
            self._ema_alpha * normalized_rank
            + (1.0 - self._ema_alpha) * self._ema_value
        )

        # ── Determine smoothed action ────────────────────────────────────
        # Find the closest-action by rank to the EMA value
        damped = self._rank_to_action(self._ema_value * max_rank)
        damping_applied = damped != raw_action

        if damping_applied:
            self._damping_count += 1

        self._transition_count += 1

        snap = SmootherSnapshot(
            ts=now,
            current_window=float(window),
            volatility_index=vi,
            smoothed_action=damped,
            raw_action=raw_action,
            oscillation_strength=oscillation,
            transition_count=self._transition_count,
            damping_applied=damping_applied,
            base_window=float(self._base_window),
            lattice_stability_score=round(self._lattice_stability_score, 4),
        )
        self._last_snapshot = snap
        return snap

    def _compute_volatility_index(self) -> float:
        """
        volatility_index ∈ [0, 1].

        Combines:
          - DRL drop rate (0..0.5 normalized)
          - Latency variance (0..100ms normalized)
          - Violation rate (0..60/min normalized)
        """
        drop_component = min(1.0, self._drl_drop_rate / 0.05)
        lat_component = min(1.0, self._latency_variance / 100.0)
        viol_component = min(1.0, self._violation_rate / 60.0)
        return min(1.0, (drop_component * 0.3 + lat_component * 0.4 + viol_component * 0.3))

    def _detect_oscillation(self) -> float:
        """
        Detect rapid alternation between actions (flapping).

        Returns float in [0, 1]:
          0 = no oscillation (stable trajectory)
          1 = strong oscillation (alternating every tick)
        """
        if len(self._action_history) < 4:
            return 0.0

        recent = self._action_history[-4:]
        # Count alternations (action differs from previous)
        alternations = sum(
            1 for i in range(1, len(recent))
            if recent[i] != recent[i - 1]
        )
        return alternations / max(1, len(recent) - 1)

    def _rank_to_action(self, rank: float) -> str:
        """Find action name whose rank is closest to `rank`."""
        best_action = "NOOP"
        best_dist = float("inf")
        for action, r in _ACTION_RANK.items():
            dist = abs(r - rank)
            if dist < best_dist:
                best_dist = dist
                best_action = action
        return best_action

    def get_snapshot(self) -> SmootherSnapshot | None:
        return self._last_snapshot

    def summary(self) -> dict:
        snap = self._last_snapshot
        return {
            "current_window": snap.current_window if snap else None,
            "volatility_index": snap.volatility_index if snap else None,
            "smoothed_action": snap.smoothed_action if snap else None,
            "oscillation_strength": snap.oscillation_strength if snap else None,
            "transition_count": self._transition_count,
            "damping_count": self._damping_count,
            "lattice_stability_score": snap.lattice_stability_score if snap else None,
            "base_window": self._base_window,
        }

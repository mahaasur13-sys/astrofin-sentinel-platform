"""
v6.8 — Model–Reality Drift Controller.

Drift = |SelfModel(t) − Reality(t)|

Control law:
  if drift > threshold + hysteresis_band:
      correction = k_p * drift
      apply_partial_repair(correction)
  elif drift < threshold − hysteresis_band:
      no-op  # inside hysteresis band → no jitter loop
  else:
      no-op  # below threshold

Uses event-triggered + proportional (P) hybrid:
  - event-triggered: only acts when threshold breached
  - P-controller: scales correction proportionally to drift magnitude
  - hysteresis band: prevents oscillation at the boundary

Drift is computed as weighted L2 distance over normalized features.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto

__all__ = ["DriftController", "DriftSnapshot", "DriftStatus"]


class DriftStatus(Enum):
    STABLE = auto()      # drift ≤ threshold − hysteresis
    BORDERLINE = auto()  # threshold − hysteresis < drift ≤ threshold + hysteresis
    DRIFTING = auto()    # threshold + hysteresis < drift ≤ critical
    CRITICAL = auto()    # drift > critical_threshold
    CORRECTION_APPLIED = auto()


# ── Feature weights (importance of each metric in drift calculation) ─────────

FEATURE_WEIGHTS = {
    "cpu": 0.20,
    "mem": 0.15,
    "latency_ms": 0.25,
    "packet_loss": 0.20,
    "throughput": 0.10,
    "error_rate": 0.10,
}


def _weighted_l2(real: dict[str, float], model: dict[str, float]) -> float:
    """
    Weighted L2 distance between real and model state.
    Only considers keys present in FEATURE_WEIGHTS.
    Each feature is normalized to [0, 1] before distance computation.
    """
    total = 0.0
    for feat, weight in FEATURE_WEIGHTS.items():
        if feat in real and feat in model:
            # Normalize: assume real values are in [0, 1] for rate metrics
            # and [0, 1000] for latency. Clamp to [0, 1] after scaling.
            r = max(0.0, min(1.0, real[feat]))
            m = max(0.0, min(1.0, model[feat]))
            diff = r - m
            total += weight * (diff ** 2)
    return total ** 0.5


@dataclass
class DriftSnapshot:
    ts: float
    drift_score: float               # raw weighted L2 distance
    drift_status: DriftStatus
    correction_magnitude: float      # magnitude of last correction applied
    correction_applied: bool
    threshold: float
    hysteresis_band: float
    k_p: float
    model_version: int
    cumulative_drift_energy: float   # Σ drift over time (for trending)
    drift_trend: str                 # "stable" | "growing" | "shrinking" | "insufficient_data"


class DriftController:
    """
    Event-triggered P-controller with hysteresis for model–reality alignment.

    Parameters
    ----------
    drift_threshold : float
        Trigger threshold for drift detection (default 0.15).
    critical_threshold : float
        Hard critical threshold — sets status to CRITICAL (default 0.40).
    hysteresis_band : float
        Width of no-action zone around threshold to prevent jitter
        (default 0.03). No action taken when:
          threshold − hysteresis < drift ≤ threshold + hysteresis
    k_p : float
        Proportional gain for correction magnitude:
          correction = k_p * drift  (default 0.5).
    max_correction : float
        Maximum correction magnitude (default 1.0, normalized [0,1]).
    """

    def __init__(
        self,
        drift_threshold: float = 0.15,
        critical_threshold: float = 0.40,
        hysteresis_band: float = 0.03,
        k_p: float = 0.5,
        max_correction: float = 1.0,
    ) -> None:
        self._threshold = drift_threshold
        self._critical = critical_threshold
        self._hysteresis = hysteresis_band
        self._k_p = k_p
        self._max_correction = max_correction

        self._model_version = 0
        self._last_drift = 0.0
        self._last_correction = 0.0
        self._correction_count = 0
        self._cumulative_drift_energy = 0.0
        self._drift_history: list[float] = []
        self._ts_last = time.monotonic()
        self._last_snapshot: DriftSnapshot | None = None
        self._in_correction = False  # guard against re-triggering immediately

    def observe(
        self,
        real_state: dict[str, float],
        model_state: dict[str, float],
    ) -> DriftSnapshot:
        """
        Compute drift and apply correction if threshold is breached.

        Returns DriftSnapshot with current drift status.
        """
        now = time.monotonic()
        drift = _weighted_l2(real_state, model_state)

        # Update cumulative drift energy (for trend analysis)
        dt = now - self._ts_last
        self._cumulative_drift_energy += drift * dt
        self._ts_last = now

        # Track drift history (last 20 points)
        self._drift_history.append(drift)
        if len(self._drift_history) > 20:
            self._drift_history = self._drift_history[-20:]

        status = self._classify_drift(drift)
        correction_applied = False
        correction_magnitude = 0.0

        # Decision: apply correction only outside hysteresis band
        # Hysteresis band prevents jitter loop at threshold boundary
        self._threshold + self._hysteresis
        lower = self._threshold - self._hysteresis

        if status in (DriftStatus.DRIFTING, DriftStatus.CRITICAL) and not self._in_correction:
            correction_magnitude = min(self._max_correction, self._k_p * drift)
            self._in_correction = True
            correction_applied = True
            self._correction_count += 1
            self._model_version += 1
        elif status == DriftStatus.STABLE and drift < lower:
            # Clear correction guard once drift is safely below lower boundary
            self._in_correction = False

        self._last_drift = drift
        self._last_correction = correction_magnitude

        snap = DriftSnapshot(
            ts=now,
            drift_score=drift,
            drift_status=status,
            correction_magnitude=correction_magnitude,
            correction_applied=correction_applied,
            threshold=self._threshold,
            hysteresis_band=self._hysteresis,
            k_p=self._k_p,
            model_version=self._model_version,
            cumulative_drift_energy=self._cumulative_drift_energy,
            drift_trend=self._compute_trend(),
        )
        self._last_snapshot = snap
        return snap

    def _classify_drift(self, drift: float) -> DriftStatus:
        if drift <= self._threshold - self._hysteresis:
            return DriftStatus.STABLE
        elif drift <= self._threshold + self._hysteresis:
            return DriftStatus.BORDERLINE
        elif drift <= self._critical:
            return DriftStatus.DRIFTING
        else:
            return DriftStatus.CRITICAL

    def _compute_trend(self) -> str:
        if len(self._drift_history) < 3:
            return "insufficient_data"
        recent = self._drift_history[-3:]
        if recent[-1] < recent[0] - 0.01:
            return "shrinking"
        elif recent[-1] > recent[0] + 0.01:
            return "growing"
        return "stable"

    def get_snapshot(self) -> DriftSnapshot | None:
        return self._last_snapshot

    def force_correction(self, reason: str = "manual") -> DriftSnapshot:
        """Force a correction even if drift is within threshold."""
        now = time.monotonic()
        self._in_correction = True
        self._correction_count += 1
        self._model_version += 1
        correction_magnitude = self._max_correction * 0.5

        snap = DriftSnapshot(
            ts=now,
            drift_score=self._last_drift,
            drift_status=DriftStatus.CORRECTION_APPLIED,
            correction_magnitude=correction_magnitude,
            correction_applied=True,
            threshold=self._threshold,
            hysteresis_band=self._hysteresis,
            k_p=self._k_p,
            model_version=self._model_version,
            cumulative_drift_energy=self._cumulative_drift_energy,
            drift_trend=self._compute_trend(),
        )
        self._last_snapshot = snap
        return snap

    def summary(self) -> dict:
        snap = self._last_snapshot
        return {
            "drift_score": snap.drift_score if snap else None,
            "drift_status": snap.drift_status.name if snap else None,
            "threshold": self._threshold,
            "hysteresis_band": self._hysteresis,
            "k_p": self._k_p,
            "model_version": self._model_version,
            "correction_count": self._correction_count,
            "cumulative_drift_energy": round(self._cumulative_drift_energy, 4),
            "drift_trend": snap.drift_trend if snap else None,
        }

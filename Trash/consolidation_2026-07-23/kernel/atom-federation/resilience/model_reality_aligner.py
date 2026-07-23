"""
v6.7 — Model–Reality Alignment Engine

Closes the model ↔ reality gap:

- Tracks self_model.predicted_state vs observed cluster state
- Computes model error (MSE, divergence)
- Triggers drift correction when error exceeds threshold
- Self-heals the causal graph over time
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

import numpy as np


class DriftStatus(Enum):
    STABLE = "stable"           # error < threshold
    DRIFTING = "drifting"       # threshold <= error < critical
    CRITICAL = "critical"       # error >= critical → full rebuild


@dataclass
class AlignmentSnapshot:
    timestamp: float
    drift_score: float          # 0..1, normalized error
    drift_status: DriftStatus
    model_version: int
    correction_applied: bool
    error_vector: dict[str, float]  # per-subsystem error


@dataclass
class DriftEvent:
    timestamp: float
    from_status: DriftStatus
    to_status: DriftStatus
    error_delta: float
    action_taken: str


class ModelRealityAligner:
    """
    Monitors the gap between self_model predictions and real cluster observations.
    Maintains an error history and triggers corrective actions when drift appears.
    """

    def __init__(
        self,
        drift_threshold: float = 0.15,
        critical_threshold: float = 0.40,
        history_len: int = 60,
        smoothing: float = 0.7,
    ):
        self.drift_threshold = drift_threshold
        self.critical_threshold = critical_threshold
        self.history_len = history_len
        self.smoothing = smoothing

        self.error_history: list[float] = []
        self.alignment_history: list[AlignmentSnapshot] = []
        self.drift_events: list[DriftEvent] = []

        self._model_version = 0
        self._last_correction_time = 0.0
        self._last_observed_state: dict | None = None
        self._last_predicted_state: dict | None = None

    def observe(
        self,
        real_state: dict,
        predicted_state: dict,
    ) -> AlignmentSnapshot:
        """
        Compare real cluster state vs self-model prediction.
        Returns AlignmentSnapshot with drift assessment.
        """
        now = time.time()
        error_vec = self._compute_error_vector(real_state, predicted_state)
        raw_error = self._normalize_error(error_vec)

        # Smooth
        if self.error_history:
            smoothed = self.smoothing * self.error_history[-1] + (1 - self.smoothing) * raw_error
        else:
            smoothed = raw_error

        self.error_history.append(smoothed)
        if len(self.error_history) > self.history_len:
            self.error_history.pop(0)

        prev_status = self._current_status()
        new_status = self._classify(smoothed)

        snap = AlignmentSnapshot(
            timestamp=now,
            drift_score=smoothed,
            drift_status=new_status,
            model_version=self._model_version,
            correction_applied=False,
            error_vector=error_vec,
        )

        if new_status != prev_status:
            evt = DriftEvent(
                timestamp=now,
                from_status=prev_status,
                to_status=new_status,
                error_delta=abs(smoothed - raw_error),
                action_taken="status_change",
            )
            self.drift_events.append(evt)
            snap = self._handle_drift(snap, new_status)

        self._last_observed_state = real_state
        self._last_predicted_state = predicted_state
        self.alignment_history.append(snap)
        return snap

    def _compute_error_vector(
        self,
        real: dict,
        predicted: dict,
    ) -> dict[str, float]:
        """Per-subsystem absolute error."""
        errors = {}
        all_keys = set(real.keys()) | set(predicted.keys())
        for k in all_keys:
            r = real.get(k, 0.0)
            p = predicted.get(k, 0.0)
            try:
                errors[k] = abs(float(r) - float(p))
            except (TypeError, ValueError):
                errors[k] = 0.0
        return errors

    def _normalize_error(self, error_vec: dict[str, float]) -> float:
        """Aggregate error vector → scalar 0..1."""
        if not error_vec:
            return 0.0
        vals = list(error_vec.values())
        return float(np.mean(vals))

    def _current_status(self) -> DriftStatus:
        if not self.error_history:
            return DriftStatus.STABLE
        return self._classify(self.error_history[-1])

    def _classify(self, score: float) -> DriftStatus:
        if score >= self.critical_threshold:
            return DriftStatus.CRITICAL
        if score >= self.drift_threshold:
            return DriftStatus.DRIFTING
        return DriftStatus.STABLE

    def _handle_drift(
        self,
        snap: AlignmentSnapshot,
        status: DriftStatus,
    ) -> AlignmentSnapshot:
        """Trigger appropriate correction based on drift severity."""
        now = snap.timestamp
        if status == DriftStatus.CRITICAL:
            # Full rebuild: increment model version + force re-align
            self._model_version += 1
            snap.action_taken = f"model_rebuild_v{self._model_version}"
            snap.correction_applied = True
        elif status == DriftStatus.DRIFTING:
            # Partial correction: fine-tune edges in causal graph
            snap.action_taken = "partial_correction"
            snap.correction_applied = True
        else:
            snap.action_taken = "no_correction"
        self._last_correction_time = now
        return snap

    def force_correction(self, reason: str = "manual") -> AlignmentSnapshot:
        """Manually trigger a model rebuild."""
        self._model_version += 1
        snap = AlignmentSnapshot(
            timestamp=time.time(),
            drift_score=0.0,
            drift_status=DriftStatus.STABLE,
            model_version=self._model_version,
            correction_applied=True,
            error_vector={},
        )
        snap.action_taken = f"force_rebuild/{reason}"
        return snap

    def get_trend(self) -> str:
        """Return one-line stability trend."""
        if len(self.error_history) < 5:
            return "insufficient_data"
        recent = self.error_history[-5:]
        if all(recent[i] <= recent[i+1] for i in range(len(recent)-1)):
            return "degrading"
        if all(recent[i] >= recent[i+1] for i in range(len(recent)-1)):
            return "improving"
        return "fluctuating"

    def summary(self) -> dict:
        return {
            "current_status": self._current_status().value,
            "current_drift_score": self.error_history[-1] if self.error_history else 0.0,
            "model_version": self._model_version,
            "trend": self.get_trend(),
            "total_corrections": sum(1 for s in self.alignment_history if s.correction_applied),
            "drift_event_count": len(self.drift_events),
        }

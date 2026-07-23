"""
v6.7 — Stability Eigenstate Detector

Finds and tracks stable attractor states (eigenstates) of the system.

- Observes state trajectory over time
- Detects when system enters a basin of attraction (eigenstate)
- Classifies eigenstates as: nominal / warning / critical
- Tracks transitions between eigenstates
- Predicts eigenstate transitions before they occur
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class EigenstateType(Enum):
    NOMINAL = "nominal"      # high stability, low stress
    WARNING = "warning"      # degraded but stable
    CRITICAL = "critical"   # near-instability basin
    UNKNOWN = "unknown"


@dataclass
class Eigenstate:
    id: str
    type: EigenstateType
    centroid: dict[str, float]        # average feature values
    radius: float                     # basin radius
    occupancy: int = 0                # how many times entered
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)


@dataclass
class TransitionEvent:
    timestamp: float
    from_id: str | None
    to_id: str
    confidence: float                  # 0..1
    predicted: bool = False


@dataclass
class EigenstateSnapshot:
    timestamp: float
    current_eigenstate: Eigenstate | None
    trajectory_variance: float         # how stable the trajectory is
    in_basin: bool
    transition_pending: str | None  # predicted next eigenstate


class EigenstateDetector:
    """
    Tracks the system state trajectory and identifies stable attractors.
    Works in three phases:
      1. Learning — builds eigenstate catalog from observation history
      2. Tracking — classifies current state into known eigenstates
      3. Prediction — warns when transition to a different eigenstate is likely
    """

    def __init__(
        self,
        n_features: int = 8,
        learning_window: int = 200,
        basin_threshold: float = 0.25,
        transition_lookahead: int = 10,
    ):
        self.n_features = n_features
        self.learning_window = learning_window
        self.basin_threshold = basin_threshold
        self.transition_lookahead = transition_lookahead

        self.state_buffer: deque[dict[str, float]] = deque(maxlen=learning_window)
        self.eigenstates: dict[str, Eigenstate] = {}
        self.transitions: list[TransitionEvent] = []
        self.transition_predictions: deque[TransitionEvent] = deque(maxlen=20)

        self._current_eigenstate_id: str | None = None
        self._model_ready = False
        self._next_eigenstate_id = 1

    def ingest(self, state_vector: dict[str, float]) -> None:
        """Add a state observation to the trajectory buffer."""
        self.state_buffer.append(state_vector)

    def _build_features(self, state: dict[str, float]) -> np.ndarray:
        """Convert state dict to feature vector."""
        vals = list(state.values())
        if len(vals) < self.n_features:
            vals += [0.0] * (self.n_features - len(vals))
        elif len(vals) > self.n_features:
            vals = vals[:self.n_features]
        return np.array(vals, dtype=np.float64)

    def _distance_to_eigenstate(self, feat: np.ndarray, es: Eigenstate) -> float:
        cent = self._build_features(es.centroid)
        return float(np.linalg.norm(feat - cent))

    def detect_current(self) -> EigenstateSnapshot:
        """
        Classify the current state.
        If model not ready → learn (create new eigenstate).
        If model ready → assign to nearest basin or create new one.
        """
        now = time.time()
        if len(self.state_buffer) < 10:
            return EigenstateSnapshot(
                timestamp=now,
                current_eigenstate=None,
                trajectory_variance=1.0,
                in_basin=False,
                transition_pending=None,
            )

        current_feat = self._build_features(self.state_buffer[-1])
        variance = self._compute_trajectory_variance()

        if not self._model_ready:
            # Learning phase: create eigenstate from current cluster
            es = self._learn_eigenstate(current_feat)
            self._current_eigenstate_id = es.id
            return EigenstateSnapshot(
                timestamp=now,
                current_eigenstate=es,
                trajectory_variance=variance,
                in_basin=True,
                transition_pending=None,
            )

        # Tracking phase: find nearest known eigenstate
        best_es: Eigenstate | None = None
        best_dist = float("inf")
        for es in self.eigenstates.values():
            d = self._distance_to_eigenstate(current_feat, es)
            if d < best_dist:
                best_dist = d
                best_es = es

        in_basin = best_es is not None and best_dist < best_es.radius

        if best_es is None or not in_basin:
            # New region → learn new eigenstate
            es = self._learn_eigenstate(current_feat)
            self._current_eigenstate_id = es.id
            return EigenstateSnapshot(
                timestamp=now,
                current_eigenstate=es,
                trajectory_variance=variance,
                in_basin=True,
                transition_pending=None,
            )

        # Check if we're leaving current basin (transition pending)
        pending = self._predict_transition(best_es.id, current_feat)

        if best_es.id != self._current_eigenstate_id:
            # Actual transition
            evt = TransitionEvent(
                timestamp=now,
                from_id=self._current_eigenstate_id,
                to_id=best_es.id,
                confidence=1.0 - (best_dist / best_es.radius),
                predicted=False,
            )
            self.transitions.append(evt)
            self._current_eigenstate_id = best_es.id

        best_es.last_seen = now
        return EigenstateSnapshot(
            timestamp=now,
            current_eigenstate=best_es,
            trajectory_variance=variance,
            in_basin=in_basin,
            transition_pending=pending,
        )

    def _learn_eigenstate(self, feat: np.ndarray) -> Eigenstate:
        """Create a new eigenstate from the current feature vector."""
        es_id = f"es_{self._next_eigenstate_id}"
        self._next_eigenstate_id += 1

        # Classify type based on feature values
        mean_val = float(np.mean(np.abs(feat)))
        if mean_val > 0.7:
            etype = EigenstateType.CRITICAL
        elif mean_val > 0.4:
            etype = EigenstateType.WARNING
        else:
            etype = EigenstateType.NOMINAL

        es = Eigenstate(
            id=es_id,
            type=etype,
            centroid={f"f{i}": float(v) for i, v in enumerate(feat)},
            radius=self.basin_threshold,
            occupancy=1,
        )
        self.eigenstates[es_id] = es

        if len(self.eigenstates) >= 3:
            self._model_ready = True

        return es

    def _compute_trajectory_variance(self) -> float:
        """Rolling-window variance of recent state features."""
        if len(self.state_buffer) < 5:
            return 1.0
        feats = np.array([self._build_features(s) for s in self.state_buffer])
        return float(np.var(feats))

    def _predict_transition(
        self,
        current_id: str,
        current_feat: np.ndarray,
    ) -> str | None:
        """Look at recent trajectory direction; predict next eigenstate."""
        if len(self.state_buffer) < self.transition_lookahead:
            return None

        recent = list(self.state_buffer)[-self.transition_lookahead:]
        # Compute mean velocity vector
        velocities = []
        for i in range(1, len(recent)):
            f_prev = self._build_features(recent[i-1])
            f_curr = self._build_features(recent[i])
            velocities.append(f_curr - f_prev)
        if not velocities:
            return None
        avg_velocity = np.mean(velocities, axis=0)
        # Project current state along velocity
        projected = current_feat + avg_velocity

        # Find eigenstate nearest to projected state
        best_es: Eigenstate | None = None
        best_dist = float("inf")
        for es_id, es in self.eigenstates.items():
            if es_id == current_id:
                continue
            d = self._distance_to_eigenstate(projected, es)
            if d < best_dist:
                best_dist = d
                best_es = es

        if best_es is not None:
            evt = TransitionEvent(
                timestamp=time.time(),
                from_id=current_id,
                to_id=best_es.id,
                confidence=0.6,
                predicted=True,
            )
            self.transition_predictions.append(evt)
            return best_es.id

        return None

    def get_current_id(self) -> str | None:
        return self._current_eigenstate_id

    def summary(self) -> dict:
        return {
            "eigenstate_count": len(self.eigenstates),
            "model_ready": self._model_ready,
            "current_eigenstate": self._current_eigenstate_id,
            "transition_count": len(self.transitions),
            "prediction_count": len(self.transition_predictions),
            "trajectory_buffer_size": len(self.state_buffer),
        }

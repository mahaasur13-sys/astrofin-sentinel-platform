"""Feedback Injection Loop — modifies future control surface distribution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class FeedbackSignalType(Enum):
    """Category of feedback signal from environment."""

    SUCCESS = "success"       # θ update improved objective
    DEGRADED = "degraded"     # θ update worsened objective marginally
    FAILED = "failed"        # θ update caused hard constraint violation
    OSCILLATION = "oscillation"  # pattern of alternating successes/failures
    PLATEAU = "plateau"       # diminishing returns on update magnitude


@dataclass
class FeedbackSignal:
    """Single feedback observation from environment."""

    signal_type: FeedbackSignalType
    episode_id: str
    timestamp: float  # wall-clock or sim time

    # Delta metrics at moment of feedback
    delta_norm_l2: float
    coherence_before: float
    coherence_after: float
    health_delta: float

    # Optional raw reward (controller-supplied)
    reward: float | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def is_improving(self) -> bool:
        return self.signal_type == FeedbackSignalType.SUCCESS

    @property
    def is_critical(self) -> bool:
        return self.signal_type in (
            FeedbackSignalType.FAILED,
            FeedbackSignalType.OSCILLATION,
        )


@dataclass
class ControlSurfaceModifier:
    """
    Maintains a learned distribution over future θ-space regions
    and adjusts it based on feedback signals.

    This is NOT a full RL credit-assignment loop — it is a lightweight
    heuristic modifier that biases future delta generation.
    """

    # Rolling window for signal history
    window_size: int = 20

    # Exploration bias parameters
    exploration_bonus: float = 0.05
    exploitation_bonus: float = 0.10

    # Oscillation dampening
    oscillation_penalty: float = 0.15

    # History
    _signals: list[FeedbackSignal] = field(default_factory=list, init=False)
    _recent_deltas: list[np.ndarray] = field(default_factory=list, init=False)
    _direction_history: list[int] = field(default_factory=list, init=False)
    _last_theta: np.ndarray | None = field(default=None, init=False)

    # ── Public API ─────────────────────────────────────────────────────────

    def ingest(self, signal: FeedbackSignal, tick: int = 0) -> None:
        """Record a feedback signal and update internal distribution."""
        self._signals.append(signal)
        if len(self._signals) > self.window_size:
            self._signals.pop(0)

        # Detect oscillation from alternating direction signs
        if self._last_theta is not None and signal.signal_type != FeedbackSignalType.OSCILLATION:
            sign = 1 if signal.coherence_after >= signal.coherence_before else -1
            self._direction_history.append(sign)
            if len(self._direction_history) > 6:
                self._direction_history.pop(0)
        # Always update _last_theta for next signal's direction detection
        self._last_theta = signal.delta_norm_l2  # store magnitude as proxy

    def get_exploration_bias(self, mutation_class) -> tuple[float, float]:
        """
        Returns (exploration_scale, exploitation_scale) multipliers
        to bias the next delta generation.

        Higher EXPLOITATION_BONUS → exploit known-good θ regions
        Higher EXPLORATION_BONUS  → explore uncertain regions
        """
        if not self._signals:
            return (self.exploration_bonus, 0.0)

        recent = self._signals[-5:]
        successes = sum(1 for s in recent if s.is_improving)
        success_rate = successes / max(len(recent), 1)

        if success_rate >= 0.7:
            # Exploit known-good direction
            return (self.exploration_bonus * 0.5, self.exploitation_bonus)
        elif success_rate <= 0.3:
            # Recover — increase exploration
            return (self.exploration_bonus * 2.0, 0.0)
        else:
            return (self.exploration_bonus, self.exploitation_bonus * 0.5)

    def oscillation_detected(self) -> bool:
        """Returns True if oscillation pattern is detected."""
        if len(self._direction_history) < 4:
            return False

        signs = self._direction_history[-6:]
        # Alternating signs: + - + - or - + - +
        alternating = all(signs[i] != signs[i + 1] for i in range(len(signs) - 1))
        return alternating

    def dampen_oscillation(self, delta: np.ndarray) -> np.ndarray:
        """Apply oscillation penalty to delta (scales magnitude down)."""
        if self.oscillation_detected():
            return delta * (1.0 - self.oscillation_penalty)
        return delta

    def recent_success_rate(self) -> float:
        """Rolling success rate over the signal window."""
        if not self._signals:
            return 0.0
        recent = self._signals[-self.window_size :]
        successes = sum(1 for s in recent if s.is_improving)
        return successes / len(recent)

    def signal_summary(self) -> dict:
        """Human-readable summary of recent signal history."""
        if not self._signals:
            return {"status": "no_signals", "window_size": self.window_size}

        recent = self._signals[-self.window_size :]
        counts = {st.value: 0 for st in FeedbackSignalType}
        for s in recent:
            counts[s.signal_type.value] = counts.get(s.signal_type.value, 0) + 1

        return {
            "window_size": self.window_size,
            "signal_counts": counts,
            "success_rate": self.recent_success_rate(),
            "oscillation_active": self.oscillation_detected(),
            "last_signal": recent[-1].signal_type.value,
        }


class FeedbackInjectionLoop:
    """
    Orchestrates feedback → bias → delta modification loop.

    Receives raw environment signals → feeds through ControlSurfaceModifier
    → produces bias modifiers → MutationExecutor applies biased deltas.
    """

    def __init__(self, modifier: ControlSurfaceModifier | None = None):
        self._modifier = modifier or ControlSurfaceModifier()

    @property
    def modifier(self) -> ControlSurfaceModifier:
        return self._modifier

    def receive(self, signal: FeedbackSignal) -> None:
        """Ingest a new feedback signal."""
        self._modifier.ingest(signal)

    def compute_biased_delta(
        self, base_delta: np.ndarray, mutation_class, tick: int = 0
    ) -> np.ndarray:
        """
        Takes a base delta (from MutationExecutor._generate_delta)
        and applies learned biases to return a modified delta.

        Bias pipeline:
          1. Exploration/exploitation reweighting
          2. Oscillation dampening
          3. Health-based scaling
        """
        expl, exp = self._modifier.get_exploration_bias(mutation_class)

        biased = base_delta.copy()
        # Reweight: EXPLOITATION bonus increases magnitude in "good" direction
        biased *= 1.0 + exp

        # Exploration bonus adds small noise in orthogonal directions
        if expl > 0:
            # FIX-3: Deterministic noise — same tick → same noise vector
            rng = np.random.default_rng(seed=tick)
            noise = rng.standard_normal(biased.shape) * expl * np.std(base_delta)
            biased += noise

        # Oscillation dampening
        biased = self._modifier.dampen_oscillation(biased)

        return biased

    def summary(self) -> dict:
        """Get current state of the feedback loop."""
        return self._modifier.signal_summary()

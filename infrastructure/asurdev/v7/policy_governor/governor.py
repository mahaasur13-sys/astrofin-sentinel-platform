#!/usr/bin/env python3
"""
Policy Governor (PUG) — stabilizes policy updates to prevent oscillation.
Fixes feedback loop instability: ML updates → policy lag → oscillation.

P_t = (1 - α) * P_{t-1} + α * P_new
Confidence-weighted updates + rate-limiting.
"""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np


@dataclass
class PolicySnapshot:
    """Immutable policy state at a point in time."""
    timestamp: datetime
    alpha: float      # throughput weight
    beta: float       # reliability weight
    gamma: float      # latency weight
    delta: float      # energy weight
    risk_threshold: float
    admission_policy: str
    confidence: float = 1.0   # how certain about this policy
    regret_smoothed: float = 0.0
    update_source: str = "init"


@dataclass
class PolicyUpdate:
    """Raw policy update from optimizer or meta-learner."""
    alpha: float
    beta: float
    gamma: float
    delta: float
    risk_threshold: float
    admission_policy: str
    confidence: float
    delta_regret: float    # change in regret that triggered this update
    source: str            # "optimizer" | "meta_learner" | "manual"


class PolicyGovernor:
    """
    EMA-based policy stabilizer.
    Prevents oscillation from feedback loops.
    """

    def __init__(
        self,
        alpha: float = 0.1,
        min_confidence: float = 0.3,
        regret_threshold: float = 0.05,
        max_update_rate: float = 0.2,
        smoothing_factor: float = 0.05,
    ):
        """
        Args:
            alpha: EMA smoothing factor (0.1 = slow, 0.5 = fast)
            min_confidence: below this, updates are suppressed
            regret_threshold: minimum Δregret to trigger update
            max_update_rate: max weight change per update
            smoothing_factor: EMA for regret signal smoothing
        """
        self.alpha = alpha
        self.min_confidence = min_confidence
        self.regret_threshold = regret_threshold
        self.max_update_rate = max_update_rate
        self.smoothing_factor = smoothing_factor

        self._current: Optional[PolicySnapshot] = None
        self._history: list[PolicySnapshot] = []
        self._pending_update: Optional[PolicyUpdate] = None

    def initialize(
        self,
        alpha: float = 0.4,
        beta: float = 0.3,
        gamma: float = 0.15,
        delta: float = 0.15,
        risk_threshold: float = 0.3,
        admission_policy: str = "probabilistic",
    ) -> PolicySnapshot:
        """Bootstrap initial policy."""
        self._current = PolicySnapshot(
            timestamp=datetime.utcnow(),
            alpha=alpha, beta=beta, gamma=gamma, delta=delta,
            risk_threshold=risk_threshold,
            admission_policy=admission_policy,
            confidence=1.0,
            regret_smoothed=0.0,
            update_source="init",
        )
        self._history.append(self._current)
        return self._current

    def receive_update(self, update: PolicyUpdate) -> bool:
        """
        Queue a policy update for next cycle.
        Returns True if update passes stability checks.
        """
        # Suppress low-confidence updates
        if update.confidence < self.min_confidence:
            return False

        # Rate-limit: max weight change per update
        if self._current:
            max_delta = self.max_update_rate
            for attr in ("alpha", "beta", "gamma", "delta"):
                delta = abs(getattr(update, attr) - getattr(self._current, attr))
                if delta > max_delta:
                    # Clamp the update
                    current_val = getattr(self._current, attr)
                    sign = 1 if getattr(update, attr) > current_val else -1
                    setattr(update, attr, current_val + sign * max_delta)

        # Only accept if Δregret exceeds threshold (reduces oscillation)
        if abs(update.delta_regret) < self.regret_threshold:
            return False

        self._pending_update = update
        return True

    def apply_update(self, regret_signal: float) -> PolicySnapshot:
        """
        Apply pending update using EMA smoothing.
        P_t = (1 - α) * P_{t-1} + α * P_new
        """
        if not self._pending_update or not self._current:
            return self._current

        u = self._pending_update

        # Smooth regret signal (EMA)
        new_regret = self.smoothing_factor * regret_signal + (1 - self.smoothing_factor) * self._current.regret_smoothed

        # EMA policy blend
        new_snapshot = PolicySnapshot(
            timestamp=datetime.utcnow(),
            alpha=self._ema(self._current.alpha, u.alpha),
            beta=self._ema(self._current.beta, u.beta),
            gamma=self._ema(self._current.gamma, u.gamma),
            delta=self._ema(self._current.delta, u.delta),
            risk_threshold=self._ema(self._current.risk_threshold, u.risk_threshold),
            admission_policy=u.admission_policy if u.confidence > 0.8 else self._current.admission_policy,
            confidence=u.confidence,
            regret_smoothed=new_regret,
            update_source=u.source,
        )

        self._current = new_snapshot
        self._history.append(new_snapshot)
        self._pending_update = None
        return new_snapshot

    def _ema(self, current: float, new: float) -> float:
        """Exponential moving average."""
        return (1 - self.alpha) * current + self.alpha * new

    def get_current(self) -> Optional[PolicySnapshot]:
        return self._current

    def get_history(self, last_n: Optional[int] = None) -> list[PolicySnapshot]:
        """Return policy history, most recent first."""
        history = sorted(self._history, key=lambda p: p.timestamp, reverse=True)
        return history[:last_n] if last_n else history

    def is_stable(self, window: int = 5) -> bool:
        """
        Check if policy has stabilized (low variance in recent history).
        """
        if len(self._history) < window:
            return False
        recent = self._history[-window:]
        alpha_std = np.std([p.alpha for p in recent])
        return alpha_std < 0.02

    def force_update(self, new_policy: PolicyUpdate) -> PolicySnapshot:
        """Force update bypassing stability checks (for critical retraining)."""
        if not self._current:
            return self.initialize(
                alpha=new_policy.alpha, beta=new_policy.beta,
                gamma=new_policy.gamma, delta=new_policy.delta,
                risk_threshold=new_policy.risk_threshold,
                admission_policy=new_policy.admission_policy,
            )
        self._current = PolicySnapshot(
            timestamp=datetime.utcnow(),
            alpha=new_policy.alpha, beta=new_policy.beta,
            gamma=new_policy.gamma, delta=new_policy.delta,
            risk_threshold=new_policy.risk_threshold,
            admission_policy=new_policy.admission_policy,
            confidence=new_policy.confidence,
            regret_smoothed=self._current.regret_smoothed,
            update_source=f"forced_{new_policy.source}",
        )
        self._history.append(self._current)
        return self._current
"""
v6.7 — Objective Stability Governor

Prevents J-gate oscillation under stress conditions.

Problem: J(t) oscillates under high variance / adversarial conditions
  → AdaptiveObjectiveController.execute() may flap between allow/deny

Solution:
  - Tracks J history with a moving window
  - Detects oscillatory patterns (sign changes, amplitude growth)
  - Enforces monotonic progression: if oscillating → damp + slow down
  - Three enforcement modes: OFF / DAMPED / STRICT
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum


class GovernorMode(Enum):
    OFF = "off"
    DAMPED = "damped"
    STRICT = "strict"


@dataclass
class JWindow:
    timestamps: list[float]
    values: list[float]

    def append(self, t: float, v: float) -> None:
        self.timestamps.append(t)
        self.values.append(v)

    def last(self, n: int = 1) -> list[float]:
        return self.values[-n:] if len(self.values) >= n else self.values

    def window(self, n: int) -> list[float]:
        return self.values[-n:] if len(self.values) >= n else self.values


@dataclass
class OscillationReport:
    detected: bool
    mode: GovernorMode
    amplitude: float
    frequency: float          # sign changes per second
    monotonic_violation: bool
    damping_applied: float    # 0.0 = no damping, 1.0 = full block
    enforced_value: float     # damped J value


@dataclass
class GovernorDecision:
    allowed: bool
    confidence: float          # 0..1
    oscillation_report: OscillationReport
    raw_J: float
    enforced_J: float


class ObjectiveStabilityGovernor:
    """
    Wraps the J-gate with oscillation detection and dampening.

    In STRICT mode: blocks actions that would make J non-monotonic.
    In DAMPED mode: reduces confidence of oscillatory actions.
    In OFF mode: transparent pass-through.
    """

    def __init__(
        self,
        window_size: int = 30,
        amplitude_threshold: float = 0.10,
        frequency_threshold: float = 2.0,   # sign changes / second
        damping_factor: float = 0.5,
        mode: GovernorMode = GovernorMode.DAMPED,
    ):
        self.window_size = window_size
        self.amplitude_threshold = amplitude_threshold
        self.frequency_threshold = frequency_threshold
        self.damping_factor = damping_factor
        self.mode = mode

        self.history = JWindow([], [])

    def evaluate(self, raw_J: float, confidence: float = 1.0) -> GovernorDecision:
        """Evaluate a J-gate decision with oscillation protection."""
        now = time.time()
        self.history.append(now, raw_J)

        if self.mode == GovernorMode.OFF:
            report = OscillationReport(
                detected=False,
                mode=self.mode,
                amplitude=0.0,
                frequency=0.0,
                monotonic_violation=False,
                damping_applied=0.0,
                enforced_value=raw_J,
            )
            return GovernorDecision(
                allowed=True,
                confidence=confidence,
                oscillation_report=report,
                raw_J=raw_J,
                enforced_J=raw_J,
            )

        report = self._detect_oscillation(now)

        if not report.detected:
            enforced_J = raw_J
            new_confidence = confidence
        elif self.mode == GovernorMode.STRICT:
            # Strict: block non-monotonic if amplitude is high
            if report.monotonic_violation and report.amplitude > self.amplitude_threshold:
                enforced_J = raw_J
                new_confidence = 0.0   # fully blocked
            else:
                enforced_J = raw_J
                new_confidence = confidence * (1.0 - report.damping_applied)
        else:  # DAMPED
            enforced_J = raw_J * (1.0 - report.damping_applied)
            new_confidence = confidence * (1.0 - report.damping_applied)

        allowed = new_confidence > 0.0 and enforced_J > 0.0

        return GovernorDecision(
            allowed=allowed,
            confidence=new_confidence,
            oscillation_report=report,
            raw_J=raw_J,
            enforced_J=enforced_J,
        )

    def _detect_oscillation(self, now: float) -> OscillationReport:
        w = self.history.window(self.window_size)
        if len(w) < 4:
            return OscillationReport(
                detected=False,
                mode=self.mode,
                amplitude=0.0,
                frequency=0.0,
                monotonic_violation=False,
                damping_applied=0.0,
                enforced_value=self.history.values[-1] if self.history.values else 0.0,
            )

        # Amplitude: max - min in window
        amplitude = max(w) - min(w)

        # Sign changes
        signs = [1 if v > 0 else -1 for v in w]
        sign_changes = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i-1])

        # Duration of window
        times = self.history.timestamps
        duration = times[-1] - times[0] if len(times) >= 2 else 1.0
        frequency = sign_changes / max(duration, 0.1)

        # Monotonic violation: check if J is consistently decreasing
        is_decreasing = all(w[i] >= w[i+1] for i in range(len(w)-1))
        is_increasing = all(w[i] <= w[i+1] for i in range(len(w)-1))
        monotonic_violation = not is_decreasing and not is_increasing and amplitude > self.amplitude_threshold

        # Damping
        oscillating = frequency > self.frequency_threshold or monotonic_violation
        damping = self.damping_factor if oscillating else 0.0

        return OscillationReport(
            detected=oscillating,
            mode=self.mode,
            amplitude=amplitude,
            frequency=frequency,
            monotonic_violation=monotonic_violation,
            damping_applied=damping,
            enforced_value=w[-1] * (1.0 - damping),
        )

    def set_mode(self, mode: GovernorMode) -> None:
        self.mode = mode

    def summary(self) -> dict:
        w = self.history.window(self.window_size)
        return {
            "mode": self.mode.value,
            "history_size": len(self.history.values),
            "current_J": self.history.values[-1] if self.history.values else 0.0,
            "amplitude": max(w) - min(w) if len(w) >= 2 else 0.0,
            "window_size": self.window_size,
        }

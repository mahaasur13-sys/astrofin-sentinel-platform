"""
Stability Feedback Controller — v7.4
Prevents oscillation collapse: ensures the system does not over-correct.

The oscillation problem:
  actuator applies correction → system responds →
  response triggers new correction → over-correct →
  oscillation / divergence collapse

The controller implements a damped feedback loop:
  observed_gain vs expected_gain → adaptive gain adjustment →
  oscillation detection → mode switch to dampen.

This is analogous to a PID controller's derivative term,
preventing the system from going into resonance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto


class OscillationMode(Enum):
    NORMAL = auto()       # no oscillation, standard proportional control
    WARNING = auto()      # slight oscillation detected, increase damping
    OSCILLATING = auto()  # oscillation confirmed, switch to dampen mode
    SATURATED = auto()    # control authority at max, can't correct further
    COLLAPSED = auto()    # oscillation led to divergence — emergency stop


@dataclass
class StabilityState:
    """
    Current stability state of the feedback loop.
    """
    mode: OscillationMode = OscillationMode.NORMAL
    oscillation_index: float = 0.0       # 0=stable, 1=oscillating
    damping_factor: float = 1.0          # multiplicative gain reducer (< 1 = dampen)
    adaptive_gain: float = 1.0          # current adaptive gain multiplier
    overshoot_count: int = 0             # number of overshoot events
    undershoot_count: int = 0            # number of undershoot events
    last_gain_adjustment: float = 0.0    # last gain delta applied
    correction_saturation: float = 0.0   # 0..1 how close to max control authority


@dataclass
class GainAdjustment:
    """
    A computed gain adjustment to apply to the actuator.
    """
    new_adaptive_gain: float
    damping_factor: float
    oscillation_mode: OscillationMode
    reasoning: str
    apply_to_commands: bool  # if True, modify command magnitudes before execution


@dataclass
class StabilityFeedbackController:
    """
    Damped feedback controller for the actuator layer.

    Monitors the error signal (actual_gain vs expected_gain) over time
    and detects oscillation patterns. When oscillation is detected,
    it transitions to a dampen mode that reduces control authority.

    The key shift from having no controller:
      No controller:     apply command → observe result → apply command →
                         → over-correction → oscillation collapse
      With controller:   apply command → observe result →
                         → detect oscillation → dampen → stable convergence

    Design constraints:
      - Damping should never go below 0.1 (system would be uncontrollable)
      - Adaptive gain converges to 1.0 when stable (full authority restored)
      - Oscillation detection uses a rolling window of gain observations
    """

    def __init__(
        self,
        damping_coeff: float = 0.7,        # how aggressively to dampen (0..1)
        oscillation_window: int = 8,        # number of observations for oscillation detection
        overshoot_threshold: float = 1.2,   # gain > expected * threshold → overshoot
        undershoot_threshold: float = 0.3,  # gain < expected * threshold → undershoot
        convergence_threshold: float = 0.02, # |gain - expected| < threshold → stable
        max_damping_factor: float = 1.0,
        min_damping_factor: float = 0.1,
    ):
        self.damping_coeff = damping_coeff
        self.oscillation_window = oscillation_window
        self.overshoot_threshold = overshoot_threshold
        self.undershoot_threshold = undershoot_threshold
        self.convergence_threshold = convergence_threshold
        self.max_damping_factor = max_damping_factor
        self.min_damping_factor = min_damping_factor

        # Internal state
        self.state = StabilityState()
        self._gain_history: list[float] = []       # actual_gain / expected_gain ratio
        self._coherence_history: list[float] = []   # rolling coherence values
        self._gain_history_ts: list[int] = []       # timestamps
        self._saturation_history: list[float] = []  # control saturation values

    def observe(
        self,
        expected_gain: float,
        actual_gain: float,
        current_coherence: float,
        control_saturation: float,
        timestamp_ms: int,
    ) -> StabilityState:
        """
        Observe the result of a control action and update stability state.

        Args:
            expected_gain: what we expected to gain in coherence
            actual_gain: what we actually gained
            current_coherence: new global coherence after the action
            control_saturation: how close control authority is to max (0..1)
            timestamp_ms: current time

        Returns:
            Updated StabilityState.
        """
        # Record history
        self._coherence_history.append(current_coherence)
        if len(self._coherence_history) > self.oscillation_window * 2:
            self._coherence_history = self._coherence_history[-self.oscillation_window * 2:]

        self._saturation_history.append(control_saturation)
        if len(self._saturation_history) > self.oscillation_window:
            self._saturation_history = self._saturation_history[-self.oscillation_window:]

        # Compute gain ratio (avoid div by zero)
        if abs(expected_gain) < 1e-9:
            gain_ratio = 1.0 if abs(actual_gain) < 1e-9 else float("inf")
        else:
            gain_ratio = actual_gain / expected_gain

        self._gain_history.append(gain_ratio)
        self._gain_history_ts.append(timestamp_ms)
        if len(self._gain_history) > self.oscillation_window:
            self._gain_history = self._gain_history[-self.oscillation_window:]
            self._gain_history_ts = self._gain_history_ts[-self.oscillation_window:]

        # Update oscillation index (0=stable, 1=oscillating)
        oscillation_index = self._compute_oscillation_index()
        self.state.oscillation_index = oscillation_index

        # Detect overshoot / undershoot
        if gain_ratio > self.overshoot_threshold:
            self.state.overshoot_count += 1
        elif gain_ratio < self.undershoot_threshold:
            self.state.undershoot_count += 1

        # Update damping factor
        new_damping = self._compute_damping(oscillation_index)
        self.state.damping_factor = new_damping

        # Adaptive gain: reduce when oscillating, restore when stable
        new_adaptive_gain = self._compute_adaptive_gain(
            oscillation_index, current_coherence, gain_ratio
        )
        self.state.adaptive_gain = new_adaptive_gain

        # Determine mode
        self.state.mode = self._determine_mode(
            oscillation_index, control_saturation, gain_ratio
        )
        self.state.correction_saturation = control_saturation

        return self.state

    def compute_gain_adjustment(
        self,
        commands: list[Any],  # List[ActuatorCommand from causal_actuation_engine]
        expected_total_gain: float,
    ) -> GainAdjustment:
        """
        Given a set of actuator commands and expected gain,
        compute gain adjustment and decide whether to modify magnitudes.

        Args:
            commands: current ActuatorCommands to be executed
            expected_total_gain: expected coherence gain from these commands

        Returns:
            GainAdjustment with new_adaptive_gain, damping_factor, reasoning.
        """
        reasoning_parts = []

        if self.state.mode == OscillationMode.COLLAPSED:
            return GainAdjustment(
                new_adaptive_gain=0.0,
                damping_factor=self.min_damping_factor,
                oscillation_mode=OscillationMode.COLLAPSED,
                reasoning="EMERGENCY STOP: oscillation collapse detected",
                apply_to_commands=True,
            )

        if self.state.mode == OscillationMode.OSCILLATING:
            reasoning_parts.append(
                f"oscillating detected (idx={self.state.oscillation_index:.3f}), reducing gain"
            )
            return GainAdjustment(
                new_adaptive_gain=self.state.adaptive_gain * self.damping_coeff,
                damping_factor=self.state.damping_factor,
                oscillation_mode=OscillationMode.OSCILLATING,
                reasoning="; ".join(reasoning_parts) or "oscillation mode",
                apply_to_commands=True,
            )

        if self.state.mode == OscillationMode.WARNING:
            reasoning_parts.append(
                f"slight oscillation (idx={self.state.oscillation_index:.3f})"
            )
            return GainAdjustment(
                new_adaptive_gain=self.state.adaptive_gain * math.sqrt(self.damping_coeff),
                damping_factor=self.state.damping_factor,
                oscillation_mode=OscillationMode.WARNING,
                reasoning="; ".join(reasoning_parts) or "warning mode",
                apply_to_commands=True,
            )

        if self.state.mode == OscillationMode.SATURATED:
            reasoning_parts.append(
                f"control saturated ({self.state.correction_saturation:.2f})"
            )
            return GainAdjustment(
                new_adaptive_gain=self.state.adaptive_gain * 0.5,
                damping_factor=self.state.damping_factor,
                oscillation_mode=OscillationMode.SATURATED,
                reasoning="; ".join(reasoning_parts) or "saturation mode",
                apply_to_commands=True,
            )

        # NORMAL mode — restore full adaptive gain toward 1.0
        reasoning_parts.append("stable, restoring adaptive gain")
        restored_gain = min(1.0, self.state.adaptive_gain * 1.05)
        self.state.adaptive_gain = restored_gain

        return GainAdjustment(
            new_adaptive_gain=restored_gain,
            damping_factor=self.state.damping_factor,
            oscillation_mode=OscillationMode.NORMAL,
            reasoning="; ".join(reasoning_parts) or "normal mode",
            apply_to_commands=False,
        )

    def apply_gain_to_commands(
        self,
        commands: list[Any],  # List[ActuatorCommand]
        adjustment: GainAdjustment,
    ) -> list[Any]:
        """
        Apply the gain adjustment to a list of commands.
        Modifies command magnitudes by multiplying by new_adaptive_gain * damping_factor.

        Returns modified commands (copy).
        """
        if not adjustment.apply_to_commands:
            return commands

        factor = adjustment.new_adaptive_gain * adjustment.damping_factor
        modified = []
        for cmd in commands:
            # Create a shallow copy with adjusted delta
            new_cmd = ActuatorCommandCopy(
                target_worker=cmd.target_worker,
                axis=cmd.axis,
                command_type=cmd.command_type,
                delta=cmd.delta * factor,
                causal_depth=cmd.causal_depth,
                priority=cmd.priority,
                reason=cmd.reason,
                expected_coherence_gain=cmd.expected_coherence_gain * factor,
                timestamp_ms=cmd.timestamp_ms,
            )
            modified.append(new_cmd)

        return modified

    def reset(self) -> None:
        """Reset the controller state (e.g., after a system reset)."""
        self.state = StabilityState()
        self._gain_history.clear()
        self._coherence_history.clear()
        self._gain_history_ts.clear()
        self._saturation_history.clear()

    # ─── Internal helpers ──────────────────────────────────────────────────────

    def _compute_oscillation_index(self) -> float:
        """
        Compute oscillation index from gain history.
        Uses sign changes and variance of gain ratios.
        A stable system has gain_ratio ≈ 1.0 (actual = expected).
        Oscillation: alternating overshoot/undershoot → sign changes in (gain_ratio - 1).

        Returns 0.0 (stable) .. 1.0 (oscillating).
        """
        if len(self._gain_history) < 3:
            return 0.0

        # Sign changes around 1.0
        deviations = [g - 1.0 for g in self._gain_history]
        sign_changes = 0
        for i in range(1, len(deviations)):
            if deviations[i] * deviations[i - 1] < 0:
                sign_changes += 1

        oscillation_from_signs = sign_changes / max(1, len(deviations) - 1)

        # Variance of deviations (high variance = oscillation)
        mean_d = sum(deviations) / len(deviations)
        variance = sum((d - mean_d) ** 2 for d in deviations) / len(deviations)
        # Normalize: variance > 1 is considered high oscillation
        oscillation_from_variance = min(1.0, math.sqrt(variance))

        # Combined: weighted average
        index = 0.4 * oscillation_from_signs + 0.6 * oscillation_from_variance
        return min(1.0, index)

    def _compute_damping(self, oscillation_index: float) -> float:
        """
        Compute damping factor based on oscillation index.
        High oscillation → low damping (reduce authority).
        """
        # damping_factor = 1 - oscillation_index * (1 - min_damping)
        damping = 1.0 - oscillation_index * (1.0 - self.min_damping_factor)
        return max(self.min_damping_factor, min(self.max_damping_factor, damping))

    def _compute_adaptive_gain(
        self,
        oscillation_index: float,
        current_coherence: float,
        gain_ratio: float,
    ) -> float:
        """
        Compute adaptive gain multiplier.
        Reduces gain when oscillating or oversaturated.
        Restores toward 1.0 when stable.
        """
        current = self.state.adaptive_gain

        if self.state.mode in (OscillationMode.OSCILLATING, OscillationMode.COLLAPSED):
            # Rapid reduction
            return max(0.05, current * self.damping_coeff ** 2)

        if self.state.mode == OscillationMode.WARNING:
            return max(0.2, current * self.damping_coeff)

        if self.state.mode == OscillationMode.SATURATED:
            return max(0.1, current * 0.5)

        # NORMAL: converge toward 1.0
        if current < 1.0:
            return min(1.0, current * 1.02)  # slowly restore
        elif current > 1.0:
            return max(1.0, current * 0.99)

        return 1.0

    def _determine_mode(
        self,
        oscillation_index: float,
        saturation: float,
        gain_ratio: float,
    ) -> OscillationMode:
        if oscillation_index >= 0.7 or gain_ratio == float("inf"):
            return OscillationMode.COLLAPSED
        if oscillation_index >= 0.4:
            return OscillationMode.OSCILLATING
        if oscillation_index >= 0.2:
            return OscillationMode.WARNING
        if saturation >= 0.95:
            return OscillationMode.SATURATED
        return OscillationMode.NORMAL


# ─── Helper for command copy ──────────────────────────────────────────────────

@dataclass
class ActuatorCommandCopy:
    """Shallow copy of ActuatorCommand with modified delta/gain."""
    target_worker: str
    axis: str
    command_type: str
    delta: float
    causal_depth: int
    priority: int
    reason: str
    expected_coherence_gain: float
    timestamp_ms: int

"""
Causal Actuation Engine — v7.4
Maps divergence field (from swarm/swarm_divergence_field.py) → corrective actions.

The closed loop:
  SwarmDivergenceField
    → ActuationSignal (direction + magnitude of corrective force)
      → ActuatorCommand (specific command to specific worker/node)
        → system dynamics update
          → new SwarmDivergenceField (feedback)

Key concept: corrective actions are CAUSAL interventions, not just config changes.
A causal intervention reshapes the causal manifold itself, not just parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class ActuationDirection(Enum):
    PULL_TOGETHER = auto()   # reduce divergence → pull workers toward shared state
    PUSH_APART = auto()      # intentionally increase separation (anti-correlation)
    REBALANCE = auto()       # redistribute load/authority across workers
    RESET = auto()           # hard reset specific axis to canonical state
    STABILIZE = auto()       # dampen oscillation / slow dynamics


class ActuationSeverity(Enum):
    NANOSCALE = 1    # micro-correction, no state change
    MICRO = 2        # small parameter shift
    MESO = 3         # moderate structural change
    MACRO = 4       # large intervention, significant state change
    CRITICAL = 5    # emergency, potential data loss


@dataclass
class ActuationSignal:
    """
    Represents the direction and magnitude of corrective force needed
    to restore swarm coherence.
    """
    most_divergent_axis: str
    most_divergent_pair: tuple[str, str]
    direction: ActuationDirection
    severity: ActuationSeverity
    required_coherence_gain: float   # how much global_coherence must improve (0..1)
    involved_workers: list[str]
    causal_depth_affected: int        # how deep in causal DAG the intervention goes
    timestamp_ms: int


@dataclass
class ActuatorCommand:
    """
    A concrete, executable command targeting a specific worker.
    """
    target_worker: str
    axis: str
    command_type: str          # "shift_state" | "reproject" | "rebalance" | "reset" | "dampen"
    delta: float               # magnitude of shift
    causal_depth: int
    priority: int              # 1=highest, 5=lowest
    reason: str                # human-readable justification
    expected_coherence_gain: float
    timestamp_ms: int


@dataclass
class ActuationResult:
    """
    Result of applying an ActuatorCommand to the swarm.
    """
    command: ActuatorCommand
    applied: bool
    coherence_gain_actual: float
    new_global_coherence: float
    workers_affected: list[str]
    oscillation_detected: bool
    messages: list[str]


class CausalActuationEngine:
    """
    Core engine that translates divergence field measurements
    into executable actuator commands.

    The key shift from v7.3:
      v7.3: observe and measure divergence field
      v7.4: ACT on the divergence field to reshape system dynamics

    The engine does NOT execute commands — it generates them.
    Execution is the responsibility of the swarm runtime.

    Design rules:
      1. Minimal intervention: never do at MACRO what can be done at MICRO
      2. Causal depth awareness: interventions affect shallow depth first
      3. Coherence-gain tracking: every command has an expected gain
      4. Oscillation detection: flag if correction overshoots
    """

    def __init__(self, causal_dimensions: list[str]):
        self.causal_dimensions = causal_dimensions

    def compute_actuation_signals(
        self,
        global_coherence: float,
        field_severity: Any,  # FieldSeverity from swarm_divergence_field
        most_divergent_axis: str,
        most_divergent_pair: tuple[str, str],
        timestamp_ms: int,
    ) -> list[ActuationSignal]:
        """
        Convert a snapshot of the divergence field into actuation signals.

        Args:
            global_coherence: current global coherence (0..1)
            field_severity: FieldSeverity enum value
            most_divergent_axis: which axis has highest divergence
            most_divergent_pair: (worker_id, worker_id) with highest flux
            timestamp_ms: current time

        Returns:
            List of ActuationSignal, one per intervention needed.
            Empty list if coherence >= 0.95 (no action needed).
        """
        if global_coherence >= 0.95:
            return []

        signals: list[ActuationSignal] = []

        # Determine direction and severity based on field_severity
        severity_map = {
            "IDENTICAL": (None, ActuationSeverity.NANOSCALE),
            "MINOR": (ActuationDirection.PULL_TOGETHER, ActuationSeverity.MICRO),
            "MODERATE": (ActuationDirection.PULL_TOGETHER, ActuationSeverity.MESO),
            "SEVERE": (ActuationDirection.REBALANCE, ActuationSeverity.MACRO),
            "CRITICAL": (ActuationDirection.RESET, ActuationSeverity.CRITICAL),
        }

        direction, act_severity = severity_map.get(
            field_severity.name if hasattr(field_severity, "name") else str(field_severity),
            (ActuationDirection.PULL_TOGETHER, ActuationSeverity.MICRO),
        )

        if direction is None:
            return []

        # Target: bring global_coherence to 0.95 or higher
        required_gain = max(0.0, 0.95 - global_coherence)

        signals.append(ActuationSignal(
            most_divergent_axis=most_divergent_axis,
            most_divergent_pair=most_divergent_pair,
            direction=direction,
            severity=act_severity,
            required_coherence_gain=required_gain,
            involved_workers=list(most_divergent_pair),
            causal_depth_affected=self._depth_for_severity(act_severity),
            timestamp_ms=timestamp_ms,
        ))

        return signals

    def generate_commands(
        self,
        signal: ActuationSignal,
        current_axis_S: dict[str, float],
        canonical_S: dict[str, float] | None = None,
        timestamp_ms: int = 0,
    ) -> list[ActuatorCommand]:
        """
        Translate an ActuationSignal into concrete ActuatorCommands.

        Args:
            signal: the actuation signal to resolve
            current_axis_S: current S_full per axis
            canonical_S: canonical (target) S per axis (optional)
            timestamp_ms: current time

        Returns:
            List of ActuatorCommand to be executed by the swarm runtime.
        """
        commands: list[ActuatorCommand] = []

        if signal.direction == ActuationDirection.PULL_TOGETHER:
            # Small shift toward mean state
            for worker_id in signal.involved_workers:
                cmd_type, delta = self._pull_delta(
                    signal.most_divergent_axis,
                    current_axis_S,
                    canonical_S,
                )
                commands.append(ActuatorCommand(
                    target_worker=worker_id,
                    axis=signal.most_divergent_axis,
                    command_type=cmd_type,
                    delta=delta,
                    causal_depth=signal.causal_depth_affected,
                    priority=self._priority_for_severity(signal.severity),
                    reason=f"Pull worker {worker_id} toward canonical state on axis {signal.most_divergent_axis}",
                    expected_coherence_gain=signal.required_coherence_gain / len(signal.involved_workers),
                    timestamp_ms=timestamp_ms,
                ))

        elif signal.direction == ActuationDirection.REBALANCE:
            # Redistribute across all involved workers
            for worker_id in signal.involved_workers:
                commands.append(ActuatorCommand(
                    target_worker=worker_id,
                    axis=signal.most_divergent_axis,
                    command_type="rebalance",
                    delta=0.0,
                    causal_depth=signal.causal_depth_affected,
                    priority=self._priority_for_severity(signal.severity),
                    reason=f"Rebalance causal authority on axis {signal.most_divergent_axis}",
                    expected_coherence_gain=signal.required_coherence_gain / len(signal.involved_workers),
                    timestamp_ms=timestamp_ms,
                ))

        elif signal.direction == ActuationDirection.RESET:
            # Hard reset to canonical state
            for worker_id in signal.involved_workers:
                commands.append(ActuatorCommand(
                    target_worker=worker_id,
                    axis=signal.most_divergent_axis,
                    command_type="reset",
                    delta=canonical_S.get(signal.most_divergent_axis, 0.0) if canonical_S else 0.0,
                    causal_depth=3,  # deep reset
                    priority=1,       # highest priority
                    reason=f"CRITICAL: hard reset axis {signal.most_divergent_axis} for {worker_id}",
                    expected_coherence_gain=signal.required_coherence_gain,
                    timestamp_ms=timestamp_ms,
                ))

        elif signal.direction == ActuationDirection.STABILIZE:
            # Dampen oscillation
            for worker_id in signal.involved_workers:
                commands.append(ActuatorCommand(
                    target_worker=worker_id,
                    axis=signal.most_divergent_axis,
                    command_type="dampen",
                    delta=-0.1,  # reduce gain
                    causal_depth=1,
                    priority=2,
                    reason=f"Dampen oscillation on axis {signal.most_divergent_axis}",
                    expected_coherence_gain=0.01,
                    timestamp_ms=timestamp_ms,
                ))

        return commands

    def evaluate_actuation_result(
        self,
        command: ActuatorCommand,
        prev_coherence: float,
        new_coherence: float,
        oscillation_detected: bool = False,
    ) -> ActuationResult:
        """
        Evaluate the outcome of applying an ActuatorCommand.

        Returns ActuationResult with actual vs expected coherence gain.
        """
        actual_gain = new_coherence - prev_coherence
        return ActuationResult(
            command=command,
            applied=True,
            coherence_gain_actual=actual_gain,
            new_global_coherence=new_coherence,
            workers_affected=[command.target_worker],
            oscillation_detected=oscillation_detected,
            messages=self._result_messages(command, actual_gain, oscillation_detected),
        )

    # ─── Internal helpers ────────────────────────────────────────────────────

    @staticmethod
    def _depth_for_severity(severity: ActuationSeverity) -> int:
        mapping = {
            ActuationSeverity.NANOSCALE: 1,
            ActuationSeverity.MICRO: 1,
            ActuationSeverity.MESO: 2,
            ActuationSeverity.MACRO: 3,
            ActuationSeverity.CRITICAL: 5,
        }
        return mapping.get(severity, 2)

    @staticmethod
    def _priority_for_severity(severity: ActuationSeverity) -> int:
        mapping = {
            ActuationSeverity.NANOSCALE: 5,
            ActuationSeverity.MICRO: 4,
            ActuationSeverity.MESO: 3,
            ActuationSeverity.MACRO: 2,
            ActuationSeverity.CRITICAL: 1,
        }
        return mapping.get(severity, 3)

    @staticmethod
    def _pull_delta(
        axis: str,
        current_S: dict[str, float],
        canonical_S: dict[str, float] | None,
    ) -> tuple[str, float]:
        """
        Compute the magnitude and type of pull correction for an axis.
        Returns (command_type, delta).
        """
        current = current_S.get(axis, 0.0)
        if canonical_S is not None:
            canonical = canonical_S.get(axis, 0.0)
            delta = canonical - current
            return ("shift_state", delta)
        # No canonical — use mean-reversion heuristic
        return ("shift_state", -current * 0.1)  # small pull toward 0

    @staticmethod
    def _result_messages(
        command: ActuatorCommand,
        actual_gain: float,
        oscillation: bool,
    ) -> list[str]:
        msgs = []
        if actual_gain > 0:
            msgs.append(f"✓ Coherence improved by {actual_gain:.4f}")
        elif actual_gain == 0:
            msgs.append("○ Coherence unchanged")
        else:
            msgs.append(f"✗ Coherence decreased by {abs(actual_gain):.4f}")
        if oscillation:
            msgs.append("⚠ Oscillation detected — consider dampening")
        if abs(actual_gain) < 0.001:
            msgs.append("ℹ Gain below threshold — intervention may be saturated")
        return msgs

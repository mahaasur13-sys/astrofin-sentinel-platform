"""
Swarm Control Surface — v7.4
Maps global S_full (from distributed_tensor_alignment) → actuator command primitives.

This is the "control surface" through which the actuation layer
interfaces with the swarm runtime. It abstracts the physical act of
sending commands to workers as a unified interface.

Key concept:
  S_full is a metric (scalar). The control surface converts it into
  a control vector that can be applied to swarm dynamics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ControlPrimitive(Enum):
    """
    Atomic control operations available to the actuator.
    """
    STATE_SHIFT = auto()       # shift worker's internal state by delta
    REPROJECT = auto()         # reproject worker onto causal manifold
    REBALANCE = auto()         # rebalance causal authority load
    RESET = auto()             # reset to canonical baseline
    DAMPEN = auto()            # reduce gain / dampen oscillation
    ISOLATE = auto()           # isolate worker (quarantine)
    SYNC = auto()              # force sync with canonical
    ACCELERATE = auto()        # speed up worker dynamics
    DECELERATE = auto()        # slow down worker dynamics


@dataclass
class SwarmActuatorState:
    """
    Mutable state of the swarm control surface.
    Tracks pending commands, active corrections, and control history.
    """
    pending_commands: list[Any] = field(default_factory=list)
    active_corrections: dict[str, Any] = field(default_factory=dict)  # worker_id → correction
    command_history: list[Any] = field(default_factory=list)           # last N commands
    last_global_coherence: float = 1.0
    control_iteration: int = 0


@dataclass
class ControlVector:
    """
    A control vector for one worker on one axis.
    Analogous to a force vector in physics: direction + magnitude.
    """
    worker_id: str
    axis: str
    primitive: ControlPrimitive
    magnitude: float            # magnitude of the control action
    coherence_target: float     # S_full we expect to reach after this action
    confidence: float          # 0..1, how confident we are in this control action
    control_gain: float        # proportional gain coefficient
    timestamp_ms: int


@dataclass
class SwarmControlSurface:
    """
    The control surface maps a global coherence metric (S_full from v7.3)
    into a set of control vectors for individual workers.

    The surface provides:
      1. S_full → control vector decomposition
      2. Conflict resolution when multiple interventions target same worker
      3. Control saturation: don't exceed max control authority per axis
      4. Control budgeting: max N interventions per control cycle

    Design constraints:
      - Control authority per axis is bounded (saturation)
      - Control budget per cycle prevents overwhelming the swarm
      - Conflicts resolved by priority (critical > macro > meso > micro)
    """

    def __init__(
        self,
        causal_dimensions: list[str],
        max_commands_per_cycle: int = 10,
        max_control_authority_per_axis: float = 0.5,
    ):
        self.causal_dimensions = causal_dimensions
        self.max_commands_per_cycle = max_commands_per_cycle
        self.max_control_authority_per_axis = max_control_authority_per_axis
        self.state = SwarmActuatorState()

    def map_S_to_control_vectors(
        self,
        canonical_S: dict[str, float],
        worker_deltas: dict[str, dict[str, float]],
        global_coherence: float,
        coherence_matrix: list[list[float]],
        worker_ids: list[str],
        timestamp_ms: int,
        priorities: dict[tuple[str, str], int] | None = None,
    ) -> list[ControlVector]:
        """
        Map the global S_full tensor (canonical + deltas) into control vectors.

        Args:
            canonical_S: canonical S per axis (from DistributedTensorAlignment)
            worker_deltas: per-worker delta from canonical per axis
            global_coherence: current global coherence
            coherence_matrix: N×N worker coherence matrix
            worker_ids: ordered list of worker IDs
            timestamp_ms: current time
            priorities: optional {(worker_id, axis): priority} override

        Returns:
            List of ControlVector, one per intervention needed.
            Sorted by priority (highest first).
        """
        vectors: list[ControlVector] = []

        # Control gain: proportional to how far from canonical
        # K_p = 1 - S (further from canonical → higher gain)
        control_gain_base = max(0.05, 1.0 - global_coherence)

        for worker_id in worker_ids:
            deltas = worker_deltas.get(worker_id, {})
            for axis in self.causal_dimensions:
                delta = deltas.get(axis, 0.0)
                if abs(delta) < 0.01:
                    continue  # no significant deviation

                # Compute magnitude capped at saturation limit
                raw_magnitude = delta * control_gain_base
                magnitude = max(
                    -self.max_control_authority_per_axis,
                    min(self.max_control_authority_per_axis, raw_magnitude),
                )

                # Confidence inversely proportional to how many workers are affected
                n_affected = sum(
                    1 for w in worker_ids
                    if worker_deltas.get(w, {}).get(axis, 0.0) != 0
                )
                confidence = 1.0 / math.sqrt(n_affected) if n_affected > 0 else 1.0

                # Determine primitive from magnitude
                primitive = self._primitive_for_magnitude(magnitude)

                # Target coherence: canonical + 50% of the delta correction
                coherence_target = canonical_S.get(axis, 0.0) + delta * 0.5

                priority_key = (worker_id, axis)
                priority = priorities.get(priority_key, 3) if priorities else 3

                vectors.append(ControlVector(
                    worker_id=worker_id,
                    axis=axis,
                    primitive=primitive,
                    magnitude=magnitude,
                    coherence_target=coherence_target,
                    confidence=confidence,
                    control_gain=control_gain_base,
                    timestamp_ms=timestamp_ms,
                ))

        # Sort by priority (lower number = higher priority)
        vectors.sort(key=lambda v: priorities.get((v.worker_id, v.axis), 3) if priorities else 3)

        # Budget limiting: keep only top N commands
        return vectors[: self.max_commands_per_cycle]

    def resolve_conflicts(
        self, vectors: list[ControlVector]
    ) -> list[ControlVector]:
        """
        Resolve conflicts when multiple vectors target same worker+axis.
        Resolution: keep highest-priority (lowest number), merge magnitudes.
        """
        # Group by (worker_id, axis)
        groups: dict[tuple[str, str], list[ControlVector]] = {}
        for v in vectors:
            key = (v.worker_id, v.axis)
            groups.setdefault(key, []).append(v)

        resolved: list[ControlVector] = []
        for (worker_id, axis), group in groups.items():
            if len(group) == 1:
                resolved.append(group[0])
            else:
                # Merge: use highest confidence, sum magnitudes (capped)
                merged_magnitude = sum(vec.magnitude for vec in group)
                merged_magnitude = max(
                    -self.max_control_authority_per_axis,
                    min(self.max_control_authority_per_axis, merged_magnitude),
                )
                best = max(group, key=lambda v: v.confidence)
                resolved.append(
                    ControlVector(
                        worker_id=worker_id,
                        axis=axis,
                        primitive=best.primitive,
                        magnitude=merged_magnitude,
                        coherence_target=best.coherence_target,
                        confidence=best.confidence,
                        control_gain=best.control_gain,
                        timestamp_ms=best.timestamp_ms,
                    )
                )

        return resolved

    def apply_control_cycle(
        self,
        vectors: list[ControlVector],
        timestamp_ms: int,
    ) -> SwarmActuatorState:
        """
        Apply a control cycle: record commands, update actuator state.
        Returns updated SwarmActuatorState.
        """
        self.state.control_iteration += 1
        self.state.pending_commands = vectors
        self.state.command_history.extend(vectors)
        if len(self.state.command_history) > 200:
            self.state.command_history = self.state.command_history[-200:]
        return self.state

    @staticmethod
    def _primitive_for_magnitude(magnitude: float) -> ControlPrimitive:
        abs_m = abs(magnitude)
        if abs_m < 0.05:
            return ControlPrimitive.DAMPEN
        elif abs_m < 0.15:
            return ControlPrimitive.STATE_SHIFT
        elif abs_m < 0.30:
            return ControlPrimitive.REPROJECT
        elif abs_m < 0.45:
            return ControlPrimitive.REBALANCE
        else:
            return ControlPrimitive.RESET

    def get_control_diagnostics(
        self,
        vectors: list[ControlVector],
    ) -> dict[str, Any]:
        """
        Return diagnostics for a set of control vectors.
        """
        return {
            "total_vectors": len(vectors),
            "by_primitive": {
                p.name: sum(1 for v in vectors if v.primitive == p)
                for p in ControlPrimitive
            },
            "by_worker": {
                w: sum(1 for v in vectors if v.worker_id == w)
                for w in set(v.worker_id for v in vectors)
            },
            "mean_confidence": (
                sum(v.confidence for v in vectors) / len(vectors) if vectors else 0.0
            ),
            "mean_magnitude": (
                sum(abs(v.magnitude) for v in vectors) / len(vectors) if vectors else 0.0
            ),
            "control_iteration": self.state.control_iteration,
        }

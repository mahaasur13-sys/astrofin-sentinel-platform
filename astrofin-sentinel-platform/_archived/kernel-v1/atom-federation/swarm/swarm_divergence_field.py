"""
Swarm Divergence Field — v7.3
Measures divergence NOT per-node BUT per-worker-field across the entire swarm.

This is the "field physics" layer: instead of pairwise O(N²) comparisons,
we model divergence as a field over the worker mesh.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any


class FieldSeverity(Enum):
    IDENTICAL = 0.0
    MINOR = 0.25
    MODERATE = 0.5
    SEVERE = 0.75
    CRITICAL = 1.0


@dataclass
class WorkerFieldPoint:
    worker_id: str
    axis: str
    projected_magnitude: float
    causal_depth: int
    sequence_number: int
    timestamp_ms: int


@dataclass
class DivergenceFlux:
    """
    Divergence flux between two worker field points.
    Not just a scalar — has direction, magnitude, and causal coherence.
    """
    worker_pair: tuple[str, str]
    axis: str
    delta_magnitude: float  # |P1 - P2| on this axis
    flux_direction: str     # "worker1→worker2" or "worker2→worker1"
    causal_coherence: float  # 0..1, how causally aligned the two workers are
    severity: FieldSeverity


@dataclass
class SwarmDivergenceField:
    """
    The full divergence field across N workers and M axes.
    Instead of a simple scalar, this is a structured field.
    """
    field_points: list[WorkerFieldPoint]
    divergence_fluxes: list[DivergenceFlux]
    global_coherence: float  # 0..1: overall swarm coherence
    most_divergent_axis: str
    most_divergent_pair: tuple[str, str]
    field_severity: FieldSeverity


class SwarmDivergenceFieldEngine:
    """
    Computes the divergence field across a swarm of N workers.

    The key shift from v7.2:
      v7.2: per-node pairwise divergence (O(N²) worker pairs)
      v7.3: per-axis field divergence with global coherence tensor

    Metric collapse risk addressed:
      S_full is computed PER PARTITION in v7.3, then reconciled via
      distributed_tensor_alignment.py into ONE global coherence tensor.
    """

    def __init__(self, causal_dimensions: list[str]):
        self.causal_dimensions = causal_dimensions

    def build_field(
        self,
        worker_projections: list[Any],  # List[WorkerProjection from worker_projection_engine]
    ) -> SwarmDivergenceField:
        """
        Build the full divergence field from a list of worker projections.
        Each WorkerProjection must have: worker_id, axes, projected_state_hash.
        """

        # Collect field points
        field_points: list[WorkerFieldPoint] = []
        for proj in worker_projections:
            for axis_name, axis_obj in proj.axes.items():
                field_points.append(WorkerFieldPoint(
                    worker_id=proj.worker_id,
                    axis=axis_name,
                    projected_magnitude=axis_obj.magnitude,
                    causal_depth=int(axis_obj.vector[0] if axis_obj.vector else 0),
                    sequence_number=proj.sequence_number,
                    timestamp_ms=proj.timestamp_ms,
                ))

        # Compute pairwise divergence fluxes
        divergence_fluxes: list[DivergenceFlux] = []
        for i in range(len(worker_projections)):
            for j in range(i + 1, len(worker_projections)):
                w1 = worker_projections[i]
                w2 = worker_projections[j]
                pair = (w1.worker_id, w2.worker_id)

                for axis_name in self.causal_dimensions:
                    ax1 = w1.axes.get(axis_name)
                    ax2 = w2.axes.get(axis_name)
                    if ax1 is None or ax2 is None:
                        continue

                    delta = abs(ax1.magnitude - ax2.magnitude)
                    direction = (
                        f"{w1.worker_id}→{w2.worker_id}"
                        if ax1.magnitude >= ax2.magnitude
                        else f"{w2.worker_id}→{w1.worker_id}"
                    )
                    # Coherence: cosine similarity of axis vectors (0=opposite, 1=identical)
                    coherence = self._cosine_coherence(ax1.vector, ax2.vector)
                    severity = self._severity_from_delta(delta)

                    divergence_fluxes.append(DivergenceFlux(
                        worker_pair=pair,
                        axis=axis_name,
                        delta_magnitude=delta,
                        flux_direction=direction,
                        causal_coherence=coherence,
                        severity=severity,
                    ))

        # Global coherence: mean of all pairwise coherence values
        if divergence_fluxes:
            global_coherence = sum(f.causal_coherence for f in divergence_fluxes) / len(divergence_fluxes)
        else:
            global_coherence = 1.0

        # Most divergent axis (highest mean delta across all worker pairs)
        axis_deltas: dict[str, float] = {}
        for axis_name in self.causal_dimensions:
            axis_fluxes = [f for f in divergence_fluxes if f.axis == axis_name]
            if axis_fluxes:
                axis_deltas[axis_name] = sum(f.delta_magnitude for f in axis_fluxes) / len(axis_fluxes)
            else:
                axis_deltas[axis_name] = 0.0
        most_divergent_axis = (
            max(axis_deltas, key=axis_deltas.get) if axis_deltas else ""
        )

        # Most divergent worker pair (highest total flux)
        pair_deltas: dict[tuple[str, str], float] = {}
        for f in divergence_fluxes:
            pair_deltas[f.worker_pair] = pair_deltas.get(f.worker_pair, 0.0) + f.delta_magnitude
        most_divergent_pair = (
            max(pair_deltas, key=pair_deltas.get) if pair_deltas else ("", "")
        )

        field_severity = self._field_severity(global_coherence)

        return SwarmDivergenceField(
            field_points=field_points,
            divergence_fluxes=divergence_fluxes,
            global_coherence=global_coherence,
            most_divergent_axis=most_divergent_axis,
            most_divergent_pair=most_divergent_pair,
            field_severity=field_severity,
        )

    @staticmethod
    def _cosine_coherence(v1: list[float], v2: list[float]) -> float:
        """Cosine similarity between two vectors (0=opposite, 1=identical)."""
        if not v1 or not v2:
            return 0.0
        min_len = min(len(v1), len(v2))
        dot = sum(v1[i] * v2[i] for i in range(min_len))
        norm1 = math.sqrt(sum(x * x for x in v1))
        norm2 = math.sqrt(sum(x * x for x in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    @staticmethod
    def _severity_from_delta(delta: float) -> FieldSeverity:
        if delta < 0.01:
            return FieldSeverity.IDENTICAL
        elif delta < 0.1:
            return FieldSeverity.MINOR
        elif delta < 0.5:
            return FieldSeverity.MODERATE
        elif delta < 1.0:
            return FieldSeverity.SEVERE
        else:
            return FieldSeverity.CRITICAL

    @staticmethod
    def _field_severity(global_coherence: float) -> FieldSeverity:
        if global_coherence >= 0.99:
            return FieldSeverity.IDENTICAL
        elif global_coherence >= 0.9:
            return FieldSeverity.MINOR
        elif global_coherence >= 0.7:
            return FieldSeverity.MODERATE
        elif global_coherence >= 0.4:
            return FieldSeverity.SEVERE
        else:
            return FieldSeverity.CRITICAL

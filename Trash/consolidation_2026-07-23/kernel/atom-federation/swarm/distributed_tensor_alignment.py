"""
Distributed Tensor Alignment — v7.3
Aligns S_full (unified_state_metric_tensor) across workers into ONE global coherence tensor.

Addresses the "Metric collapse risk" from v7.3 spec:
  S_full becomes inconsistent across partitions →
  we compute S_full per partition, then reconcile into ONE global tensor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class WorkerSTensor:
    """S_full tensor + metadata for a single worker."""
    worker_id: str
    sequence_number: int
    timestamp_ms: int
    axes_S: dict[str, float]   # axis_name → S_full value
    total_S: float              # overall S_full
    severity: str              # "IDENTICAL" | "MINOR" | "MODERATE" | "SEVERE" | "CRITICAL"


@dataclass
class AlignmentConstraint:
    """A pairwise equality constraint between two axis tensors."""
    worker_A: str
    worker_B: str
    axis: str
    weight: float  # how strongly to enforce (0..1)


@dataclass
class GlobalCoherenceTensor:
    """
    The reconciled global coherence tensor.
    Holds ONE canonical S_full per axis and per worker deltas from canonical.
    """
    canonical_axes_S: dict[str, float]  # axis → canonical S_full (mean of workers)
    worker_deltas: dict[str, dict[str, float]]  # worker_id → {axis → delta_from_canonical}
    global_coherence: float  # 0..1
    alignment_constraints_satisfied: int
    alignment_constraints_total: int
    partition_count: int
    coherence_matrix: list[list[float]]  # N×N worker × worker coherence matrix


class DistributedTensorAlignment:
    """
    Aligns per-worker S_full tensors into a global coherence tensor.

    The problem (Metric Collapse Risk):
      worker-1: S_full = 0.42  (partition A)
      worker-2: S_full = 0.87  (partition B)
      worker-3: S_full = 0.11  (partition C)

    Without alignment: no system-wide S_full, only per-partition metrics.
    With alignment: ONE canonical tensor, deltas measured from canonical.

    Method:
      1. Compute per-worker S_full via unified_state_metric_tensor logic
      2. Compute canonical (mean or weighted-mean) per axis
      3. Compute delta from canonical per worker per axis
      4. Build N×N coherence matrix (pairwise similarity)
      5. Check constraint satisfaction
    """

    def __init__(self, causal_dimensions: list[str]):
        self.causal_dimensions = causal_dimensions

    def align(
        self,
        worker_tensors: list[WorkerSTensor],
        constraints: list[AlignmentConstraint] | None = None,
    ) -> GlobalCoherenceTensor:
        """
        Align all worker S_full tensors into one global coherence tensor.
        """
        if not worker_tensors:
            return GlobalCoherenceTensor(
                canonical_axes_S={},
                worker_deltas={},
                global_coherence=0.0,
                alignment_constraints_satisfied=0,
                alignment_constraints_total=0,
                partition_count=0,
                coherence_matrix=[],
            )

        # 1. Compute canonical S per axis (unweighted mean of workers)
        canonical_axes_S: dict[str, float] = {}
        for axis in self.causal_dimensions:
            vals = [wt.axes_S.get(axis, 0.0) for wt in worker_tensors if axis in wt.axes_S]
            canonical_axes_S[axis] = sum(vals) / len(vals) if vals else 0.0

        # Overall canonical S = mean of axis canonicals
        canonical_total = sum(canonical_axes_S.values()) / len(canonical_axes_S) if canonical_axes_S else 0.0

        # 2. Compute per-worker deltas from canonical
        worker_deltas: dict[str, dict[str, float]] = {}
        for wt in worker_tensors:
            deltas: dict[str, float] = {}
            for axis in self.causal_dimensions:
                local_S = wt.axes_S.get(axis, 0.0)
                canonical_S = canonical_axes_S.get(axis, 0.0)
                deltas[axis] = local_S - canonical_S
            worker_deltas[wt.worker_id] = deltas

        # 3. Build N×N coherence matrix (cosine similarity of delta vectors)
        worker_ids = [wt.worker_id for wt in worker_tensors]
        n = len(worker_ids)
        coherence_matrix: list[list[float]] = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                wti = worker_tensors[i]
                wtj = worker_tensors[j]
                # Delta vectors
                di = [worker_deltas[wti.worker_id].get(a, 0.0) for a in self.causal_dimensions]
                dj = [worker_deltas[wtj.worker_id].get(a, 0.0) for a in self.causal_dimensions]
                coherence = self._cosine_similarity(di, dj)
                coherence_matrix[i][j] = coherence
                coherence_matrix[j][i] = coherence

        # 4. Global coherence = mean of off-diagonal entries
        if n > 1:
            off_diag = [coherence_matrix[i][j] for i in range(n) for j in range(n) if i != j]
            global_coherence = sum(off_diag) / len(off_diag)
        else:
            global_coherence = 1.0

        # 5. Check constraints
        sat = 0
        total = 0
        if constraints:
            for c in constraints:
                # Find the two workers
                wi = next((i for i, wt in enumerate(worker_tensors) if wt.worker_id == c.worker_A), -1)
                wj = next((j for j, wt in enumerate(worker_tensors) if wt.worker_id == c.worker_B), -1)
                if wi == -1 or wj == -1:
                    continue
                delta_i = worker_deltas[c.worker_A].get(c.axis, 0.0)
                delta_j = worker_deltas[c.worker_B].get(c.axis, 0.0)
                diff = abs(delta_i - delta_j)
                # Satisfied if difference < threshold proportional to weight
                threshold = (1.0 - c.weight) * 0.5
                total += 1
                if diff <= threshold:
                    sat += 1

        return GlobalCoherenceTensor(
            canonical_axes_S=canonical_axes_S,
            worker_deltas=worker_deltas,
            global_coherence=global_coherence,
            alignment_constraints_satisfied=sat,
            alignment_constraints_total=total,
            partition_count=n,
            coherence_matrix=coherence_matrix,
        )

    @staticmethod
    def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
        if not v1 or not v2:
            return 0.0
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        if n1 == 0 or n2 == 0:
            # Both zero vectors = identical (no divergence)
            return 1.0
        dot = sum(a * b for a, b in zip(v1, v2))
        return dot / (n1 * n2)

    def reconcile_swarm_S(
        self, global_tensor: GlobalCoherenceTensor
    ) -> dict[str, float]:
        """
        Return a per-axis reconciled S value for the swarm.
        Uses canonical S as base, penalizes by (1 - global_coherence).
        """
        reconciled: dict[str, float] = {}
        penalty = 1.0 - global_tensor.global_coherence
        for axis, canonical_S in global_tensor.canonical_axes_S.items():
            reconciled[axis] = canonical_S * (1.0 - penalty * 0.5)
        return reconciled

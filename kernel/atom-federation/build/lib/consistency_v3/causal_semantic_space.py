"""
causal_semantic_space.py
========================
v7.2 — CausalSemanticSpace: embed state + time + rate + causality into a unified vector space.

Embedding axes (9-dim vector per domain):
  [0] S_exec        — normalized state magnitude (L2 norm of state dict values)
  [1] S_replay      — same for replay state
  [2] Δ_exec        — delta magnitude of exec (L2 norm of state delta)
  [3] Δ_replay      — delta magnitude of replay
  [4] R_exec        — transition rate of exec (transitions per wallclock second)
  [5] R_replay      — transition rate of replay
  [6] C_exec        — causal depth (max causal graph depth at last transition)
  [7] C_replay      — causal depth for replay
  [8] T_drift       — temporal drift magnitude (wallclock_ns delta, normalized)

Semantic distance between exec and replay:
  S(exec, replay) = ||V_exec - V_replay||_2  (Euclidean distance in embedded space)

Divergence classification (based on which axes dominate):
  axis 0,1 dominant  → state-level divergence
  axis 2,3 dominant  → rate-of-change divergence
  axis 4,5 dominant  → transition frequency divergence
  axis 6,7 dominant  → causal structure divergence
  axis 8 dominant    → temporal drift

This layer answers: WHY the systems diverge, not just IF they diverge.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CausalSemanticVector:
    """9-dimensional embedding of a single-system execution trace."""

    s_state: float = 0.0   # [0] L2 norm of state dict
    s_delta: float = 0.0   # [1] L2 norm of state delta from previous tick
    r_transitions: float = 0.0  # [2] transitions per wallclock second
    c_depth: int = 0       # [3] causal graph depth at last transition
    t_wallclock_ns: int = 0  # [4] wallclock timestamp in nanoseconds

    def to_vector(self) -> list[float]:
        return [
            self.s_state,
            self.s_delta,
            self.r_transitions,
            float(self.c_depth),
            float(self.t_wallclock_ns),
        ]

    @classmethod
    def from_state_dict(
        cls,
        state: dict[str, Any],
        prev_state: dict[str, Any] | None = None,
        transitions: int = 0,
        wallclock_ns: int | None = None,
        causal_depth: int = 0,
    ) -> CausalSemanticVector:
        s_state = _l2_norm(state)
        s_delta = _l2_norm(_dict_diff(state, prev_state or {}))
        r_transitions = transitions  # rate computed externally
        t_wallclock_ns = wallclock_ns or int(time.time_ns())
        return cls(
            s_state=s_state,
            s_delta=s_delta,
            r_transitions=float(transitions),
            c_depth=causal_depth,
            t_wallclock_ns=t_wallclock_ns,
        )

    @classmethod
    def zero(cls) -> CausalSemanticVector:
        return cls()

    def distance_to(self, other: CausalSemanticVector) -> float:
        v1, v2 = self.to_vector(), other.to_vector()
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


@dataclass
class CausalSemanticSpace:
    """
    Unified vector-space embedding for exec + replay system traces.

    Maintains rolling window of vectors per domain, computes:
    - Per-axis divergence magnitude
    - Dominant axis (explains primary divergence mode)
    - Semantic distance S(exec, replay)
    """

    domain: str
    window_size: int = 32

    # Rolling vectors per system
    exec_vectors: list[list[float]] = field(default_factory=list)
    replay_vectors: list[list[float]] = field(default_factory=list)

    # Per-axis weights (more axes may be added)
    axis_weights: list[float] = field(
        default_factory=lambda: [1.0, 1.0, 1.0, 1.0, 1.0]
    )

    def embed(
        self,
        exec_state: dict[str, Any],
        replay_state: dict[str, Any],
        exec_prev_state: dict[str, Any] | None = None,
        replay_prev_state: dict[str, Any] | None = None,
        exec_transitions: int = 0,
        replay_transitions: int = 0,
        exec_causal_depth: int = 0,
        replay_causal_depth: int = 0,
    ) -> tuple[CausalSemanticVector, CausalSemanticVector]:
        """Embed both systems into the semantic space."""
        now_ns = int(time.time_ns())
        exec_vec = CausalSemanticVector.from_state_dict(
            exec_state, exec_prev_state, exec_transitions, now_ns, exec_causal_depth
        )
        replay_vec = CausalSemanticVector.from_state_dict(
            replay_state, replay_prev_state, replay_transitions, now_ns, replay_causal_depth
        )
        self.exec_vectors.append(exec_vec.to_vector())
        self.replay_vectors.append(replay_vec.to_vector())

        # Trim to window
        if len(self.exec_vectors) > self.window_size:
            self.exec_vectors = self.exec_vectors[-self.window_size :]
        if len(self.replay_vectors) > self.window_size:
            self.replay_vectors = self.replay_vectors[-self.window_size :]

        return exec_vec, replay_vec

    def semantic_distance(self) -> float:
        """Euclidean distance between the most recent exec and replay vectors."""
        if not self.exec_vectors or not self.replay_vectors:
            return 0.0
        v_exec = self.exec_vectors[-1]
        v_replay = self.replay_vectors[-1]
        return math.sqrt(
            sum(w * (a - b) ** 2 for a, b, w in zip(v_exec, v_replay, self.axis_weights))
        )

    def per_axis_divergence(self) -> list[float]:
        """Per-axis |exec - replay| magnitude for the most recent tick."""
        if not self.exec_vectors or not self.replay_vectors:
            return [0.0] * 5
        v_exec = self.exec_vectors[-1]
        v_replay = self.replay_vectors[-1]
        return [abs(a - b) for a, b in zip(v_exec, v_replay)]

    def dominant_divergence_axis(self) -> tuple[int, float]:
        """
        Returns (axis_index, magnitude) of the dominant divergence axis.
        Axes: 0=state magnitude, 1=delta magnitude, 2=transition rate,
              3=causal depth, 4=temporal drift
        """
        per_axis = self.per_axis_divergence()
        if all(v == 0.0 for v in per_axis):
            return (-1, 0.0)
        max_idx = int(max(range(len(per_axis)), key=lambda i: per_axis[i]))
        return (max_idx, per_axis[max_idx])

    def divergence_classification(self) -> str:
        """Human-readable classification of the dominant divergence mode."""
        axis_map = {
            0: "state-level divergence",
            1: "delta-rate divergence",
            2: "transition-frequency divergence",
            3: "causal-structure divergence",
            4: "temporal drift",
        }
        idx, mag = self.dominant_divergence_axis()
        if idx == -1:
            return "no divergence detected"
        return f"{axis_map.get(idx, f'axis-{idx}')} (magnitude={mag:.4f})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "window_size": self.window_size,
            "exec_vector_count": len(self.exec_vectors),
            "replay_vector_count": len(self.replay_vectors),
            "semantic_distance": self.semantic_distance(),
            "per_axis_divergence": self.per_axis_divergence(),
            "dominant_axis": self.dominant_divergence_axis()[0],
            "classification": self.divergence_classification(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────


def _l2_norm(d: dict[str, Any]) -> float:
    """L2 norm of a dict's values (handles numeric types)."""
    values = []
    for v in d.values():
        if isinstance(v, (int, float)):
            values.append(float(v))
        elif isinstance(v, dict):
            values.append(_l2_norm(v))
        elif isinstance(v, (list, tuple)):
            sub = [x for x in v if isinstance(x, (int, float))]
            if sub:
                values.append(math.sqrt(sum(float(x) ** 2 for x in sub)))
    return math.sqrt(sum(x**2 for x in values)) if values else 0.0


def _dict_diff(
    curr: dict[str, Any], prev: dict[str, Any]
) -> dict[str, Any]:
    """Field-level diff: curr - prev, non-numeric fields skipped."""
    result = {}
    all_keys = set(curr.keys()) | set(prev.keys())
    for k in all_keys:
        cv = curr.get(k)
        pv = prev.get(k)
        if isinstance(cv, (int, float)) and isinstance(pv, (int, float)):
            result[k] = cv - pv
        elif isinstance(cv, dict) and isinstance(pv, dict):
            sub_diff = _dict_diff(cv, pv)
            if sub_diff:
                result[k] = sub_diff
    return result

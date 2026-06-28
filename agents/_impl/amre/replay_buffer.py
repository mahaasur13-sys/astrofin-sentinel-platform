"""amre/replay_buffer.py — Replay Buffer for trajectory learning"""

from __future__ import annotations


from dataclasses import dataclass
from typing import Any

from .similarity import is_similar_trajectory
from .trajectory import Trajectory, TrajectoryMetrics

DEFAULT_BUFFER_SIZE = 1000


@dataclass
class BufferEntry:
    trajectory: Trajectory
    metrics: TrajectoryMetrics
    outcome: float
    market_context: dict[str, Any]
    created_at: str


class ReplayBuffer:
    def __init__(self, max_size: int = DEFAULT_BUFFER_SIZE):
        self.max_size = max_size
        self.buffer: list[BufferEntry] = []

    def add(self, entry: BufferEntry):
        self.buffer.append(entry)
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)

    def get_all_trajectories(self) -> list[Trajectory]:
        return [e.trajectory for e in self.buffer]

    def get_similar(self, trajectory: Trajectory, threshold: float = 0.3) -> list[BufferEntry]:
        return [e for e in self.buffer if is_similar_trajectory(trajectory, e.trajectory, threshold)]

    def size(self) -> int:
        return len(self.buffer)


_DEFAULT_BUFFER: ReplayBuffer | None = None


def get_default_buffer() -> ReplayBuffer:
    global _DEFAULT_BUFFER
    if _DEFAULT_BUFFER is None:
        _DEFAULT_BUFFER = ReplayBuffer()
    return _DEFAULT_BUFFER


def _select_best_trajectory(trajectories: list[Trajectory], q_star_scores: list[float]) -> Trajectory:
    if not trajectories:
        raise ValueError("No trajectories provided")
    scored = list(zip(trajectories, q_star_scores, strict=False))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]

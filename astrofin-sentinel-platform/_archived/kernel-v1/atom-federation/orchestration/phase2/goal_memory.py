"""
goal_memory.py — v8.0 Phase 2
Goal-level persistence: bridges goal state → DecisionMemory + StateWindowStore.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class GoalRecord:
    goal_id: int
    goal_payload: dict
    planned_source: str
    planned_priority: float
    proof_verdict: bool
    coherence_at_plan: float
    actual_outcome: float | None = None
    persistence_drift: float = 0.0
    replan_triggered: bool = False
    timestamp: float = field(default_factory=time.time)


class GoalMemory:
    """
    Goal-level version of DecisionMemory.
    Records goal attempts paired with their outcomes and persistence drift.
    Used by replanner to detect goal-level degradation.
    """

    def __init__(self, max_goals: int = 200) -> None:
        self._max = max_goals
        self._deque: deque[GoalRecord] = deque(maxlen=max_goals)
        self._id_counter = 0

    def append(
        self,
        goal_payload: dict,
        planned_source: str,
        planned_priority: float,
        proof_verdict: bool,
        coherence_at_plan: float,
        actual_outcome: float | None = None,
        persistence_drift: float = 0.0,
    ) -> int:
        self._id_counter += 1
        rec = GoalRecord(
            goal_id=self._id_counter,
            goal_payload=goal_payload,
            planned_source=planned_source,
            planned_priority=planned_priority,
            proof_verdict=proof_verdict,
            coherence_at_plan=coherence_at_plan,
            actual_outcome=actual_outcome,
            persistence_drift=persistence_drift,
        )
        self._deque.append(rec)
        return self._id_counter

    def record_outcome(self, goal_id: int, outcome: float) -> bool:
        for rec in self._deque:
            if rec.goal_id == goal_id:
                rec.actual_outcome = outcome
                return True
        return False

    def record_drift(self, goal_id: int, drift: float) -> bool:
        for rec in self._deque:
            if rec.goal_id == goal_id:
                rec.persistence_drift = drift
                return True
        return False

    def mark_replan(self, goal_id: int) -> bool:
        for rec in self._deque:
            if rec.goal_id == goal_id:
                rec.replan_triggered = True
                return True
        return False

    def recent(self, n: int = 10) -> list[GoalRecord]:
        return list(self._deque)[-n:]

    def with_outcomes(self) -> list[GoalRecord]:
        return [r for r in self._deque if r.actual_outcome is not None]

    def avg_outcome(self) -> float:
        outcomes = [r.actual_outcome for r in self._deque if r.actual_outcome is not None]
        return sum(outcomes) / len(outcomes) if outcomes else 0.0

    def drift_trend(self) -> float:
        """Average drift across all goals with recorded drift."""
        drifts = [r.persistence_drift for r in self._deque if r.persistence_drift != 0.0]
        return sum(drifts) / len(drifts) if drifts else 0.0

    def replan_rate(self) -> float:
        """Fraction of goals that triggered replan."""
        total = len(self._deque)
        if total == 0:
            return 0.0
        return sum(1 for r in self._deque if r.replan_triggered) / total

    @property
    def count(self) -> int:
        return len(self._deque)

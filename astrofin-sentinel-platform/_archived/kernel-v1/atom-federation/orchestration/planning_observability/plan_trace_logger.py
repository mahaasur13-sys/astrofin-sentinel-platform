"""
plan_trace_logger.py — planning_observability layer
Records full execution trace of the planning pipeline.

Logged events:
  - node traversal (add_node, complete_node, skip_node)
  - 4D score evolution over time
  - cycle detection events
  - replanning triggers
  - coherence deviations

Invariant (v8.0 Phase A):
  trace_health = f(log Completeness, log Coherence, event Coverage)
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class TraceEventType(Enum):
    # Node lifecycle
    NODE_ADDED = "node_added"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_SKIPPED = "node_skipped"
    # Planning lifecycle
    PLAN_CREATED = "plan_created"
    PLAN_LOCKED = "plan_locked"
    PLAN_EXECUTED = "plan_executed"
    PLAN_PRUNED = "plan_pruned"
    # Evaluation
    EVAL_SCORE = "eval_score"
    EVAL_WEIGHTS_UPDATED = "eval_weights_updated"
    # Cycle detection
    CYCLE_DETECTED = "cycle_detected"
    CYCLE_BROKEN = "cycle_broken"
    # Replanning
    REPLAN_TRIGGERED = "replan_triggered"
    REPLAN_SUPPRESSED = "replan_suppressed"
    # Coherence
    COHERENCE_DEVIATION = "coherence_deviation"
    COHERENCE_DROP = "coherence_drop"
    # DAG
    DAG_BRANCH_ADDED = "dag_branch_added"
    DAG_EDGE_ADDED = "dag_edge_added"


@dataclass
class TraceEvent:
    tick: int
    event_type: TraceEventType
    plan_id: str
    node_id: str | None
    data: dict
    timestamp: float = field(default_factory=time.time)


@dataclass
class ScoreEvolutionPoint:
    tick: int
    plan_id: str
    stability_score: float
    coherence_score: float
    gain_score: float
    weight_score: float
    overall: float


@dataclass
class CycleRecord:
    tick: int
    plan_id: str
    cycle_node_ids: list[str]
    broken_via: str  # "edge_removal" | "node_prune" | "replan"


@dataclass
class ReplanRecord:
    tick: int
    plan_id: str
    trigger_reason: str  # "coherence_drop" | "cycle_detected" | "stability_collapse" | ...
    coherence_before: float
    coherence_after: float
    nodes_regenerated: int


class PlanTraceLogger:
    """
    Records full execution trace of the planning pipeline.

    Provides:
      - full event log (in-memory, bounded)
      - score evolution history
      - cycle detection log
      - replanning history
      - trace health metrics

    Thread-unsafe (single-threaded execution assumed).
    """

    def __init__(
        self,
        max_events: int = 1000,
        max_score_points: int = 500,
        max_cycles: int = 100,
        max_replans: int = 200,
    ) -> None:
        self._events: deque[TraceEvent] = deque(maxlen=max_events)
        self._score_history: deque[ScoreEvolutionPoint] = deque(maxlen=max_score_points)
        self._cycles: deque[CycleRecord] = deque(maxlen=max_cycles)
        self._replans: deque[ReplanRecord] = deque(maxlen=max_replans)
        self._node_count: int = 0
        self._plan_count: int = 0
        self._replan_count: int = 0
        self._coherence_last: float = 0.0

    # ─── event emission ────────────────────────────────────────────────────────

    def log_node_added(
        self,
        tick: int,
        plan_id: str,
        node_id: str,
        action: str,
        priority: float,
        has_proof: bool,
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.NODE_ADDED,
            plan_id=plan_id,
            node_id=node_id,
            data={
                "action": action,
                "priority": priority,
                "has_proof": has_proof,
            },
        ))
        self._node_count += 1

    def log_node_completed(
        self,
        tick: int,
        plan_id: str,
        node_id: str,
        outcome: float,
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.NODE_COMPLETED,
            plan_id=plan_id,
            node_id=node_id,
            data={"outcome": outcome},
        ))

    def log_node_skipped(
        self,
        tick: int,
        plan_id: str,
        node_id: str,
        reason: str,
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.NODE_SKIPPED,
            plan_id=plan_id,
            node_id=node_id,
            data={"reason": reason},
        ))

    def log_plan_created(
        self,
        tick: int,
        plan_id: str,
        root_node_ids: list[str],
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.PLAN_CREATED,
            plan_id=plan_id,
            node_id=None,
            data={"root_count": len(root_node_ids)},
        ))
        self._plan_count += 1

    def log_plan_locked(self, tick: int, plan_id: str) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.PLAN_LOCKED,
            plan_id=plan_id,
            node_id=None,
            data={},
        ))

    def log_plan_executed(
        self,
        tick: int,
        plan_id: str,
        node_count: int,
        completion_rate: float,
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.PLAN_EXECUTED,
            plan_id=plan_id,
            node_id=None,
            data={
                "node_count": node_count,
                "completion_rate": completion_rate,
            },
        ))

    def log_eval_score(
        self,
        tick: int,
        plan_id: str,
        stability: float,
        coherence: float,
        gain: float,
        weight: float,
        overall: float,
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.EVAL_SCORE,
            plan_id=plan_id,
            node_id=None,
            data={
                "stability": stability,
                "coherence": coherence,
                "gain": gain,
                "weight": weight,
                "overall": overall,
            },
        ))
        self._score_history.append(ScoreEvolutionPoint(
            tick=tick,
            plan_id=plan_id,
            stability_score=stability,
            coherence_score=coherence,
            gain_score=gain,
            weight_score=weight,
            overall=overall,
        ))

    def log_cycle_detected(
        self,
        tick: int,
        plan_id: str,
        cycle_node_ids: list[str],
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.CYCLE_DETECTED,
            plan_id=plan_id,
            node_id=None,
            data={"cycle_nodes": cycle_node_ids},
        ))
        self._cycles.append(CycleRecord(
            tick=tick,
            plan_id=plan_id,
            cycle_node_ids=cycle_node_ids,
            broken_via="unknown",
        ))

    def log_cycle_broken(
        self,
        tick: int,
        plan_id: str,
        cycle_node_ids: list[str],
        method: Literal["edge_removal", "node_prune", "replan"],
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.CYCLE_BROKEN,
            plan_id=plan_id,
            node_id=None,
            data={"cycle_nodes": cycle_node_ids, "method": method},
        ))
        if self._cycles:
            rec = self._cycles[-1]
            rec.broken_via = method

    def log_replan_triggered(
        self,
        tick: int,
        plan_id: str,
        reason: str,
        coherence_before: float,
        coherence_after: float,
        nodes_regenerated: int,
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.REPLAN_TRIGGERED,
            plan_id=plan_id,
            node_id=None,
            data={
                "reason": reason,
                "coherence_before": coherence_before,
                "coherence_after": coherence_after,
                "nodes_regenerated": nodes_regenerated,
            },
        ))
        self._replans.append(ReplanRecord(
            tick=tick,
            plan_id=plan_id,
            trigger_reason=reason,
            coherence_before=coherence_before,
            coherence_after=coherence_after,
            nodes_regenerated=nodes_regenerated,
        ))
        self._replan_count += 1

    def log_replan_suppressed(
        self,
        tick: int,
        plan_id: str,
        reason: str,
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.REPLAN_SUPPRESSED,
            plan_id=plan_id,
            node_id=None,
            data={"suppression_reason": reason},
        ))

    def log_coherence_deviation(
        self,
        tick: int,
        plan_id: str,
        coherence_before: float,
        coherence_after: float,
        deviation: float,
    ) -> None:
        self._events.append(TraceEvent(
            tick=tick,
            event_type=TraceEventType.COHERENCE_DEVIATION,
            plan_id=plan_id,
            node_id=None,
            data={
                "coherence_before": coherence_before,
                "coherence_after": coherence_after,
                "deviation": deviation,
            },
        ))
        self._coherence_last = coherence_after

    # ─── trace health ──────────────────────────────────────────────────────────

    def trace_completeness(self) -> float:
        """Fraction of plans that have eval_score events (0..1)."""
        if not self._plan_count:
            return 1.0
        plans_with_eval = {
            e.plan_id for e in self._events
            if e.event_type == TraceEventType.EVAL_SCORE
        }
        return len(plans_with_eval) / self._plan_count

    def trace_coherence(self) -> float:
        """Fraction of consecutive eval scores within ±0.1 (0..1)."""
        scores = [p.overall for p in self._score_history]
        if len(scores) < 2:
            return 1.0
        coherent = sum(
            1 for i in range(1, len(scores))
            if abs(scores[i] - scores[i - 1]) <= 0.1
        )
        return coherent / (len(scores) - 1)

    def get_trace_health(self) -> float:
        """
        Composite trace health score (0..1).

        Combines:
          - completeness: fraction of plans with evaluation
          - coherence: fraction of smooth score transitions
          - event_rate: normalized event density (0..1)
        """
        completeness = self.trace_completeness()
        coherence = self.trace_coherence()
        # event density vs theoretical max (rough proxy: ~10 events/plan)
        event_rate = min(1.0, len(self._events) / max(1, self._plan_count * 10))
        return (completeness + coherence + event_rate) / 3.0

    # ─── summary accessors ─────────────────────────────────────────────────────

    def recent_events(self, n: int = 50) -> list[TraceEvent]:
        return list(self._events)[-n:]

    def score_trajectory(self, plan_id: str) -> list[ScoreEvolutionPoint]:
        return [p for p in self._score_history if p.plan_id == plan_id]

    def cycle_summary(self) -> list[CycleRecord]:
        return list(self._cycles)

    def replan_summary(self) -> list[ReplanRecord]:
        return list(self._replans)

    @property
    def total_nodes(self) -> int:
        return self._node_count

    @property
    def total_plans(self) -> int:
        return self._plan_count

    @property
    def total_replans(self) -> int:
        return self._replan_count

    @property
    def last_coherence(self) -> float:
        return self._coherence_last

    def to_dict(self) -> dict:
        return {
            "total_nodes": self._node_count,
            "total_plans": self._plan_count,
            "total_replans": self._replan_count,
            "last_coherence": self._coherence_last,
            "trace_health": self.get_trace_health(),
            "completeness": self.trace_completeness(),
            "coherence": self.trace_coherence(),
            "events_stored": len(self._events),
            "score_points": len(self._score_history),
            "cycles": len(self._cycles),
            "replans": len(self._replans),
        }

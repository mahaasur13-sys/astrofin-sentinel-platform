#!/usr/bin/env python3
"""
Evolution Engine — Long-horizon policy adaptation.
Tracks correction loop decisions over time and evolves system parameters.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from ..correction_loop.loop import CorrectionCycleResult, FixType, CorrectionAction


@dataclass
class EvolutionRecord:
    """Single evolution event."""
    timestamp: datetime
    generation: int
    fix_type: FixType
    action: CorrectionAction
    success: bool
    latency_before: float
    latency_after: Optional[float]
    p99_before: float
    p99_after: Optional[float]


@dataclass
class GenerationSummary:
    """Summary of one generation (correction cycle batch)."""
    generation: int
    started_at: datetime
    cycles_run: int
    fixes_applied: int
    escalations: int
    avg_latency_ms: float
    p99_latency_ms: float
    success_rate: float
    converged: bool


class EvolutionEngine:
    """
    Tracks system evolution over time.
    Detects convergence, identifies stuck patterns, triggers meta-learning.
    """

    def __init__(self):
        self._records: list[EvolutionRecord] = []
        self._generation = 0
        self._generation_cycles: list[CorrectionCycleResult] = []
        self._generation_start: Optional[datetime] = None
        self._convergence_threshold = 3  # generations with same fix type
        self._last_fix_type: Optional[FixType] = None
        self._stuck_counter = 0

    def record(self, cycle_result: CorrectionCycleResult, latency_before: float, p99_before: float) -> None:
        """Record correction cycle result for evolution tracking."""
        if cycle_result.decision is None:
            return

        record = EvolutionRecord(
            timestamp=cycle_result.timestamp,
            generation=self._generation,
            fix_type=cycle_result.decision.fix_type,
            action=cycle_result.decision.primary_action,
            success=cycle_result.next_cycle_recommended is False,
            latency_before=latency_before,
            latency_after=None,
            p99_before=p99_before,
            p99_after=None,
        )
        self._records.append(record)
        self._generation_cycles.append(cycle_result)

    def end_generation(self) -> GenerationSummary:
        """End current generation and compute summary."""
        if not self._generation_cycles:
            return GenerationSummary(generation=self._generation, started_at=datetime.utcnow(), cycles_run=0, fixes_applied=0, escalations=0, avg_latency_ms=0, p99_latency_ms=0, success_rate=0, converged=False)

        cycles = self._generation_cycles
        fixes = sum(1 for c in cycles if c.decision and c.decision.primary_action != CorrectionAction.ADJUST_QUEUE_DEPTH)
        escalations = sum(1 for c in cycles if c.escalation_required)

        # Check convergence
        fix_types = [c.decision.fix_type for c in cycles if c.decision]
        most_common = max(set(fix_types), key=fix_types.count) if fix_types else None
        if most_common == self._last_fix_type:
            self._stuck_counter += 1
        else:
            self._stuck_counter = 0
            self._last_fix_type = most_common

        converged = self._stuck_counter >= self._convergence_threshold

        summary = GenerationSummary(
            generation=self._generation,
            started_at=self._generation_start or datetime.utcnow(),
            cycles_run=len(cycles),
            fixes_applied=fixes,
            escalations=escalations,
            avg_latency_ms=0,
            p99_latency_ms=0,
            success_rate=fixes / max(1, len(cycles)),
            converged=converged,
        )
        self._generation += 1
        self._generation_cycles = []
        self._generation_start = datetime.utcnow()
        return summary

    def should_trigger_meta_learning(self) -> bool:
        """Return True if stuck pattern detected — meta-learner should intervene."""
        return self._stuck_counter >= self._convergence_threshold

    def get_evolution_report(self) -> dict:
        """Generate full evolution report."""
        if not self._records:
            return {"generations": 0, "records": 0}

        fix_type_counts = {}
        action_counts = {}
        for r in self._records:
            ft = r.fix_type.value
            fix_type_counts[ft] = fix_type_counts.get(ft, 0) + 1
            action_counts[r.action.value] = action_counts.get(r.action.value, 0) + 1

        return {
            "total_generations": self._generation,
            "total_records": len(self._records),
            "fix_type_distribution": fix_type_counts,
            "action_distribution": action_counts,
            "stuck_counter": self._stuck_counter,
            "meta_learning_recommended": self.should_trigger_meta_learning(),
        }

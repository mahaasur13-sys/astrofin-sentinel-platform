#!/usr/bin/env python3
"""
Execution Budget Controller (EBC) — prevents P99 latency tail risk.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import time
import asyncio


@dataclass
class ExecutionBudget:
    total_ms: float = 1000.0
    beam_search_ms: float = 200.0    # 20%
    constraint_filter_ms: float = 100.0  # 10%
    ilp_solver_ms: float = 400.0     # 40%
    digital_twin_ms: float = 200.0   # 20%
    policy_eval_ms: float = 100.0    # 10%


@dataclass
class StageResult:
    stage: str
    elapsed_ms: float
    budget_ms: float
    timed_out: bool = False
    output: Optional[object] = None


@dataclass
class BudgetCycle:
    cycle_id: str
    started_at: datetime
    stages: list[StageResult] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    total_elapsed_ms: float = 0.0
    fallback_triggered: bool = False
    fallback_at_stage: Optional[str] = None


class ExecutionBudgetController:
    def __init__(
        self,
        total_budget_ms: float = 1000.0,
        ilp_timeout_ms: float = 400.0,
        twin_timeout_ms: float = 200.0,
        beam_timeout_ms: float = 200.0,
        constraint_timeout_ms: float = 100.0,
        policy_eval_timeout_ms: float = 100.0,
    ):
        self.default_budget = ExecutionBudget(
            total_ms=total_budget_ms,
            beam_search_ms=beam_timeout_ms,
            constraint_filter_ms=constraint_timeout_ms,
            ilp_solver_ms=ilp_timeout_ms,
            digital_twin_ms=twin_timeout_ms,
            policy_eval_ms=policy_eval_timeout_ms,
        )
        self._cycles: list[BudgetCycle] = []
        self._current_cycle: Optional[BudgetCycle] = None
        self._mode: str = "normal"
        self._degradation_count: int = 0

    def start_cycle(self, cycle_id: str) -> BudgetCycle:
        cycle = BudgetCycle(cycle_id=cycle_id, started_at=datetime.utcnow())
        self._current_cycle = cycle
        return cycle

    def run_stage(self, stage_name: str, budget_ms: float, func, *args, **kwargs) -> StageResult:
        if self._current_cycle is None:
            raise RuntimeError("No active cycle")
        start = time.monotonic()
        timed_out = False
        output = None
        try:
            remaining = budget_ms / 1000.0
            output = func(*args, **kwargs)
        except TimeoutError:
            timed_out = True
        except Exception as e:
            timed_out = True
            output = e
        elapsed_ms = (time.monotonic() - start) * 1000.0
        result = StageResult(stage=stage_name, elapsed_ms=elapsed_ms, budget_ms=budget_ms, timed_out=timed_out, output=output)
        self._current_cycle.stages.append(result)
        if timed_out:
            self._trigger_fallback(stage_name)
        return result

    async def run_stage_async(self, stage_name: str, budget_ms: float, func, *args, **kwargs) -> StageResult:
        if self._current_cycle is None:
            raise RuntimeError("No active cycle")
        start = time.monotonic()
        timed_out = False
        output = None
        try:
            coro = func(*args, **kwargs)
            output = await asyncio.wait_for(coro, timeout=budget_ms / 1000.0)
        except asyncio.TimeoutError:
            timed_out = True
        except Exception as e:
            timed_out = True
            output = e
        elapsed_ms = (time.monotonic() - start) * 1000.0
        result = StageResult(stage=stage_name, elapsed_ms=elapsed_ms, budget_ms=budget_ms, timed_out=timed_out, output=output)
        self._current_cycle.stages.append(result)
        if timed_out:
            self._trigger_fallback(stage_name)
        return result

    def _trigger_fallback(self, stage_name: str) -> None:
        self._mode = "degraded_heuristic"
        self._degradation_count += 1
        if self._current_cycle:
            self._current_cycle.fallback_triggered = True
            self._current_cycle.fallback_at_stage = stage_name

    def end_cycle(self) -> BudgetCycle:
        if self._current_cycle is None:
            raise RuntimeError("No active cycle")
        cycle = self._current_cycle
        cycle.completed_at = datetime.utcnow()
        cycle.total_elapsed_ms = sum(s.elapsed_ms for s in cycle.stages)
        self._current_cycle = None
        self._cycles.append(cycle)
        if cycle.fallback_triggered:
            self._mode = "degraded_heuristic"
        return cycle

    def get_mode(self) -> str:
        return self._mode

    def get_stats(self) -> dict:
        if not self._cycles:
            return {}
        all_totals = sorted([c.total_elapsed_ms for c in self._cycles])
        n = len(all_totals)
        return {
            "mode": self._mode,
            "total_cycles": n,
            "fallback_count": sum(1 for c in self._cycles if c.fallback_triggered),
            "degradation_count": self._degradation_count,
            "p50_ms": float(all_totals[n // 2]),
            "p95_ms": float(all_totals[int(n * 0.95)]),
            "p99_ms": float(all_totals[int(n * 0.99)]) if n >= 100 else None,
            "avg_ms": float(sum(all_totals) / n),
        }

    def reset_mode(self) -> None:
        self._mode = "normal"
        self._degradation_count = 0

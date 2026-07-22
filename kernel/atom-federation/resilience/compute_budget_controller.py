"""
v6.7 — Compute Budget Controller

Bounds the computational overhead of:
  - DecisionLattice (proof search, branching)
  - PredictiveController (forecast horizon, simulation depth)
  - EigenstateDetector (clustering, distance computations)

Mechanisms:
  - Time budget per tick (max CPU time allowed)
  - Lattice pruning: cut branches below confidence threshold
  - Adaptive horizon: reduce forecast window under load
  - Cost accounting: track and limit per-subsystem spend
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum


class Subsystem(Enum):
    DECISION_LATTICE = "decision_lattice"
    PREDICTIVE_CONTROLLER = "predictive_controller"
    EIGENSTATE_DETECTOR = "eigenstate_detector"
    MODEL_ALIGNER = "model_reality_aligner"
    GOVERNORS = "governors"


@dataclass
class BudgetAllocation:
    subsystem: Subsystem
    max_time_ms: float
    priority: int                # 1 = highest
    allow_pruning: bool = True


@dataclass
class CostEntry:
    timestamp: float
    subsystem: Subsystem
    elapsed_ms: float
    nodes_visited: int
    pruned: bool
    budget_exceeded: bool


@dataclass
class BudgetDecision:
    allowed: bool
    reason: str
    time_remaining_ms: float
    effective_budget_ms: float


@dataclass
class ComputeBudgetSnapshot:
    timestamp: float
    total_budget_ms: float
    spent_ms: float
    remaining_ms: float
    utilization_pct: float
    allocations: dict[Subsystem, float]
    active_subsystem: Subsystem | None = None


class ComputeBudgetController:
    """
    Tracks and limits compute spend per tick.

    Tick budget is divided among subsystems proportionally to priority.
    Subsystems may prune their work if they exceed their allocation.
    """

    def __init__(
        self,
        total_budget_ms: float = 50.0,
        default_allocation_ms: float = 10.0,
    ):
        self.total_budget_ms = total_budget_ms
        self.default_allocation_ms = default_allocation_ms
        self.tick_start: float | None = None
        self.current_subsystem: Subsystem | None = None
        self.subsystem_spend: dict[Subsystem, float] = {s: 0.0 for s in Subsystem}
        self.cost_log: list[CostEntry] = []
        self.tick_count = 0

        # Default allocations by priority
        self.allocations: dict[Subsystem, BudgetAllocation] = {
            Subsystem.DECISION_LATTICE: BudgetAllocation(
                subsystem=Subsystem.DECISION_LATTICE,
                max_time_ms=15.0,
                priority=1,
            ),
            Subsystem.PREDICTIVE_CONTROLLER: BudgetAllocation(
                subsystem=Subsystem.PREDICTIVE_CONTROLLER,
                max_time_ms=12.0,
                priority=2,
            ),
            Subsystem.EIGENSTATE_DETECTOR: BudgetAllocation(
                subsystem=Subsystem.EIGENSTATE_DETECTOR,
                max_time_ms=8.0,
                priority=3,
            ),
            Subsystem.MODEL_ALIGNER: BudgetAllocation(
                subsystem=Subsystem.MODEL_ALIGNER,
                max_time_ms=7.0,
                priority=3,
            ),
            Subsystem.GOVERNORS: BudgetAllocation(
                subsystem=Subsystem.GOVERNORS,
                max_time_ms=5.0,
                priority=2,
            ),
        }

    def begin_tick(self) -> None:
        """Mark start of a new control tick."""
        self.tick_start = time.monotonic()
        self.subsystem_spend = {s: 0.0 for s in Subsystem}
        self.tick_count += 1

    def enter_subsystem(self, subsystem: Subsystem) -> BudgetDecision:
        """Called when entering a subsystem. Returns budget decision."""
        self.current_subsystem = subsystem
        elapsed = self._elapsed_ms()
        remaining = max(self.total_budget_ms - elapsed, 0.0)
        alloc = self.allocations.get(subsystem)

        if remaining <= 0.0:
            return BudgetDecision(
                allowed=False,
                reason="tick_budget_exhausted",
                time_remaining_ms=0.0,
                effective_budget_ms=0.0,
            )

        effective = min(remaining, alloc.max_time_ms if alloc else self.default_allocation_ms)

        return BudgetDecision(
            allowed=True,
            reason="within_budget",
            time_remaining_ms=remaining,
            effective_budget_ms=effective,
        )

    def exit_subsystem(
        self,
        subsystem: Subsystem,
        elapsed_ms: float,
        nodes_visited: int = 0,
        pruned: bool = False,
    ) -> CostEntry:
        """Record cost of a subsystem execution."""
        entry = CostEntry(
            timestamp=time.time(),
            subsystem=subsystem,
            elapsed_ms=elapsed_ms,
            nodes_visited=nodes_visited,
            pruned=pruned,
            budget_exceeded=elapsed_ms > self.allocations[subsystem].max_time_ms,
        )
        self.subsystem_spend[subsystem] += elapsed_ms
        self.cost_log.append(entry)
        if len(self.cost_log) > 1000:
            self.cost_log = self.cost_log[-500:]
        self.current_subsystem = None
        return entry

    def should_prune(self, subsystem: Subsystem, current_nodes: int) -> bool:
        """Check if subsystem should prune its search tree."""
        alloc = self.allocations.get(subsystem)
        if not alloc or not alloc.allow_pruning:
            return False
        elapsed = self._elapsed_ms()
        remaining = self.total_budget_ms - elapsed
        alloc_remaining = alloc.max_time_ms - self.subsystem_spend[subsystem]
        # Prune if we have spent > 80% of our allocation in < 50% of tick time
        spent_ratio = self.subsystem_spend[subsystem] / max(alloc.max_time_ms, 0.1)
        time_ratio = elapsed / max(self.total_budget_ms, 0.1)
        return spent_ratio > 0.8 and time_ratio < 0.5

    def get_adaptive_horizon(self, base_horizon: float, subsystem: Subsystem) -> float:
        """Reduce horizon if compute budget is under pressure."""
        elapsed = self._elapsed_ms()
        remaining_pct = max((self.total_budget_ms - elapsed) / self.total_budget_ms, 0.0)
        # Linear scaling: if 50% time remaining, allow 50% of horizon
        scale = min(remaining_pct / 0.5, 1.0)
        return base_horizon * scale

    def snapshot(self) -> ComputeBudgetSnapshot:
        elapsed = self._elapsed_ms()
        remaining = max(self.total_budget_ms - elapsed, 0.0)
        utilization = (elapsed / self.total_budget_ms * 100) if self.total_budget_ms > 0 else 0.0
        return ComputeBudgetSnapshot(
            timestamp=time.time(),
            total_budget_ms=self.total_budget_ms,
            spent_ms=elapsed,
            remaining_ms=remaining,
            utilization_pct=utilization,
            allocations={
                s: self.subsystem_spend.get(s, 0.0) for s in Subsystem
            },
            active_subsystem=self.current_subsystem,
        )

    def _elapsed_ms(self) -> float:
        if self.tick_start is None:
            return 0.0
        return (time.monotonic() - self.tick_start) * 1000.0

    def summary(self) -> dict:
        snap = self.snapshot()
        return {
            "tick": self.tick_count,
            "total_budget_ms": snap.total_budget_ms,
            "spent_ms": round(snap.spent_ms, 2),
            "remaining_ms": round(snap.remaining_ms, 2),
            "utilization_pct": round(snap.utilization_pct, 1),
            "log_size": len(self.cost_log),
        }

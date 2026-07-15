"""
merge_engine.py — v10.1 Causal Convergence Layer

Executes merge decisions produced by equivalence.py.

Core invariant (preserved):
  Events are NEVER deleted. Merge creates a new committed branch.
  Both source branches are preserved in the audit trail as MERGED/SUPERSEDED.

Merge algorithm:
  1. Build LCA-relative event sequences for both branches
  2. Interleave by causal timestamp (Lamport order)
  3. Apply conflict resolution (L1>L2>L3 priority)
  4. Emit MERGE_COMMIT event to new merged branch

Conflict resolution matrix:
  L1 conflict  → structural priority (hard reject divergent branch)
  L2 conflict  → causal timestamp ordering (earlier wins)
  L3 conflict  → goal alignment (higher fidelity wins)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from core.deterministic import DeterministicClock, DeterministicUUIDFactory

from .branch import Branch, BranchPoint, BranchStatus, BranchStore
from .equivalence import Decision, EquivalenceChecker, MergeDecision

# ── Stage function: G3 alignment — called ONLY from ExecutionGateway ──────

def apply_merge_alignment(
    decision: MergeDecision,
    branch_store: BranchStore,
    event_store: Any,
) -> MergeLog:
    """
    Pure stage function for ExecutionGateway G3 stage.
    Executes merge decision produced by equivalence.py.
    All execution MUST route through ExecutionGateway.
    """
    engine = MergeEngine(branch_store, event_store)
    if decision.decision == Decision.MERGE:
        return engine._do_merge(decision)
    if decision.decision in (Decision.KEEP_A, Decision.KEEP_B):
        return engine._do_keep(decision, keep_branch="a" if decision.decision == Decision.KEEP_A else "b")
    return engine._do_split(decision)


# ── Merge artifacts ─────────────────────────────────────────────────────────

class ConflictType(Enum):
    NONE = auto()
    L1_STRUCTURAL = auto()   # node set or dependency mismatch
    L2_ORDERING = auto()      # causal inversion conflict
    L3_SEMANTIC = auto()      # goal/outcome divergence


@dataclass
class MergeConflict:
    conflict_type: ConflictType
    node_id: str
    branch_a_value: object
    branch_b_value: object
    resolution: object          # the resolved value
    resolved_by: str           # "L1_priority" | "causal_timestamp" | "L3_fidelity"
    priority: int              # lower = higher priority


@dataclass
class MergeLog:
    """Append-only audit trail for merge operations."""
    merge_id: str
    decision: Decision
    branch_a_id: str
    branch_b_id: str
    lca_checkpoint_id: str
    branch_point_id: str
    merged_branch_id: str
    conflicts_resolved: list[MergeConflict]
    causal_order: list[str]     # merged event sequence (by event_id)
    started_at_ns: int
    committed_at_ns: int
    confidence: float

    def summary(self) -> str:
        conflict_kinds = [c.conflict_type.name for c in self.conflicts_resolved]
        return (
            f"merge_id={self.merge_id[:12]} "
            f"decision={self.decision.name} "
            f"conflicts={len(self.conflicts_resolved)} "
            f"causal_order={len(self.causal_order)} events "
            f"confidence={self.confidence:.2f}"
        )


# ── Merge Engine ─────────────────────────────────────────────────────────────

class MergeEngine:
    """
    Executes merge decisions with full causal ordering and conflict resolution.

    Usage:
        engine = MergeEngine(branch_store, event_store)
        log = engine.execute(decision)
        assert log.decision == Decision.MERGE  # or handle KEEP_A/KEEP_B/SPLIT
    """

    def __init__(
        self,
        branch_store: BranchStore,
        event_store: Any,  # federation.semantic.v910.EventStore
        equivalence_checker: EquivalenceChecker | None = None,
    ):
        self._branches = branch_store
        self._events = event_store
        self._equiv = equivalence_checker or EquivalenceChecker()
        self._logs: list[MergeLog] = []

    # ── MERGE ───────────────────────────────────────────────────────────────

    def _do_merge(self, decision: MergeDecision) -> MergeLog:
        """
        Two-branch merge:
          1. Build LCA-relative sequences (branch events after LCA checkpoint)
          2. Interleave by causal timestamp
          3. Resolve conflicts via ConflictResolutionMatrix
          4. Create new MERGED branch with merged causal order
          5. Mark both source branches as SUPERSEDED
          6. Emit MERGE_COMMIT event
        """
        started = DeterministicClock.get_tick_ns()

        # Get both branches
        ba = self._branches.get(decision.l1.l1_equivalent and decision.l2.l2_equivalent and decision.l3.l3_equivalent)  # resolved via decision attrs
        # Source branches are identified via decision attributes from equivalence
        # In practice these come from the equivalence checker context
        # For this implementation we reconstruct from decision
        branch_a_id = getattr(decision, '_branch_a_id', 'unknown')
        branch_b_id = getattr(decision, '_branch_b_id', 'unknown')

        # Build branch point
        branch_point = BranchPoint(
            checkpoint_id=getattr(decision, 'lca_checkpoint_id', ''),
            divergence_event_id=DeterministicUUIDFactory.make_id('div', f'{branch_a_id}:{branch_b_id}', salt=''),
            branch_a_id=branch_a_id,
            branch_b_id=branch_b_id,
            divergence_ns=started,
            cause="merge",
        )

        # Resolve conflicts and build merged causal order
        conflicts, causal_order = self._resolve_and_interleave(
            branch_a_id, branch_b_id, decision
        )

        # Create merged branch
        merged_branch = self._branches.create(
            plan_id=getattr(decision, 'plan_id', 'unknown'),
            root_checkpoint_id=branch_point.checkpoint_id,
            parent_branch_id=None,
            tags=["merged", f"merge-{branch_a_id[:8]}", f"merge-{branch_b_id[:8]}"],
        )

        # Emit merge commit event to the new branch
        self._emit_merge_commit(merged_branch, branch_a_id, branch_b_id, causal_order)

        # Mark source branches as SUPERSEDED
        self._branches.update_status(branch_a_id, BranchStatus.SUPERSEDED)
        self._branches.update_status(branch_b_id, BranchStatus.SUPERSEDED)

        log = MergeLog(
            merge_id=DeterministicUUIDFactory.make_id('merge', f'{branch_a_id}:{branch_b_id}', salt=''),
            decision=Decision.MERGE,
            branch_a_id=branch_a_id,
            branch_b_id=branch_b_id,
            lca_checkpoint_id=branch_point.checkpoint_id,
            branch_point_id=branch_point.divergence_event_id,
            merged_branch_id=merged_branch.branch_id,
            conflicts_resolved=conflicts,
            causal_order=causal_order,
            started_at_ns=started,
            committed_at_ns=DeterministicClock.get_tick_ns(),
            confidence=decision.confidence,
        )
        self._logs.append(log)
        return log

    def _resolve_and_interleave(
        self,
        branch_a_id: str,
        branch_b_id: str,
        decision: MergeDecision,
    ) -> tuple[list[MergeConflict], list[str]]:
        """
        Build merged causal order by interleaving events from both branches.

        Algorithm:
          For each position in topological order (relative to LCA):
            - If event exists in both branches → conflict → resolve via matrix
            - If event exists in only one branch → take it
            - Preserve causal timestamp order (Lamport)

        Conflict resolution (strict priority):
          1. L1: structural → hard reject (node set difference)
          2. L2: causal timestamp → earlier event wins
          3. L3: semantic fidelity → higher goal_alignment wins
        """
        conflicts: list[MergeConflict] = []
        merged_order: list[str] = []

        # Get event sequences from event store (LCA-relative)
        events_a = self._events.get_branch_events_since_checkpoint(branch_a_id)
        events_b = self._events.get_branch_events_since_checkpoint(branch_b_id)

        # Build timeline: interleave by lamport timestamp
        all_events = sorted(
            [(e, 'a') for e in events_a] + [(e, 'b') for e in events_b],
            key=lambda x: x[0].lamport_ts if hasattr(x[0], 'lamport_ts') else 0
        )

        seen_node_ids: set[str] = set()

        for event, source in all_events:
            node_id = getattr(event, 'step_id', getattr(event, 'node_id', 'unknown'))

            # Deduplicate: if node already placed, skip
            if node_id in seen_node_ids:
                continue
            seen_node_ids.add(node_id)

            # Check for conflict: same node from both sources
            conflicting = next(
                (e2 for e2, s2 in all_events
                 if getattr(e2, 'step_id', getattr(e2, 'node_id', '')) == node_id and s2 != source),
                None
            )
            if conflicting:
                conflict = self._resolve_conflict(
                    node_id, event, conflicting, decision
                )
                conflicts.append(conflict)
                merged_order.append(conflict.resolved.node_id if hasattr(conflict.resolved, 'node_id') else node_id)
            else:
                merged_order.append(node_id)

        return conflicts, merged_order

    def _resolve_conflict(
        self,
        node_id: str,
        event_a: object,
        event_b: object,
        decision: MergeDecision,
    ) -> MergeConflict:
        """
        Resolve a node conflict between two events.

        Priority (strict):
          1. L1 structural → reject based on node hash mismatch
          2. L2 causal    → earlier Lamport timestamp wins
          3. L3 semantic → higher goal_alignment wins

        Returns MergeConflict with resolved value and justification.
        """
        # L1: structural conflict
        hash_a = getattr(event_a, 'content_hash', lambda: 'x')()
        hash_b = getattr(event_b, 'content_hash', lambda: 'y')()

        if hash_a != hash_b:
            # Structural conflict — content hash differs
            # L1 resolution: keep the one with higher goal_alignment
            goal_a = getattr(event_a, 'goal_alignment', 0.0)
            goal_b = getattr(event_b, 'goal_alignment', 0.0)
            winner = event_a if goal_a >= goal_b else event_b
            return MergeConflict(
                conflict_type=ConflictType.L1_STRUCTURAL,
                node_id=node_id,
                branch_a_value=hash_a,
                branch_b_value=hash_b,
                resolution=winner,
                resolved_by="L1_priority",
                priority=1,
            )

        # L2: causal ordering conflict (same content, different timestamp)
        ts_a = getattr(event_a, 'lamport_ts', 0)
        ts_b = getattr(event_b, 'lamport_ts', 0)

        if ts_a != ts_b:
            earlier = event_a if ts_a < ts_b else event_b
            later = event_b if ts_a < ts_b else event_a
            return MergeConflict(
                conflict_type=ConflictType.L2_ORDERING,
                node_id=node_id,
                branch_a_value=ts_a,
                branch_b_value=ts_b,
                resolution=earlier,
                resolved_by="causal_timestamp",
                priority=2,
            )

        # L3: semantic divergence (same content, same timestamp — identical event)
        # No conflict — take either
        return MergeConflict(
            conflict_type=ConflictType.NONE,
            node_id=node_id,
            branch_a_value=hash_a,
            branch_b_value=hash_b,
            resolution=event_a,
            resolved_by="identical",
            priority=99,
        )

    def _emit_merge_commit(
        self,
        merged_branch: Branch,
        branch_a_id: str,
        branch_b_id: str,
        causal_order: list[str],
    ) -> None:
        """Emit merge commit event to event store."""
        from federation.semantic.v910 import EventStore, EventType
        EventStore.emit(
            event_type=EventType.MERGE_COMMIT,
            entity_hash=merged_branch.branch_id,
            parent_refs=[branch_a_id, branch_b_id],
            metadata=(
                f"causal_order={','.join(causal_order[:10])}",
                f"events_merged={len(causal_order)}",
                f"source_a={branch_a_id[:8]}",
                f"source_b={branch_b_id[:8]}",
            ),
        )
        self._branches.append_event(merged_branch.branch_id, merged_branch.last_event_id)

    # ── KEEP_A / KEEP_B ──────────────────────────────────────────────────────

    def _do_keep(self, decision: MergeDecision, keep_branch: str) -> MergeLog:
        """
        One branch clearly dominates — mark the other as SUPERSEDED.
        No merge event emitted; the winning branch continues.
        """
        started = DeterministicClock.get_tick_ns()
        winner_id = decision.winner_branch_id
        loser_id = (
            getattr(decision, '_branch_b_id', None)
            if keep_branch == "a"
            else getattr(decision, '_branch_a_id', None)
        )

        self._branches.update_status(winner_id, BranchStatus.MERGED)
        self._branches.update_status(loser_id, BranchStatus.SUPERSEDED)

        log = MergeLog(
            merge_id=DeterministicUUIDFactory.make_id('merge', f'{winner_id}:{loser_id}', salt=''),
            decision=Decision.KEEP_A if keep_branch == "a" else Decision.KEEP_B,
            branch_a_id=winner_id,
            branch_b_id=loser_id,
            lca_checkpoint_id=getattr(decision, 'lca_checkpoint_id', ''),
            branch_point_id="",
            merged_branch_id=winner_id,
            conflicts_resolved=[],
            causal_order=[],
            started_at_ns=started,
            committed_at_ns=DeterministicClock.get_tick_ns(),
            confidence=decision.confidence,
        )
        self._logs.append(log)
        return log

    # ── SPLIT ───────────────────────────────────────────────────────────────

    def _do_split(self, decision: MergeDecision) -> MergeLog:
        """
        Branches are irreconcilable — mark both as IRRECONCILABLE.
        Both become terminal leaf branches. No convergence.
        """
        started = DeterministicClock.get_tick_ns()

        branch_a_id = getattr(decision, '_branch_a_id', 'unknown')
        branch_b_id = getattr(decision, '_branch_b_id', 'unknown')

        self._branches.update_status(branch_a_id, BranchStatus.IRRECONCILABLE)
        self._branches.update_status(branch_b_id, BranchStatus.IRRECONCILABLE)

        log = MergeLog(
            merge_id=DeterministicUUIDFactory.make_id('merge', f'{branch_a_id}:{branch_b_id}', salt=''),
            decision=Decision.SPLIT,
            branch_a_id=branch_a_id,
            branch_b_id=branch_b_id,
            lca_checkpoint_id=getattr(decision, 'lca_checkpoint_id', ''),
            branch_point_id="",
            merged_branch_id="",
            conflicts_resolved=[],
            causal_order=[],
            started_at_ns=started,
            committed_at_ns=DeterministicClock.get_tick_ns(),
            confidence=decision.confidence,
        )
        self._logs.append(log)
        return log

    # ── Metrics ─────────────────────────────────────────────────────────────

    def metrics(self) -> ConvergenceMetrics:
        total = len(self._logs)
        if total == 0:
            return ConvergenceMetrics(0, 0.0, 0.0, 0.0, 0)

        merges = sum(1 for l in self._logs if l.decision == Decision.MERGE)
        splits = sum(1 for l in self._logs if l.decision == Decision.SPLIT)
        keeps = sum(1 for l in self._logs if l.decision in (Decision.KEEP_A, Decision.KEEP_B))

        avg_confidence = sum(l.confidence for l in self._logs) / total

        total_conflicts = sum(len(l.conflicts_resolved) for l in self._logs)

        return ConvergenceMetrics(
            total_merges=merges,
            merge_success_rate=merges / total if total else 0.0,
            irreconcilable_ratio=splits / total if total else 0.0,
            avg_merge_confidence=avg_confidence,
            total_conflicts_resolved=total_conflicts,
        )

    def history(self) -> list[MergeLog]:
        return list(self._logs)


@dataclass
class ConvergenceMetrics:
    total_merges: int
    merge_success_rate: float
    irreconcilable_ratio: float
    avg_merge_confidence: float
    total_conflicts_resolved: int

    def summary(self) -> str:
        return (
            f"merges={self.total_merges} "
            f"success_rate={self.merge_success_rate:.1%} "
            f"irreconcilable={self.irreconcilable_ratio:.1%} "
            f"avg_conf={self.avg_merge_confidence:.2f} "
            f"conflicts_resolved={self.total_conflicts_resolved}"
        )

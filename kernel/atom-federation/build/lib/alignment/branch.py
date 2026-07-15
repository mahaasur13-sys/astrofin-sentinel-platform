"""
branch.py — v10.1 Causal Convergence Layer

Data models for branching-aware execution.

Key concepts:
  Branch — a causal history of events from a shared checkpoint.
  Leaf — terminal branch (merged or irreconcilable).
  LCA — Lowest Common Ancestor (shared checkpoint of two branches).
  Converged state — the result of merging two branches.

Invariant (preserved from v10.0):
  Events are NEVER deleted. Merge creates new committed events;
  both branch histories are preserved in the audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from core.deterministic import DeterministicClock, DeterministicUUIDFactory


class BranchStatus(Enum):
    ACTIVE = auto()      # still accepting events
    MERGING = auto()      # convergence protocol in progress
    MERGED = auto()       # merged into another branch (committed)
    IRRECONCILABLE = auto()  # SPLIT decision — terminal leaf
    SUPERSEDED = auto()  # another branch committed first (stale)


@dataclass(frozen=True)
class BranchPoint:
    """
    A divergence point: the checkpoint from which two branches diverged.
    
    Immutable: the point of divergence is a historical fact.
    """
    checkpoint_id: str          # shared checkpoint before divergence
    divergence_event_id: str     # event that triggered the branch
    branch_a_id: str
    branch_b_id: str
    divergence_ns: int           # nanoseconds timestamp
    cause: str                   # human-readable reason


@dataclass(frozen=True)
class Branch:
    """
    A causal history of committed events, originating from a shared checkpoint.
    
    Branch is immutable — once created it is never modified.
    New events are appended; the branch_id is the identity.
    """
    branch_id: str
    plan_id: str                # the original plan this branch serves
    root_checkpoint_id: str      # shared ancestor checkpoint
    parent_branch_id: str | None  # branch this branched from (for rollback branches)
    created_at_ns: int
    status: BranchStatus = BranchStatus.ACTIVE
    event_count: int = 0
    node_count: int = 0
    last_event_id: str = ""
    last_updated_ns: int = 0
    tags: tuple[str, ...] = field(default_factory=tuple)  # e.g. "rollback", "shadow", "merged"

    def is_live(self) -> bool:
        return self.status in (BranchStatus.ACTIVE, BranchStatus.MERGING)

    def is_terminal(self) -> bool:
        return self.status in (BranchStatus.MERGED, BranchStatus.IRRECONCILABLE, BranchStatus.SUPERSEDED)

    def is_ancestor_of(self, other: Branch) -> bool:
        """True if self is in the causal ancestry of other."""
        # Causal ancestry: walk up parent_branch_id chain
        current = other
        while current.parent_branch_id is not None:
            if current.parent_branch_id == self.branch_id:
                return True
            # Walk further up (simplified — real impl would use branch store)
            break
        return False


@dataclass
class BranchStore:
    """
    Immutable branch registry.
    Branches are never deleted; only their status changes.
    """
    _by_id: dict[str, Branch] = field(default_factory=dict)
    _by_plan: dict[str, list[str]] = field(default_factory=dict)  # plan_id → [branch_ids]
    _lock: __import__("threading").RLock = field(
        default_factory=__import__("threading").RLock
    )

    def create(
        self,
        plan_id: str,
        root_checkpoint_id: str,
        parent_branch_id: str | None = None,
        tags: list[str] | None = None,
    ) -> Branch:
        branch = Branch(
            branch_id=DeterministicUUIDFactory.make_id('branch', plan_id, salt=''),
            plan_id=plan_id,
            root_checkpoint_id=root_checkpoint_id,
            parent_branch_id=parent_branch_id,
            created_at_ns=DeterministicClock.get_tick_ns(),
            tags=tuple(tags or []),
        )
        with self._lock:
            self._by_id[branch.branch_id] = branch
            self._by_plan.setdefault(plan_id, []).append(branch.branch_id)
        return branch

    def get(self, branch_id: str) -> Branch | None:
        return self._by_id.get(branch_id)

    def by_plan(self, plan_id: str) -> list[Branch]:
        with self._lock:
            return [self._by_id[bid] for bid in self._by_plan.get(plan_id, []) if bid in self._by_id]

    def update_status(self, branch_id: str, status: BranchStatus) -> Branch:
        with self._lock:
            b = self._by_id[branch_id]
            updated = Branch(
                branch_id=b.branch_id,
                plan_id=b.plan_id,
                root_checkpoint_id=b.root_checkpoint_id,
                parent_branch_id=b.parent_branch_id,
                created_at_ns=b.created_at_ns,
                status=status,
                event_count=b.event_count,
                node_count=b.node_count,
                last_event_id=b.last_event_id,
                last_updated_ns=DeterministicClock.get_tick_ns(),
                tags=b.tags,
            )
            self._by_id[branch_id] = updated
            return updated

    def append_event(self, branch_id: str, event_id: str) -> None:
        with self._lock:
            b = self._by_id[branch_id]
            updated = Branch(
                branch_id=b.branch_id,
                plan_id=b.plan_id,
                root_checkpoint_id=b.root_checkpoint_id,
                parent_branch_id=b.parent_branch_id,
                created_at_ns=b.created_at_ns,
                status=b.status,
                event_count=b.event_count + 1,
                node_count=b.node_count,
                last_event_id=event_id,
                last_updated_ns=DeterministicClock.get_tick_ns(),
                tags=b.tags,
            )
            self._by_id[branch_id] = updated

    def find_lca(self, branch_a: str, branch_b: str) -> str | None:
        """
        Find Lowest Common Ancestor of two branches.
        Walks the parent chain of both branches to find shared checkpoint.
        Returns root_checkpoint_id of LCA if found, else None.
        """
        with self._lock:
            def parent_chain(bid: str):
                chain = []
                current = bid
                for _ in range(100):  # bounded chain depth
                    b = self._by_id.get(current)
                    if b is None:
                        break
                    chain.append(b.root_checkpoint_id)
                    if b.parent_branch_id is None:
                        break
                    current = b.parent_branch_id
                return chain

            chain_a = set(parent_chain(branch_a))
            for cp in parent_chain(branch_b):
                if cp in chain_a:
                    return cp
            return None

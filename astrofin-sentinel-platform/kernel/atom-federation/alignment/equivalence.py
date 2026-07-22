"""
equivalence.py — v10.1 Causal Convergence Layer

Determines equivalence or conflict between two branches:
  L1 equivalence — structural (DAG shape, node set)
  L2 equivalence — causal (execution order, dependency pattern)
  L3 equivalence — semantic (goal alignment, outcome similarity)

merge_decision(A, B, threshold) → Decision enum.

All comparisons are against the Lowest Common Ancestor (LCA) checkpoint,
not against each other — this prevents comparison bias.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Decision(Enum):
    MERGE = auto()       # branches are compatible → converge
    KEEP_A = auto()      # branch A dominates; discard B
    KEEP_B = auto()      # branch B dominates; discard A
    SPLIT = auto()       # irreconcilable → both become terminal leaves


@dataclass
class L1Equivalence:
    """L1 — structural equivalence (planned vs runtime graph)."""
    structural_similarity: float   # 0..1 (1 = identical structure)
    node_set_delta: int           # nodes added/removed vs LCA
    dep_pattern_delta: float      # dependency pattern change
    l1_equivalent: bool          # structural_similarity >= threshold


@dataclass
class L2Equivalence:
    """L2 — causal equivalence (execution order vs planned topological order)."""
    causal_similarity: float      # 0..1 (1 = identical causal pattern)
    inversion_delta: int         # additional inversions vs LCA
    ordering_divergence: float   # fraction of nodes with changed order
    l2_equivalent: bool


@dataclass
class L3Equivalence:
    """L3 — semantic equivalence (goal alignment vs outcome fidelity)."""
    goal_alignment: float         # 0..1 (1 = goal perfectly preserved)
    semantic_distance: float     # 0..1 (1 = maximally divergent outcomes)
    l3_equivalent: bool


@dataclass
class MergeDecision:
    """
    Formal merge decision with full justification trail.

    Invariant:
      l1_equivalent and l2_equivalent and l3_equivalent → decision == MERGE
      l1_conflict or (l2_conflict and not l3_equivalent) → decision in {KEEP_A, KEEP_B, SPLIT}
    """
    decision: Decision
    l1: L1Equivalence
    l2: L2Equivalence
    l3: L3Equivalence

    # Merge direction when decision != SPLIT
    winner_branch_id: str | None = None   # which branch survives (if KEEP_A/KEEP_B)
    merged_branch_id: str | None = None    # new branch id (if MERGE)
    branch_point_id: str | None = None     # BranchPoint record

    # Conflicts found
    l1_conflict: bool = False    # True → hard structural conflict
    l2_conflict: bool = False     # True → causal inversion conflict
    l3_conflict: bool = False     # True → semantic divergence conflict

    # Confidence
    confidence: float = 0.0       # 0..1

    def is_mergeable(self) -> bool:
        return self.decision == Decision.MERGE

    def summary(self) -> str:
        return (
            f"[{self.decision.name}] "
            f"L1={'equiv' if self.l1.l1_equivalent else 'conflict'} "
            f"L2={'equiv' if self.l2.l2_equivalent else 'conflict'} "
            f"L3={'equiv' if self.l3.l3_equivalent else 'conflict'} "
            f"conf={self.confidence:.2f}"
        )


class EquivalenceChecker:
    """
    Computes L1/L2/L3 equivalence between two branches.

    All comparisons are against the LCA (shared checkpoint) to ensure
    we measure divergence from the known-good state, not relative bias.

    Configuration:
      structural_threshold — L1 equivalence threshold (default 0.80)
      causal_threshold    — L2 equivalence threshold (default 0.75)
      semantic_threshold  — L3 equivalence threshold (default 0.70)
      conflict_threshold   — above this → hard conflict (default 0.40)
    """

    WEIGHTS = (0.30, 0.30, 0.40)  # w1=L1, w2=L2, w3=L3

    def __init__(
        self,
        structural_threshold: float = 0.80,
        causal_threshold: float = 0.75,
        semantic_threshold: float = 0.70,
        conflict_threshold: float = 0.40,
    ):
        self.structural_threshold = structural_threshold
        self.causal_threshold = causal_threshold
        self.semantic_threshold = semantic_threshold
        self.conflict_threshold = conflict_threshold

    def compare(
        self,
        branch_a_summary: BranchSummary,
        branch_b_summary: BranchSummary,
        lca_checkpoint: CheckpointSnapshot,
    ) -> MergeDecision:
        """
        Compare two branches against their shared LCA checkpoint.

        Args:
            branch_a_summary: summary of branch A (nodes, deps, semantic state)
            branch_b_summary: summary of branch B
            lca_checkpoint: shared checkpoint (lowest common ancestor)

        Returns:
            MergeDecision with full equivalence analysis
        """
        # ── L1: Structural comparison ───────────────────────────────────
        l1 = self._compare_l1(branch_a_summary, branch_b_summary, lca_checkpoint)

        # ── L2: Causal comparison ───────────────────────────────────────
        l2 = self._compare_l2(branch_a_summary, branch_b_summary, lca_checkpoint)

        # ── L3: Semantic comparison ─────────────────────────────────────
        l3 = self._compare_l3(branch_a_summary, branch_b_summary, lca_checkpoint)

        # ── Conflict detection ──────────────────────────────────────────
        l1_conflict = l1.structural_similarity < self.conflict_threshold
        l2_conflict = l2.causal_similarity < self.conflict_threshold
        l3_conflict = l3.semantic_distance > (1.0 - self.conflict_threshold)

        # ── Merge decision logic ─────────────────────────────────────────
        # Rule 1: Hard L1 conflict → SPLIT (structural irreconcilable)
        if l1_conflict:
            decision = self._decide_by_semantic(l3, branch_a_summary, branch_b_summary)
            return MergeDecision(
                decision=decision,
                l1=l1, l2=l2, l3=l3,
                l1_conflict=True, l2_conflict=l2_conflict, l3_conflict=l3_conflict,
                confidence=0.95,
            )

        # Rule 2: All three equivalent → MERGE
        if l1.l1_equivalent and l2.l2_equivalent and l3.l3_equivalent:
            # Compute composite confidence
            confidence = (
                0.30 * l1.structural_similarity +
                0.30 * l2.causal_similarity +
                0.40 * (1.0 - l3.semantic_distance)
            )
            return MergeDecision(
                decision=Decision.MERGE,
                l1=l1, l2=l2, l3=l3,
                l1_conflict=False, l2_conflict=False, l3_conflict=False,
                confidence=confidence,
            )

        # Rule 3: L1+L2 equivalent but L3 diverged → semantic dominance
        # The branch with higher goal_alignment wins
        if l1.l1_equivalent and l2.l2_equivalent and not l3.l3_equivalent:
            if branch_a_summary.goal_alignment >= branch_b_summary.goal_alignment:
                return MergeDecision(
                    decision=Decision.KEEP_A,
                    l1=l1, l2=l2, l3=l3,
                    winner_branch_id=branch_a_summary.branch_id,
                    l1_conflict=False, l2_conflict=False, l3_conflict=True,
                    confidence=0.80,
                )
            else:
                return MergeDecision(
                    decision=Decision.KEEP_B,
                    l1=l1, l2=l2, l3=l3,
                    winner_branch_id=branch_b_summary.branch_id,
                    l1_conflict=False, l2_conflict=False, l3_conflict=True,
                    confidence=0.80,
                )

        # Rule 4: L2 conflict but L3 equivalent → causal dominance
        # Use causal similarity to decide
        if l2_conflict and l3.l3_equivalent:
            if l2.causal_similarity >= self.causal_threshold:
                return MergeDecision(
                    decision=Decision.MERGE,
                    l1=l1, l2=l2, l3=l3,
                    l1_conflict=False, l2_conflict=False, l3_conflict=False,
                    confidence=0.70,
                )
            else:
                # Causal conflict too severe → SPLIT
                return MergeDecision(
                    decision=Decision.SPLIT,
                    l1=l1, l2=l2, l3=l3,
                    l1_conflict=False, l2_conflict=True, l3_conflict=False,
                    confidence=0.85,
                )

        # Rule 5: Partial equivalence → weighted composite decision
        composite = self._composite_score(l1, l2, l3)

        if composite >= 0.65:
            decision = Decision.MERGE
        elif composite >= 0.40:
            # Partial: decide by which layer has strongest equivalence
            if l3.l3_equivalent and not l1.l1_equivalent:
                decision = Decision.KEEP_A if branch_a_summary.goal_alignment >= branch_b_summary.goal_alignment else Decision.KEEP_B
            elif l1.l1_equivalent:
                decision = Decision.KEEP_A if l1.structural_similarity >= l2.causal_similarity else Decision.KEEP_B
            else:
                decision = Decision.SPLIT
        else:
            decision = Decision.SPLIT

        winner = None
        if decision in (Decision.KEEP_A, Decision.KEEP_B):
            winner = branch_a_summary.branch_id if decision == Decision.KEEP_A else branch_b_summary.branch_id

        confidence = (
            0.25 * l1.structural_similarity +
            0.25 * l2.causal_similarity +
            0.50 * (1.0 - l3.semantic_distance)
        )

        return MergeDecision(
            decision=decision,
            l1=l1, l2=l2, l3=l3,
            winner_branch_id=winner,
            l1_conflict=l1_conflict,
            l2_conflict=l2_conflict,
            l3_conflict=l3_conflict,
            confidence=confidence,
        )

    def _compare_l1(
        self,
        a: BranchSummary,
        b: BranchSummary,
        lca: CheckpointSnapshot,
    ) -> L1Equivalence:
        """L1: structural equivalence vs LCA."""
        # Node set similarity (Jaccard)
        lca_nodes = set(lca.node_ids)
        a_nodes = set(a.node_ids)
        b_nodes = set(b.node_ids)

        # Similarity to LCA
        a_jaccard = len(a_nodes & lca_nodes) / max(len(a_nodes | lca_nodes), 1)
        b_jaccard = len(b_nodes & lca_nodes) / max(len(b_nodes | lca_nodes), 1)

        structural_similarity = (a_jaccard + b_jaccard) / 2.0

        # Node set delta (how many nodes diverged from LCA)
        node_set_delta = len(a_nodes ^ b_nodes)

        # Dep pattern similarity
        a_deps = set(a.deps_pattern)  # frozenset of (from, to) tuples
        b_deps = set(b.deps_pattern)
        lca_deps = set(lca.deps_pattern)

        dep_jaccard_a = len(a_deps & lca_deps) / max(len(a_deps | lca_deps), 1)
        dep_jaccard_b = len(b_deps & lca_deps) / max(len(b_deps | lca_deps), 1)
        dep_pattern_delta = 1.0 - (dep_jaccard_a + dep_jaccard_b) / 2.0

        return L1Equivalence(
            structural_similarity=structural_similarity,
            node_set_delta=node_set_delta,
            dep_pattern_delta=dep_pattern_delta,
            l1_equivalent=structural_similarity >= self.structural_threshold,
        )

    def _compare_l2(
        self,
        a: BranchSummary,
        b: BranchSummary,
        lca: CheckpointSnapshot,
    ) -> L2Equivalence:
        """L2: causal equivalence vs LCA."""
        # Inversion count vs LCA
        a_inversions = getattr(a, 'inversion_count', 0)
        b_inversions = getattr(b, 'inversion_count', 0)
        lca_inversions = getattr(lca, 'inversion_count', 0)

        inversion_delta = abs((a_inversions - lca_inversions) - (b_inversions - lca_inversions))

        # Ordering divergence: fraction of nodes with different topological position
        lca_order = {n: i for i, n in enumerate(lca.topological_order or [])}
        a_order = {n: i for i, n in enumerate(a.topological_order or [])}
        b_order = {n: i for i, n in enumerate(b.topological_order or [])}

        all_nodes = set(lca_order.keys()) | set(a_order.keys()) | set(b_order.keys())
        order_changes_a = sum(1 for n in all_nodes if lca_order.get(n, -1) != a_order.get(n, -2))
        order_changes_b = sum(1 for n in all_nodes if lca_order.get(n, -1) != b_order.get(n, -2))
        ordering_divergence = (order_changes_a + order_changes_b) / (2 * max(len(all_nodes), 1))

        causal_similarity = 1.0 - ordering_divergence

        return L2Equivalence(
            causal_similarity=causal_similarity,
            inversion_delta=inversion_delta,
            ordering_divergence=ordering_divergence,
            l2_equivalent=causal_similarity >= self.causal_threshold,
        )

    def _compare_l3(
        self,
        a: BranchSummary,
        b: BranchSummary,
        lca: CheckpointSnapshot,
    ) -> L3Equivalence:
        """L3: semantic equivalence vs LCA."""
        goal_alignment = (a.goal_alignment + b.goal_alignment) / 2.0
        semantic_distance = 1.0 - goal_alignment

        return L3Equivalence(
            goal_alignment=goal_alignment,
            semantic_distance=semantic_distance,
            l3_equivalent=goal_alignment >= self.semantic_threshold,
        )

    def _decide_by_semantic(self, l3: L3Equivalence, a: BranchSummary, b: BranchSummary) -> Decision:
        """When L1 hard conflict — use L3 to break tie."""
        if l3.l3_equivalent:
            return Decision.MERGE
        if a.goal_alignment >= b.goal_alignment:
            return Decision.KEEP_A
        return Decision.KEEP_B

    def _composite_score(self, l1: L1Equivalence, l2: L2Equivalence, l3: L3Equivalence) -> float:
        w1, w2, w3 = self.WEIGHTS
        return w1 * l1.structural_similarity + w2 * l2.causal_similarity + w3 * (1.0 - l3.semantic_distance)


# ── Supporting data classes ────────────────────────────────────────────────────

@dataclass(frozen=True)
class CheckpointSnapshot:
    """Immutable snapshot of a checkpoint's structural state."""
    checkpoint_id: str
    node_ids: frozenset[str]
    deps_pattern: frozenset[tuple[str, str]]
    topological_order: tuple[str, ...]
    inversion_count: int = 0
    goal_alignment: float = 1.0


@dataclass(frozen=True)
class BranchSummary:
    """
    Compressed summary of a branch's state for equivalence checking.
    Built from DriftEngine snapshot + branch metadata.
    """
    branch_id: str
    node_ids: frozenset[str]
    deps_pattern: frozenset[tuple[str, str]]  # set of (from_id, to_id)
    topological_order: tuple[str, ...]
    inversion_count: int
    goal_alignment: float   # L3 semantic fidelity score (0..1)
    event_count: int
    last_updated_ns: int

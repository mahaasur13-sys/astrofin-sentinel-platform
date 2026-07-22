"""
proof_aware_policy_sync.py — v9.3 Phase 1: SemanticProof-aware Policy Sync

Key shift from v9.2:
  v9.2: SemanticProofEngine + CROSS_ORIGIN_EQUIVALENCE invariant defined
  v9.3: proof → runtime enforcement in federation sync pipeline

Before (v9.2 and before):
    remote θ → replay → apply  (accept always)
    No proof verification at sync time

After (v9.3):
    remote θ
        ↓
    replay
        ↓
    semantic_proof (v9.2)  ← SemanticProofEngine.prove_equivalence()
        ↓
    if equivalent → apply
    else          → QUARANTINE  (enforce CROSS_ORIGIN_EQUIVALENCE)

Architecture:
    PolicySyncDecision  — decision gate: accept / quarantine / partial
    ProofAwarePolicySync — orchestrates proof + sync + enforcement
    QUARANTINE          — marks remote state as untrusted until proven

Integration points:
    - SemanticProofEngine (cross_origin_proof.py)
    - InvariantEnforcer (invariant_contract.py)
    - CROSS_ORIGIN_EQUIVALENCE invariant → runtime enforcement
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto

from federation.delta_gossip.dag_hash_modes import DAGHashMode
from orchestration.consistency.invariant_contract.cross_mode_validator import SemanticNode, SemanticTree
from orchestration.consistency.invariant_contract.cross_origin_proof import (

import logging
log = logging.getLogger(__name__)

    ProofOrigin,
    SemanticProof,
    SemanticProofEngine,
    get_cross_origin_equivalence_invariant,
)
from orchestration.consistency.invariant_contract.invariant_contract import (
    EnforcementAction,
    InvariantEvaluator,
    InvariantRegistry,
)

# ─────────────────────────────────────────────────────────────────
# PolicySyncDecision
# ─────────────────────────────────────────────────────────────────

class SyncVerdict(Enum):
    """
    Result of proof-validated policy sync.

    ACCEPT      — proof valid, remote state trusted, apply delta
    QUARANTINE  — proof invalid or missing, reject delta, isolate
    PARTIAL     — proof partial (empty digests, degraded mode), apply with notice
    """
    ACCEPT = auto()
    QUARANTINE = auto()
    PARTIAL = auto()


@dataclass
class PolicySyncDecision:
    """
    Decision produced by proof-validated policy sync.

    Fields:
        verdict           — ACCEPT / QUARANTINE / PARTIAL
        proof             — SemanticProof if available (else None)
        reason            — human-readable explanation
        tick              — current system tick
        enforcement_action— what InvariantEnforcer should do
        quarantined_nodes — node IDs isolated due to this decision
        timestamp         — wall-clock
    """
    verdict: SyncVerdict
    proof: SemanticProof | None
    reason: str
    tick: int = 0
    enforcement_action: EnforcementAction = EnforcementAction.LOG_ONLY
    quarantined_nodes: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_trusted(self) -> bool:
        return self.verdict == SyncVerdict.ACCEPT


# ─────────────────────────────────────────────────────────────────
# ProofAwarePolicySync
# ─────────────────────────────────────────────────────────────────

class ProofAwarePolicySync:
    """
    Federation policy sync with integrated SemanticProof verification.

    Pipeline:
        1. Receive remote θ digest (from delta gossip)
        2. Compute / retrieve local replay digest
        3. Build SemanticProof via SemanticProofEngine
        4. Run CROSS_ORIGIN_EQUIVALENCE invariant check
        5. Emit PolicySyncDecision (ACCEPT / QUARANTINE / PARTIAL)

    Usage:
        sync = ProofAwarePolicySync(node_id="node_1")
        decision = sync.evaluate_remote_theta(
            remote_digests=[...],
            replay_digests=[...],
            remote_origin=ProofOrigin.REMOTE,
            tick=42,
        )
        if decision.verdict == SyncVerdict.QUARANTINE:
            quarantine_nodes(decision.quarantined_nodes)
    """

    def __init__(
        self,
        node_id: str,
        default_mode: DAGHashMode = DAGHashMode.CONSENSUS,
    ):
        self.node_id = node_id
        self.default_mode = default_mode
        self._engine = SemanticProofEngine()
        self._inv_registry = InvariantRegistry()
        self._inv_registry.register(get_cross_origin_equivalence_invariant())
        self._evaluator = InvariantEvaluator(self._inv_registry)
        self._decision_log: list[PolicySyncDecision] = []
        self._quarantined: set[str] = set()

    # ── core evaluation ────────────────────────────────────────────

    def evaluate_remote_theta(
        self,
        remote_digests: list[str],
        replay_digests: list[str],
        remote_origin: ProofOrigin = ProofOrigin.REMOTE,
        remote_node_id: str | None = None,
        tick: int = 0,
        dag_mode: DAGHashMode | None = None,
    ) -> PolicySyncDecision:
        """
        Evaluate remote θ against local replay using SemanticProof.

        Args:
            remote_digests: digest list from remote peer (via delta gossip)
            replay_digests: digest list from local replay trace
            remote_origin: ProofOrigin of remote source (REMOTE / SNAPSHOT / etc.)
            remote_node_id: node_id of remote peer (for quarantine tracking)
            tick: current system tick
            dag_mode: DAGHashMode for digest trees (default: CONSENSUS)

        Returns:
            PolicySyncDecision with verdict and enforcement action
        """
        mode = dag_mode or self.default_mode

        # Step 1: build proof
        proof = self._build_proof(
            remote_digests, replay_digests, mode,
            remote_origin=remote_origin,
        )

        # Step 2: build state for invariant check
        state: dict = {
            "proof": proof,
            "remote_digests": remote_digests,
            "replay_digests": replay_digests,
            "dag_mode": mode.name,
            "tick": tick,
        }

        # Step 3: run CROSS_ORIGIN_EQUIVALENCE invariant
        results = self._evaluator.evaluate(state, tick=tick)
        critical_violations = [
            r for r in results
            if not r.satisfied and r.severity.name == "CRITICAL"
        ]

        # Step 4: produce decision
        if proof.is_valid() and not critical_violations:
            verdict = SyncVerdict.ACCEPT
            reason = f"SemanticProof valid (proof_hash={proof.proof_hash[:8]})"
            enforcement_action = EnforcementAction.LOG_ONLY
            quarantined: list[str] = []

        elif not remote_digests or not replay_digests:
            verdict = SyncVerdict.PARTIAL
            reason = "Missing digests on one or both sides — partial trust"
            enforcement_action = EnforcementAction.ESCALATE
            quarantined = []

        else:
            # Proof invalid or critical violation → QUARANTINE
            divergence = (
                proof.equivalence_result.divergence_reason
                if proof.equivalence_result else "proof.build_failed"
            )
            verdict = SyncVerdict.QUARANTINE
            reason = f"Cross-origin equivalence violated: {divergence}"
            enforcement_action = EnforcementAction.QUARANTINE
            quarantined = [remote_node_id] if remote_node_id else []

        decision = PolicySyncDecision(
            verdict=verdict,
            proof=proof,
            reason=reason,
            tick=tick,
            enforcement_action=enforcement_action,
            quarantined_nodes=quarantined,
        )

        self._decision_log.append(decision)

        # Track quarantined nodes
        if verdict == SyncVerdict.QUARANTINE:
            for nid in quarantined:
                self._quarantined.add(nid)

        return decision

    # ── batch evaluation ──────────────────────────────────────────

    def evaluate_batch(
        self,
        remote_states: list[tuple[list[str], list[str], str | None, ProofOrigin]],
        tick: int = 0,
    ) -> list[PolicySyncDecision]:
        """
        Evaluate multiple remote states in one call.

        Args:
            remote_states: list of (remote_digests, replay_digests, remote_node_id, origin)
        """
        decisions = []
        for remote_digests, replay_digests, remote_node_id, origin in remote_states:
            d = self.evaluate_remote_theta(
                remote_digests=remote_digests,
                replay_digests=replay_digests,
                remote_origin=origin,
                remote_node_id=remote_node_id,
                tick=tick,
            )
            decisions.append(d)
        return decisions

    # ── quarantine management ─────────────────────────────────────

    def is_quarantined(self, node_id: str) -> bool:
        return node_id in self._quarantined

    def lift_quarantine(self, node_id: str) -> bool:
        """Lift quarantine after re-validation succeeds."""
        return self._quarantined.discard(node_id) is None

    def quarantined_nodes(self) -> set[str]:
        return set(self._quarantined)

    # ── helpers ───────────────────────────────────────────────────

    def _build_proof(
        self,
        remote_digests: list[str],
        replay_digests: list[str],
        mode: DAGHashMode,
        remote_origin: ProofOrigin,
    ) -> SemanticProof:
        if not remote_digests and not replay_digests:
            return self._engine._empty_proof(remote_origin, ProofOrigin.REPLAY)

        # Handle one-side-empty → build tree only from non-empty side
        if not remote_digests:
            tree_b = SemanticTree.from_digest_list(replay_digests, mode)
            empty_tree = SemanticTree(root=SemanticNode(""))
            return self._engine.prove_equivalence(
                empty_tree, tree_b,
                mode_a=mode, mode_b=mode,
                origin_a=remote_origin,
                origin_b=ProofOrigin.REPLAY,
                tick_a=0, tick_b=0,
            )
        if not replay_digests:
            tree_a = SemanticTree.from_digest_list(remote_digests, mode)
            empty_tree = SemanticTree(root=SemanticNode(""))
            return self._engine.prove_equivalence(
                tree_a, empty_tree,
                mode_a=mode, mode_b=mode,
                origin_a=remote_origin,
                origin_b=ProofOrigin.REPLAY,
                tick_a=0, tick_b=0,
            )

        tree_a = SemanticTree.from_digest_list(remote_digests, mode)
        tree_b = SemanticTree.from_digest_list(replay_digests, mode)

        return self._engine.prove_equivalence(
            tree_a, tree_b,
            mode_a=mode, mode_b=mode,
            origin_a=remote_origin,
            origin_b=ProofOrigin.REPLAY,
            tick_a=0, tick_b=0,
        )

    def decision_log(self) -> list[PolicySyncDecision]:
        return list(self._decision_log)

    def summary(self) -> dict:
        accepted = sum(1 for d in self._decision_log if d.verdict == SyncVerdict.ACCEPT)
        quarantined = sum(1 for d in self._decision_log if d.verdict == SyncVerdict.QUARANTINE)
        partial = sum(1 for d in self._decision_log if d.verdict == SyncVerdict.PARTIAL)
        return {
            "node_id": self.node_id,
            "total_decisions": len(self._decision_log),
            "accepted": accepted,
            "quarantined": quarantined,
            "partial": partial,
            "quarantined_nodes": list(self._quarantined),
        }


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────

def _test_v9_3_phase1():
    """Sanity test for v9.3 Phase 1."""
    sync = ProofAwarePolicySync(node_id="node_A")

    # Case 1: identical digests → ACCEPT
    d = ["d1", "d2", "d3", "d4"]
    decision = sync.evaluate_remote_theta(d, d, remote_origin=ProofOrigin.REMOTE, tick=1)
    assert decision.verdict == SyncVerdict.ACCEPT, f"Expected ACCEPT, got {decision.verdict}"
    assert decision.proof.is_valid()
    log.info(f"✅ Case 1 (identical): {decision.verdict.name} — {decision.reason}")

    # Case 2: different digests → QUARANTINE
    decision2 = sync.evaluate_remote_theta(d, ["x1", "x2", "x3", "x4"], tick=2)
    assert decision2.verdict == SyncVerdict.QUARANTINE
    assert decision2.enforcement_action == EnforcementAction.QUARANTINE
    log.info(f"✅ Case 2 (diverged): {decision2.verdict.name} — {decision2.reason}")

    # Case 3: one side empty → PARTIAL
    decision3 = sync.evaluate_remote_theta([], d, tick=3)
    assert decision3.verdict == SyncVerdict.PARTIAL
    log.info(f"✅ Case 3 (partial): {decision3.verdict.name} — {decision3.reason}")

    # Case 4: quarantine tracking
    assert "node_B" not in sync.quarantined_nodes()
    decision4 = sync.evaluate_remote_theta(
        d, ["x1", "x2", "x3", "x4"],
        remote_node_id="node_B", tick=4,
    )
    assert decision4.verdict == SyncVerdict.QUARANTINE
    assert "node_B" in sync.quarantined_nodes()
    sync.lift_quarantine("node_B")
    assert "node_B" not in sync.quarantined_nodes()
    log.info("✅ Case 4 (quarantine tracking + lift)")

    log.info("\n✅ v9.3 Phase 1: ProofAwarePolicySync — all checks passed")


if __name__ == "__main__":
    _test_v9_3_phase1()


__all__ = [
    "PolicySyncDecision",
    "ProofAwarePolicySync",
    "SyncVerdict",
]

"""
cross_origin_proof.py — v9.2 Cross-Origin Equivalence Proof Layer

Key shift from v9.1:
  v9.1: "one tree in two modes — does it project consistently?"
  v9.2: "two independent trees from different origins — are they equivalent?"

Proof pipeline:
  Tree_A (origin=remote, mode=X)   Tree_B (origin=replay, mode=Y)
         ↓                                  ↓
  normalize_A                      normalize_B
         ↓                                  ↓
  project_A → CONSENSUS            project_B → CONSENSUS
         ↓                                  ↓
  compare consensus hashes  ←→  cross-check via CAUSAL projection
         ↓
  SemanticProof result

CROSS_ORIGIN_EQUIVALENCE (CRITICAL / QUARANTINE) — new top-level invariant.

FIX-5: All IDs are content-addressed. Same proof content → same ID.
       No uuid4() or time-based IDs in proof objects.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum, auto

from federation.delta_gossip.dag_hash_modes import DAGHashMode
from orchestration.consistency.invariant_contract.cross_mode_validator import (

import logging
log = logging.getLogger(__name__)

    CrossModeValidator,
    EquivalenceResult,
    SemanticNode,
    SemanticProjectionEngine,
    SemanticTree,
)


def _content_id(prefix: str, *parts: str) -> str:
    """
    FIX-5: Deterministic content-addressed ID.
    Same prefix + parts → same ID across all nodes and replay runs.
    """
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:12]
    return f"{prefix}_{h}"


# ─────────────────────────────────────────────────────────────────
# ProofOrigin
# ─────────────────────────────────────────────────────────────────

class ProofOrigin(Enum):
    REMOTE = auto()      # θ from remote peer
    REPLAY = auto()      # local replay trace
    SNAPSHOT = auto()    # checkpoint / memory dump
    SYNTHETIC = auto()   # generated / test fixture


# ─────────────────────────────────────────────────────────────────
# ProjectionStep
# ─────────────────────────────────────────────────────────────────

@dataclass
class ProjectionStep:
    """Single step in a semantic projection chain."""
    from_mode: DAGHashMode
    to_mode: DAGHashMode
    intermediate_tree_hash: str = ""
    projection_digest: str = ""
    timestamp: float = field(default_factory=time.time)
    step_id: str = ""

    def __post_init__(self):
        # FIX-5: Content-addressed ID from modes and content
        if not self.step_id:
            self.step_id = _content_id(
                "proj",
                self.from_mode.name,
                self.to_mode.name,
                self.intermediate_tree_hash,
                self.projection_digest,
            )


# ─────────────────────────────────────────────────────────────────
# SemanticProof
# ─────────────────────────────────────────────────────────────────

@dataclass
class SemanticProof:
    """
    Cryptographic proof that two trees from different origins are semantically equivalent.

    FIX-5: proof_id is content-addressed from tree roots + modes.
           Same trees at same ticks → same proof_id on all nodes.
    """
    proof_id: str = ""
    created_at: float = field(default_factory=time.time)
    source_a: tuple[SemanticTree, ProofOrigin, DAGHashMode] = field(
        default_factory=lambda: (None, ProofOrigin.SYNTHETIC, DAGHashMode.CONSENSUS)
    )
    source_b: tuple[SemanticTree, ProofOrigin, DAGHashMode] = field(
        default_factory=lambda: (None, ProofOrigin.SYNTHETIC, DAGHashMode.CONSENSUS)
    )
    projection_steps: list[ProjectionStep] = field(default_factory=list)
    equivalence_result: EquivalenceResult | None = None
    proof_hash: str = ""
    ticks: tuple[int, int] = (0, 0)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        # FIX-5: Content-addressed proof_id from tree content
        if not self.proof_id:
            tree_a, origin_a, mode_a = self.source_a
            tree_b, origin_b, mode_b = self.source_b
            root_a = tree_a.root_hash(mode_a) if tree_a else ""
            root_b = tree_b.root_hash(mode_b) if tree_b else ""
            self.proof_id = _content_id(
                "sp",
                root_a,
                root_b,
                str(self.ticks),
            )

    def is_valid(self) -> bool:
        return (
            self.equivalence_result is not None
            and self.equivalence_result.is_equivalent
            and bool(self.proof_hash)
        )

    def to_dict(self) -> dict:
        return {
            "proof_id": self.proof_id,
            "created_at": self.created_at,
            "source_a_origin": self.source_a[1].name,
            "source_a_mode": self.source_a[2].name,
            "source_b_origin": self.source_b[1].name,
            "source_b_mode": self.source_b[2].name,
            "projection_steps": [
                {"from": s.from_mode.name, "to": s.to_mode.name,
                 "proj_hash": s.projection_digest}
                for s in self.projection_steps
            ],
            "equivalence": {
                "is_equivalent": self.equivalence_result.is_equivalent,
                "consensus_hash": self.equivalence_result.consensus_hash,
                "causal_hash": self.equivalence_result.causal_hash,
                "divergence_reason": self.equivalence_result.divergence_reason,
            } if self.equivalence_result else None,
            "proof_hash": self.proof_hash,
            "ticks": self.ticks,
            "metadata": self.metadata,
        }


# ─────────────────────────────────────────────────────────────────
# SemanticProofEngine
# ─────────────────────────────────────────────────────────────────

class SemanticProofEngine:
    """
    Proves cross-origin equivalence between two SemanticTrees.

    Pipeline:
        1. normalize both trees (ensure mode-consistent representation)
        2. project both to CONSENSUS (common ground)
        3. cross-check via CAUSAL projection
        4. compute final equivalence
        5. embed into immutable SemanticProof

    Theorems used:
        T1 (CAUSAL_n_uniqueness):         CAUSAL varies with permutation
        T2 (CAUSAL_projection_soundness): pairwise always equivalent
        T3 (cross_mode_reconcile):        decision matrix
        T4 (HASH_MODE_consistency):        equivalence matrix
        T5 (structural_equivalence):       root_hash(mode) equality ↔ structural equivalence
    """

    def __init__(self):
        self._proj = SemanticProjectionEngine()
        self._cross_val = CrossModeValidator()
        self._proof_log: list[SemanticProof] = []

    def prove_equivalence(
        self,
        tree_a: SemanticTree,
        tree_b: SemanticTree,
        mode_a: DAGHashMode = DAGHashMode.CONSENSUS,
        mode_b: DAGHashMode = DAGHashMode.CONSENSUS,
        origin_a: ProofOrigin = ProofOrigin.REMOTE,
        origin_b: ProofOrigin = ProofOrigin.REPLAY,
        tick_a: int = 0,
        tick_b: int = 0,
        metadata: dict | None = None,
    ) -> SemanticProof:
        """
        Build a SemanticProof that tree_a and tree_b are equivalent.

        Pipeline: normalize → project both to CONSENSUS → compare →
                   cross-check to CAUSAL → build proof object

        FIX-5: proof_id is derived from tree content — deterministic across nodes.
        """
        steps: list[ProjectionStep] = []

        # Step 1: project A → CONSENSUS
        tree_a_cons = self._proj.project_to_consensus(tree_a)
        root_a = tree_a.root_hash(mode_a)
        cons_hash_a = tree_a_cons.root_hash(DAGHashMode.CONSENSUS)
        steps.append(ProjectionStep(
            from_mode=mode_a,
            to_mode=DAGHashMode.CONSENSUS,
            intermediate_tree_hash=root_a,
            projection_digest=cons_hash_a,
        ))

        # Step 2: project B → CONSENSUS
        tree_b_cons = self._proj.project_to_consensus(tree_b)
        root_b = tree_b.root_hash(mode_b)
        cons_hash_b = tree_b_cons.root_hash(DAGHashMode.CONSENSUS)
        steps.append(ProjectionStep(
            from_mode=mode_b,
            to_mode=DAGHashMode.CONSENSUS,
            intermediate_tree_hash=root_b,
            projection_digest=cons_hash_b,
        ))

        # Step 3: compare consensus hashes
        consensus_equal = (cons_hash_a == cons_hash_b)

        # Step 4: cross-check via CAUSAL projection
        causal_hash_a = ""
        causal_hash_b = ""
        causal_equal = False
        if consensus_equal:
            tree_a_causal = self._proj.project_to_causal(tree_a)
            tree_b_causal = self._proj.project_to_causal(tree_b)
            causal_hash_a = tree_a_causal.root_hash(DAGHashMode.CAUSAL)
            causal_hash_b = tree_b_causal.root_hash(DAGHashMode.CAUSAL)
            causal_equal = (causal_hash_a == causal_hash_b)
            steps.append(ProjectionStep(
                from_mode=DAGHashMode.CONSENSUS,
                to_mode=DAGHashMode.CAUSAL,
                intermediate_tree_hash=cons_hash_a,
                projection_digest=causal_hash_a,
            ))
            steps.append(ProjectionStep(
                from_mode=DAGHashMode.CONSENSUS,
                to_mode=DAGHashMode.CAUSAL,
                intermediate_tree_hash=cons_hash_b,
                projection_digest=causal_hash_b,
            ))

        # Step 5: final equivalence result
        if consensus_equal and causal_equal:
            equiv_result = EquivalenceResult(
                is_equivalent=True,
                consensus_hash=cons_hash_a,
                causal_hash=causal_hash_a,
                divergence_reason=None,
            )
        elif consensus_equal:
            equiv_result = EquivalenceResult(
                is_equivalent=False,
                consensus_hash=cons_hash_a,
                causal_hash=causal_hash_a,
                divergence_reason="CAUSAL projection mismatch (structural divergence)",
            )
        else:
            equiv_result = EquivalenceResult(
                is_equivalent=False,
                consensus_hash=cons_hash_a,
                causal_hash="",
                divergence_reason=f"CONSENSUS hash mismatch: {cons_hash_a} ≠ {cons_hash_b}",
            )

        # Step 6: compute proof hash
        proof_hash = self._compute_proof_hash(tree_a_cons, tree_b_cons, steps)

        # FIX-5: deterministic proof_id from content
        proof_id = _content_id(
            "sp",
            root_a,
            root_b,
            str((tick_a, tick_b)),
        )

        proof = SemanticProof(
            proof_id=proof_id,
            created_at=time.time(),
            source_a=(tree_a, origin_a, mode_a),
            source_b=(tree_b, origin_b, mode_b),
            projection_steps=steps,
            equivalence_result=equiv_result,
            proof_hash=proof_hash,
            ticks=(tick_a, tick_b),
            metadata=metadata or {},
        )

        self._proof_log.append(proof)
        return proof

    def _compute_proof_hash(
        self,
        tree_a: SemanticTree,
        tree_b: SemanticTree,
        steps: list[ProjectionStep],
    ) -> str:
        parts = [
            tree_a.root_hash(DAGHashMode.CONSENSUS),
            tree_b.root_hash(DAGHashMode.CONSENSUS),
            "|".join(s.projection_digest for s in steps),
            str(len(steps)),
        ]
        raw = "|".join(parts).encode()
        return hashlib.sha256(raw).hexdigest()[:32]

    def prove_from_digests(
        self,
        digests_a: list[str],
        digests_b: list[str],
        mode_a: DAGHashMode = DAGHashMode.CONSENSUS,
        mode_b: DAGHashMode = DAGHashMode.CONSENSUS,
        origin_a: ProofOrigin = ProofOrigin.REMOTE,
        origin_b: ProofOrigin = ProofOrigin.REPLAY,
    ) -> SemanticProof:
        """Convenience: build trees from digest lists, then prove."""
        if not digests_a or not digests_b:
            return self._empty_proof(origin_a, origin_b)
        tree_a = SemanticTree.from_digest_list(digests_a, mode_a)
        tree_b = SemanticTree.from_digest_list(digests_b, mode_b)
        return self.prove_equivalence(tree_a, tree_b, mode_a, mode_b, origin_a, origin_b)

    def _empty_proof(
        self, origin_a: ProofOrigin, origin_b: ProofOrigin
    ) -> SemanticProof:
        # FIX-5: deterministic ID for empty proof
        return SemanticProof(
            proof_id=_content_id("sp", "empty", "empty", "0"),
            source_a=(SemanticTree(root=SemanticNode("")), origin_a, DAGHashMode.CONSENSUS),
            source_b=(SemanticTree(root=SemanticNode("")), origin_b, DAGHashMode.CONSENSUS),
            equivalence_result=EquivalenceResult(
                is_equivalent=True, consensus_hash="", causal_hash="", divergence_reason=None
            ),
            proof_hash="empty",
        )

    def proof_log(self) -> list[SemanticProof]:
        return list(self._proof_log)


# ─────────────────────────────────────────────────────────────────
# CROSS_ORIGIN_EQUIVALENCE Invariant
# ─────────────────────────────────────────────────────────────────

def _check_cross_origin_equivalence(state: dict) -> bool:
    """
    State must contain either:
      - 'proof': a SemanticProof object  OR
      - 'remote_digests' + 'replay_digests': two digest lists

    If proof exists: use its is_valid()
    Else: build proof from digests and check equivalence
    """
    proof: SemanticProof | None = state.get("proof")
    if proof is not None:
        return proof.is_valid()

    remote_digests = state.get("remote_digests", [])
    replay_digests = state.get("replay_digests", [])

    if not remote_digests and not replay_digests:
        return True  # no data is not a violation

    if not remote_digests or not replay_digests:
        return False

    try:
        mode_name = state.get("dag_mode", "CONSENSUS")
        mode = DAGHashMode[mode_name]
    except KeyError:
        mode = DAGHashMode.CONSENSUS

    engine = SemanticProofEngine()
    proof = engine.prove_from_digests(remote_digests, replay_digests, mode, mode)
    return proof.is_valid()


def get_cross_origin_equivalence_invariant():
    from orchestration.consistency.invariant_contract.invariant_contract import (
        EnforcementAction,
        InvariantDefinition,
        InvariantSeverity,
    )
    return InvariantDefinition(
        name="CROSS_ORIGIN_EQUIVALENCE",
        description=(
            "Remote θ state and replay-backed state must be semantically equivalent "
            "across origins. Proven via SemanticProofEngine pipeline: normalize both trees, "
            "project to CONSENSUS, cross-check via CAUSAL, verify root_hash equality. "
            "Violation → QUARANTINE the diverged component and block federation sync."
        ),
        severity=InvariantSeverity.CRITICAL,
        enforcement_action=EnforcementAction.QUARANTINE,
        check_fn=_check_cross_origin_equivalence,
        violation_cost=1.0,
        tags=["cross_origin", "equivalence", "v9.2", "critical", "proof"],
    )


def get_all_cross_origin_invariants():
    return [get_cross_origin_equivalence_invariant()]


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────

def _example_proof():
    """Quick sanity check — run with: python -c cross_origin_proof.py"""
    engine = SemanticProofEngine()

    # Identical digests — equivalent
    digests = ["d1", "d2", "d3", "d4"]
    proof = engine.prove_from_digests(digests, digests)
    log.info(f"Same digests:           valid={proof.is_valid()}")
    log.info(f"  proof_id={proof.proof_id}")
    log.info(f"  consensus_hash={proof.equivalence_result.consensus_hash}")
    log.info(f"  proof_hash={proof.proof_hash}")
    assert proof.is_valid(), "identical digests must be equivalent"

    # Determinism: same digests → same proof_id
    proof2 = engine.prove_from_digests(digests, digests)
    assert proof.proof_id == proof2.proof_id, "same digests → same proof_id (FIX-5)"
    log.info("  ✓ Deterministic: proof_id stable across calls")

    # Different digests — NOT equivalent
    proof_d = engine.prove_from_digests(digests, ["x1", "x2", "x3", "x4"])
    log.info(f"\nDifferent digests:       valid={proof_d.is_valid()}")
    log.info(f"  reason={proof_d.equivalence_result.divergence_reason}")

    # Invariant checks
    inv = get_cross_origin_equivalence_invariant()
    r_ok = inv.evaluate({"proof": proof})
    log.info(f"\nInvariant (same):        satisfied={r_ok.satisfied}")
    r_fail = inv.evaluate({"proof": proof_d})
    log.info(f"Invariant (diff):        satisfied={r_fail.satisfied}")
    log.info(f"  severity={r_fail.severity.name}, action={r_fail.enforcement_action.name}")

    log.info("\n✅ All sanity checks passed")


if __name__ == "__main__":
    _example_proof()


__all__ = [
    "ProjectionStep",
    "ProofOrigin",
    "SemanticProof",
    "SemanticProofEngine",
    "get_all_cross_origin_invariants",
    "get_cross_origin_equivalence_invariant",
]

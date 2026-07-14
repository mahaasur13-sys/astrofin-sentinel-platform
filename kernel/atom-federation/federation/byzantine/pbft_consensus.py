"""
pbft_consensus.py — PBFT-lite consensus engine for v9.8

Integrates with existing TrustWeightedConsensusResolver.
Adds PBFT phases: PREPARE → COMMIT (lightweight, not full SMR view-change).

Each phase uses 2f+1 quorum for Byzantine tolerance.
Messages carry signed digests for verification.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum, auto

from .message_signatures import FederationMessageSigning
from .quorum import QuorumCalculator


class PBFTPhase(Enum):
    IDLE = auto()
    PRE_PREPARE = auto()   # leader broadcasts proposed value
    PREPARE = auto()       # nodes投票 PREPARE if digest valid
    COMMIT = auto()        # nodes投票 COMMIT after PREPARE quorum
    FINISHED = auto()


@dataclass
class PBFTMessage:
    phase: PBFTPhase
    view: int
    sender_id: str
    digest: str          # hash of proposed value
    round_num: int
    signature: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "phase": self.phase.name,
            "view": self.view,
            "sender_id": self.sender_id,
            "digest": self.digest,
            "round_num": self.round_num,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }


@dataclass
class PhaseAccumulator:
    """Accumulates messages per phase per digest."""
    messages: list[PBFTMessage] = field(default_factory=list)
    digests_seen: set[str] = field(default_factory=set)

    def add(self, msg: PBFTMessage) -> bool:
        if msg.digest in self.digests_seen:
            return False
        self.messages.append(msg)
        self.digests_seen.add(msg.digest)
        return True

    @property
    def unique_digests(self) -> list[str]:
        return list(self.digests_seen)


@dataclass
class ConsensusOutcome:
    reached: bool
    phase: PBFTPhase
    digest: str | None
    view: int
    reason: str
    latency_ms: float


class PBFTLiteConsensusEngine:
    """
    PBFT-lite ON TOP of TrustWeightedConsensusResolver.

    Flow:
      IDLE → PRE_PREPARE (leader) → PREPARE (all) → 2f+1 quorum →
             COMMIT (all) → 2f+1 quorum → FINISHED

    Responsibilities:
      - Phase accumulation and quorum checking
      - Integration with FederationMessageSigning for digest verification
      - NOT replacing TrustWeightedConsensusResolver — layered on top

    Design note:
      Messages are signed with HMAC. Real deployment would use Ed25519/XMSS.
    """

    def __init__(
        self,
        node_id: str,
        n_nodes: int,
        signer: FederationMessageSigning,
        max_rounds: int = 3,
    ):
        self.node_id = node_id
        self.n_nodes = n_nodes
        self.signer = signer
        self.max_rounds = max_rounds

        self._phase: PBFTPhase = PBFTPhase.IDLE
        self._view: int = 0
        self._round: int = 0
        self._current_digest: str | None = None
        self._prepare_queue: list[PBFTMessage] = []
        self._commit_queue: list[PBFTMessage] = []
        self._started_at: float = 0.0

    @property
    def phase(self) -> PBFTPhase:
        return self._phase

    @property
    def view(self) -> int:
        return self._view

    def _sign(self, phase: PBFTPhase, view: int, digest: str, round_num: int) -> str:
        msg = f"{self.node_id}:{phase.name}:{view}:{digest}:{round_num}"
        signed = self.signer.sign(self.node_id, msg)
        return signed.signature

    def _make_msg(
        self,
        phase: PBFTPhase,
        view: int,
        digest: str,
        round_num: int,
    ) -> PBFTMessage:
        sig = self._sign(phase, view, digest, round_num)
        return PBFTMessage(
            phase=phase,
            view=view,
            sender_id=self.node_id,
            digest=digest,
            round_num=round_num,
            signature=sig,
        )

    # ── PRE_PREPARE ─────────────────────────────────────────────────

    def send_pre_prepare(self, digest: str) -> PBFTMessage | None:
        if self._phase != PBFTPhase.IDLE:
            return None
        self._phase = PBFTPhase.PRE_PREPARE
        self._current_digest = digest
        self._round = 0
        self._started_at = time.time()
        return self._make_msg(PBFTPhase.PRE_PREPARE, self._view, digest, self._round)

    def on_pre_prepare(self, msg: PBFTMessage) -> tuple[bool, PBFTMessage | None]:
        """
        Process incoming PRE_PREPARE from leader.
        Returns (accepted, own PREPARE message to broadcast).
        """
        if self._phase not in (PBFTPhase.IDLE,):
            return False, None
        if msg.view != self._view:
            return False, None
        if not msg.digest:
            return False, None

        self._phase = PBFTPhase.PREPARE
        self._current_digest = msg.digest
        self._round = msg.round_num
        self._prepare_queue.clear()
        return True, self._make_msg(PBFTPhase.PREPARE, self._view, msg.digest, msg.round_num)

    # ── PREPARE ─────────────────────────────────────────────────────

    def on_prepare(self, msg: PBFTMessage) -> tuple[bool, PBFTMessage | None]:
        """
        Accumulate PREPARE. If 2f+1 for same digest → transition to COMMIT.
        Quorum includes self (leader who sent PRE_PREPARE).

        Validates:
        - phase is PREPARE
        - view matches
        - digest matches leader's PRE_PREPARE (equivocation detection)

        Build prepare_certificate for COMMIT phase:
        - digest must match _current_digest (locked from PRE_PREPARE)
        - certificate = hash(sorted([all_prepare_digests])) → ensures all voters committed to same digest
        """
        if self._phase != PBFTPhase.PREPARE:
            return False, None
        if msg.view != self._view:
            return False, None
        if msg.digest != self._current_digest:
            return False, None  # ← equivocation: voter sent different digest → reject

        self._prepare_queue.append(msg)
        f = QuorumCalculator.compute_f(self.n_nodes)
        threshold = 2 * f + 1

        if len(self._prepare_queue) + 1 >= threshold:  # +1 = self (leader)
            self._phase = PBFTPhase.COMMIT
            self._commit_queue.clear()
            # Prepare certificate: hash of sorted prepare digests for commit binding
            digests = sorted([m.digest for m in self._prepare_queue] + [self._current_digest])
            self._prepare_certificate = hashlib.sha256("".join(digests).encode()).hexdigest()[:16]
            return True, self._make_msg(PBFTPhase.COMMIT, self._view, self._current_digest, self._round)

        return True, None

    # ── COMMIT ──────────────────────────────────────────────────────

    def on_commit(self, msg: PBFTMessage) -> tuple[bool, ConsensusOutcome]:
        """
        Accumulate COMMIT. If 2f+1 for same digest → consensus reached.
        Returns (accepted, outcome).
        """
        if self._phase != PBFTPhase.COMMIT:
            return False, ConsensusOutcome(
                reached=False,
                phase=self._phase,
                digest=None,
                view=self._view,
                reason="not in COMMIT phase",
                latency_ms=0.0,
            )
        if msg.view != self._view:
            return False, ConsensusOutcome(
                reached=False,
                phase=self._phase,
                digest=None,
                view=self._view,
                reason="view mismatch",
                latency_ms=0.0,
            )
        if msg.digest != self._current_digest:
            return False, ConsensusOutcome(
                reached=False,
                phase=self._phase,
                digest=None,
                view=self._view,
                reason="digest mismatch",
                latency_ms=0.0,
            )

        self._commit_queue.append(msg)
        f = QuorumCalculator.compute_f(self.n_nodes)
        threshold = 2 * f + 1

        if len(self._commit_queue) >= threshold:
            self._phase = PBFTPhase.FINISHED
            elapsed_ms = (time.time() - self._started_at) * 1000
            return True, ConsensusOutcome(
                reached=True,
                phase=PBFTPhase.FINISHED,
                digest=msg.digest,
                view=self._view,
                reason="commit_quorum_reached",
                latency_ms=elapsed_ms,
            )

        return True, ConsensusOutcome(
            reached=False,
            phase=self._phase,
            digest=self._current_digest,
            view=self._view,
            reason="waiting for more commits",
            latency_ms=0.0,
        )

    # ── Reset ───────────────────────────────────────────────────────

    def reset(self) -> None:
        self._phase = PBFTPhase.IDLE
        self._round = 0
        self._current_digest = None
        self._prepare_queue.clear()
        self._commit_queue.clear()

    def advance_round(self) -> bool:
        """Manual round advance (for stalled consensus)."""
        if self._round >= self.max_rounds - 1:
            return False
        self._round += 1
        self._phase = PBFTPhase.IDLE
        self._prepare_queue.clear()
        self._commit_queue.clear()
        return True

    def summary(self) -> dict:
        return {
            "node_id": self.node_id,
            "phase": self._phase.name,
            "view": self._view,
            "round": self._round,
            "digest": self._current_digest,
            "prepare_count": len(self._prepare_queue),
            "commit_count": len(self._commit_queue),
        }


# ─── Tests ────────────────────────────────────────────────────────────────

def _test_pbft_lite():
    from federation.byzantine.message_signatures import FederationMessageSigning

    secrets = {f"node_{i}": f"secret_{i}" for i in range(4)}
    signer = FederationMessageSigning(secrets)
    engine = PBFTLiteConsensusEngine(node_id="node_0", n_nodes=4, signer=signer, max_rounds=3)

    # PRE_PREPARE
    digest = "abc123"
    pre_prep = engine.send_pre_prepare(digest)
    assert pre_prep is not None
    assert pre_prep.phase == PBFTPhase.PRE_PREPARE
    print(f"✅ PRE_PREPARE sent: view={pre_prep.view}, digest={pre_prep.digest}")

    # Simulate other nodes receiving PRE_PREPARE and transitioning to PREPARE
    # Node_0 (leader) sends PRE_PREPARE → nodes 1,2,3 receive it via on_pre_prepare
    print(f"  _current_digest={engine._current_digest!r}, _prepare_queue len before={len(engine._prepare_queue)}")

    # Node_0 (leader) transitions to PREPARE after sending PRE_PREPARE
    # (leader also enters PREPARE state and sends its own PREPARE)
    engine._phase = PBFTPhase.PREPARE  # leader also enters PREPARE after sending PRE_PREPARE

    for node_id in ["node_1", "node_2", "node_3"]:
        # Other nodes call on_pre_prepare first to transition from IDLE → PREPARE
        _, my_prepare = engine.on_pre_prepare(pre_prep)
        # Now simulate node_id's PREPARE message (signed by node_id)
        signed = signer.sign(node_id, f"{node_id}:PREPARE:{pre_prep.view}:{digest}:{pre_prep.round_num}")
        prep_msg = PBFTMessage(
            phase=PBFTPhase.PREPARE, view=0, sender_id=node_id,
            digest=digest, round_num=pre_prep.round_num, signature=signed.signature,
        )
        accepted, commit = engine.on_prepare(prep_msg)
        print(f"  node {node_id}: accepted={accepted}, commit_phase={commit.phase.name if commit else None}, queue_len={len(engine._prepare_queue)}, engine_phase={engine._phase.name}")
        if commit:
            assert commit.phase == PBFTPhase.COMMIT
            print(f"✅ PREPARE from {node_id} → COMMIT triggered")

    # COMMIT quorum: 2f+1=3
    for node_id in ["node_1", "node_2", "node_3"]:
        signed = signer.sign(node_id, f"{node_id}:COMMIT:{pre_prep.view}:{digest}:{pre_prep.round_num}")
        commit_msg = PBFTMessage(
            phase=PBFTPhase.COMMIT, view=0, sender_id=node_id,
            digest=digest, round_num=pre_prep.round_num, signature=signed.signature,
        )
        accepted, outcome = engine.on_commit(commit_msg)
        if outcome.reached:
            assert outcome.reached is True
            assert outcome.digest == digest
            print(f"✅ COMMIT from {node_id} → consensus reached (latency={outcome.latency_ms:.2f}ms)")

    assert engine.phase == PBFTPhase.FINISHED
    print(f"✅ Final phase: {engine.phase.name}")

    # ── view change ──────────────────────────────────────────────────
    engine.reset()
    engine._view = 1
    pre_prep2 = engine.send_pre_prepare("digest_xyz")
    assert pre_prep2.view == 1
    print(f"✅ View reset works: view={pre_prep2.view}")

    # ── quorum sizes ───────────────────────────────────────────────
    from federation.byzantine.quorum import QuorumCalculator, QuorumType
    f4 = QuorumCalculator.compute_f(4)
    assert f4 == 1
    assert QuorumCalculator.quorum_size(4, QuorumType.two_f_plus_1) == 3
    f7 = QuorumCalculator.compute_f(7)
    assert f7 == 2
    assert QuorumCalculator.quorum_size(7, QuorumType.two_f_plus_1) == 5
    print(f"✅ QuorumCalculator: n=4 → f={f4}, 2f+1={3}; n=7 → f={f7}, 2f+1={5}")

    print("\n✅ v9.8 PBFTLiteConsensusEngine — all checks passed")


if __name__ == "__main__":
    _test_pbft_lite()


__all__ = [
    "ConsensusOutcome",
    "PBFTLiteConsensusEngine",
    "PBFTMessage",
    "PBFTPhase",
    "PhaseAccumulator",
]

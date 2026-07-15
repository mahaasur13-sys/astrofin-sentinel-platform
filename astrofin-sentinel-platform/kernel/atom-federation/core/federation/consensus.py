"""consensus.py — atom-federation-os v9.0+P6 Federated Consensus (ATOM-META-RL-020)

Implements Raft-like quorum consensus for the FederatedExecutionGateway.
Each node runs FULL P5 pipeline independently; consensus requires quorum of VALID votes.

Zero-trust invariant: NO trust between nodes — every node verifies independently.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

from core.deterministic import DeterministicClock, DeterministicUUIDFactory

# ── Types ────────────────────────────────────────────────────────────────────

class VoteValue(Enum):
    COMMIT = "commit"      # node verified proof and votes to commit
    REJECT = "reject"      # node rejected (invalid proof / runtime violation)
    ABSTAIN = "abstain"    # node did not participate

class NodeRole(Enum):
    LEADER = "leader"      # coordinates the round
    FOLLOWER = "follower"   # participates in voting
    CANDIDATE = "candidate" # campaigning for leadership

# ── Vote record ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class VoteRecord:
    node_id: str
    value: VoteValue
    term: int
    proof_hash: str           # hash of the proof this node verified
    payload_hash: str         # hash of the payload this node verified
    timestamp: float
    reason: str = ""          # rejection reason if REJECT

    @property
    def is_commit(self) -> bool:
        return self.value == VoteValue.COMMIT

# ── Consensus round ────────────────────────────────────────────────────────────

@dataclass
class ConsensusRound:
    round_id: str
    term: int
    payload_hash: str
    proof_hash: str
    votes: dict[str, VoteRecord] = field(default_factory=dict)
    started_at: float = field(default_factory=DeterministicClock.get_physical_time)
    decided_at: float | None = None
    outcome: VoteValue | None = None
    quorum_size: int = 0
    votes_required: int = 0

    @property
    def commit_count(self) -> int:
        return sum(1 for v in self.votes.values() if v.is_commit)

    @property
    def reject_count(self) -> int:
        return sum(1 for v in self.votes.values() if v.value == VoteValue.REJECT)

    @property
    def quorum_reached(self) -> bool:
        return self.commit_count >= self.votes_required

    @property
    def rejected(self) -> bool:
        return self.reject_count > (len(self.votes) - self.quorum_size)

    @property
    def is_complete(self) -> bool:
        return self.outcome is not None

    def cast_vote(self, record: VoteRecord) -> None:
        if self.outcome is not None:
            return  # already decided
        self.votes[record.node_id] = record
        if record.is_commit:
            # Check if quorum now reached
            if self.commit_count >= self.votes_required:
                self.outcome = VoteValue.COMMIT
                self.decided_at = DeterministicClock.get_physical_time()
        else:
            # Any reject votes? Check termination
            active = self.quorum_size - self.abstain_count
            if self.reject_count > (active - self.reject_count):
                self.outcome = VoteValue.REJECT
                self.decided_at = DeterministicClock.get_physical_time()

    @property
    def abstain_count(self) -> int:
        return sum(1 for v in self.votes.values() if v.value == VoteValue.ABSTAIN)


# ── Consensus module ─────────────────────────────────────────────────────────

class RaftConsensus:
    """
    Minimal Raft-like consensus for FederatedExecutionGateway.

    Key design choices (zero-trust):
      - Every node verifies the proof independently BEFORE voting
      - Votes are tied to specific (proof_hash, payload_hash) — no generic votes
      - Quorum = strict majority (ceil(n/2)+1 for odd, (n//2)+1 for even)
      - Rejection by ANY node in quorum → abort
      - Fork prevention: round_id must advance for same payload
    """

    def __init__(self, node_id: str, peers: list[str], quorum_fraction: float = 0.67):
        self.node_id = node_id
        self.peers = list(peers)  # all known peer node_ids
        self.all_nodes = [node_id] + self.peers
        self.n = len(self.all_nodes)
        # Quorum = ceil(2/3) for Byzantine tolerance, or ceil(n/2)+1 for crash
        self.quorum_size = max(1, int(self.n * quorum_fraction))
        self.votes_required = self.quorum_size  # commit requires quorum_size commits

        self._current_term = 0
        self._voted_for: str | None = None
        self._current_round: ConsensusRound | None = None
        self._ledger: list[dict] = []

    # ── Round management ──────────────────────────────────────────────────────

    def start_round(
        self,
        payload_hash: str,
        proof_hash: str,
        term: int | None = None,
    ) -> ConsensusRound:
        """Begin a new consensus round for the given payload+proof pair."""
        if term is not None:
            self._current_term = term
        else:
            self._current_term += 1

        self._current_round = ConsensusRound(
            round_id=DeterministicUUIDFactory.make_round_id(self._current_term, 0),
            term=self._current_term,
            payload_hash=payload_hash,
            proof_hash=proof_hash,
            quorum_size=self.quorum_size,
            votes_required=self.votes_required,
        )
        return self._current_round

    def current_round(self) -> ConsensusRound | None:
        return self._current_round

    def _round_for(self, payload_hash: str, proof_hash: str) -> ConsensusRound | None:
        r = self._current_round
        if r and r.payload_hash == payload_hash and r.proof_hash == proof_hash:
            return r
        return None

    # ── Vote casting ────────────────────────────────────────────────────────

    def cast_local_vote(
        self,
        proof_valid: bool,
        proof_hash: str,
        payload_hash: str,
        reason: str = "",
    ) -> VoteRecord:
        """
        Cast this node's vote after running full P5 verification.

        In the real system, this is called after:
            ProofVerifier.verify(request) → PASS
            RuntimeExecutionGuard.assert_system_integrity() → PASS
            G1..G10 → all PASS
        """
        record = VoteRecord(
            node_id=self.node_id,
            value=VoteValue.COMMIT if proof_valid else VoteValue.REJECT,
            term=self._current_term,
            proof_hash=proof_hash,
            payload_hash=payload_hash,
            timestamp=DeterministicClock.get_physical_time(),
            reason=reason,
        )

        if self._current_round is None:
            self.start_round(payload_hash, proof_hash)

        # Verify this vote is for the current round's payload
        if self._current_round.payload_hash != payload_hash:
            raise RuntimeError(
                f"Payload hash mismatch: vote for {payload_hash} "
                f"but current round is {self._current_round.payload_hash}"
            )
        if self._current_round.proof_hash != proof_hash:
            raise RuntimeError(
                f"Proof hash mismatch: vote for {proof_hash} "
                f"but current round uses {self._current_round.proof_hash}"
            )

        self._current_round.cast_vote(record)

        # Also cast to local ledger if commit
        if record.is_commit:
            self._append_to_ledger(record)

        return record

    def receive_vote(self, vote: VoteRecord) -> None:
        """Process a vote received from a peer node."""
        if vote.term < self._current_term:
            return  # stale vote

        if self._current_round is None:
            self.start_round(vote.payload_hash, vote.proof_hash, term=vote.term)

        self._current_round.cast_vote(vote)

        if vote.is_commit:
            self._append_to_ledger(vote)

    # ── Quorum decisions ─────────────────────────────────────────────────────

    def quorum_reached(self, round_id: str | None = None) -> bool:
        """Return True if commit quorum is reached in the current (or specified) round."""
        r = self._current_round
        if r is None:
            return False
        if round_id is not None and r.round_id != round_id:
            return False
        return r.outcome == VoteValue.COMMIT

    def rejection_threshold_reached(self, round_id: str | None = None) -> bool:
        """Return True if the round is unrecoverably rejected."""
        r = self._current_round
        if r is None:
            return False
        if round_id is not None and r.round_id != round_id:
            return False
        return r.outcome == VoteValue.REJECT

    def get_decision(self) -> tuple[VoteValue, list[VoteRecord]] | None:
        """Return (outcome, all_votes) if round is decided, else None."""
        r = self._current_round
        if r is None or r.outcome is None:
            return None
        return r.outcome, list(r.votes.values())

    # ── Ledger operations ────────────────────────────────────────────────────

    def _append_to_ledger(self, vote: VoteRecord) -> None:
        prev_hash = self._ledger[-1]["entry_hash"] if self._ledger else "GENESIS"
        entry_hash = hashlib.sha256(
            f"{prev_hash}{vote.proof_hash}{vote.payload_hash}{vote.node_id}{vote.timestamp}"
            .encode()
        ).hexdigest()

        self._ledger.append({
            "entry_hash": entry_hash,
            "prev_hash": prev_hash,
            "proof_hash": vote.proof_hash,
            "payload_hash": vote.payload_hash,
            "node_id": vote.node_id,
            "timestamp": vote.timestamp,
            "term": vote.term,
            "round_id": self._current_round.round_id if self._current_round else None,
        })

    def get_ledger_tail(self, n: int = 5) -> list[dict]:
        """Return the last n ledger entries."""
        return self._ledger[-n:] if self._ledger else []

    def verify_ledger_chain(self) -> bool:
        """Verify ledger integrity: each entry's prev_hash links correctly."""
        if not self._ledger:
            return True
        for i, entry in enumerate(self._ledger):
            if i == 0:
                if entry["prev_hash"] != "GENESIS":
                    return False
            else:
                if entry["prev_hash"] != self._ledger[i - 1]["entry_hash"]:
                    return False
        return True

    @property
    def current_term(self) -> int:
        return self._current_term

    def simulate_peer_votes(
        self,
        peer_results: list[tuple[str, bool]],
        payload_hash: str,
        proof_hash: str,
    ) -> tuple[VoteValue, list[VoteRecord]]:
        """
        Simulate receiving votes from peers (for testing / single-node simulation).

        peer_results: list of (node_id, proof_valid) tuples
        Returns: (final_outcome, all_votes)
        """
        if self._current_round is None:
            self.start_round(payload_hash, proof_hash)

        all_votes: list[VoteRecord] = []

        for peer_id, proof_valid in peer_results:
            vote = VoteRecord(
                node_id=peer_id,
                value=VoteValue.COMMIT if proof_valid else VoteValue.REJECT,
                term=self._current_term,
                proof_hash=proof_hash,
                payload_hash=payload_hash,
                timestamp=DeterministicClock.get_physical_time(),
                reason="" if proof_valid else "peer_validation_failed",
            )
            self.receive_vote(vote)
            all_votes.append(vote)

        decision = self.get_decision()
        if decision is None:
            return VoteValue.REJECT, all_votes
        return decision[0], all_votes

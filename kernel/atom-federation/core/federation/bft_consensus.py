"""bft_consensus.py — atom-federation-os v9.0+P7 Byzantine-Fault-Tolerant Consensus.

Implements PBFT-like three-phase consensus tolerating f Byzantine nodes.

Assumptions:
  - n >= 3f + 1 total nodes
  - At most f nodes are Byzantine (can lie, equivocate, drop messages)
  - Honest nodes follow the protocol correctly
  - Network may delay/reorder but will not corrupt messages in transit

Protocol phases:
  1. PRE-PREPARE  — primary orders the request, assigns view+sequence
  2. PREPARE      — nodes validate and broadcast their prepare votes
  3. COMMIT       — after 2f+1 prepares, nodes broadcast commit votes
  4. DECIDED      — after 2f+1 commits, request is safely committed

Strong quorum requirement:
  PREPARE quorum: 2f + 1 (ensures at least f+1 honest agree on ordering)
  COMMIT  quorum: 2f + 1 (ensures at least f+1 honest will never revert)

Invariant maintained:
  |honest| >= 2f + 1 iff  n >= 3f + 1  and  |faulty| <= f
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

# ── Enums ─────────────────────────────────────────────────────────────────────

class Phase(Enum):
    INITIAL       = auto()
    PRE_PREPARED  = auto()
    PREPARED      = auto()
    COMMITTED     = auto()
    DECIDED       = auto()


class VoteValue(Enum):
    COMMIT  = auto()   # vote to commit this request
    ABORT   = auto()   # vote to reject (e.g. invalid proof)
    SUSPECT = auto()    # node suspects Byzantine behaviour


# ── BFT Thresholds ───────────────────────────────────────────────────────────

def bft_thresholds(n: int) -> tuple[int, int, int]:
    """
    Compute Byzantine-resilient quorum sizes for given n.

    Returns (f, prepare_quorum, commit_quorum):
      f             = floor((n-1) / 3)
      prepare_quorum = 2f + 1  (PREPARE phase threshold)
      commit_quorum  = 2f + 1  (COMMIT phase threshold)
    """
    f = (n - 1) // 3
    quorum = 2 * f + 1
    return f, quorum, quorum


# ── Message Records ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BFTVote:
    node_id: str
    phase: Phase          # which phase this vote is for
    request_hash: str
    view: int
    sequence: int
    vote: VoteValue
    signature: str        # placeholder — in production use ed25519/ BLS
    timestamp: float


@dataclass(frozen=True)
class PreparedCertificate:
    """Proof that ≥ 2f+1 nodes have prepared the request."""
    request_hash: str
    view: int
    sequence: int
    prepare_votes: tuple[BFTVote, ...]
    quorum_size: int
    threshold: int        # must be >= threshold for valid

    @property
    def is_valid(self) -> bool:
        return (
            len(self.prepare_votes) >= self.threshold
            and all(v.phase == Phase.PREPARED for v in self.prepare_votes)
        )


@dataclass(frozen=True)
class CommitCertificate:
    """Proof that the request is irreversibly committed."""
    request_hash: str
    view: int
    sequence: int
    commit_votes: tuple[BFTVote, ...]
    quorum_size: int
    threshold: int

    @property
    def is_valid(self) -> bool:
        return (
            len(self.commit_votes) >= self.threshold
            and all(v.phase == Phase.COMMITTED for v in self.commit_votes)
        )


# ── BFTConsensus ───────────────────────────────────────────────────────────────

class BFTConsensus:
    """
    PBFT-like consensus engine tolerating f Byzantine nodes.

    Thread-safety note:
      All state mutations happen inside phase-transition methods.
      External callers MUST hold the lock (self._lock) during any read-modify-write.

    Usage:
        bft = BFTConsensus(node_id='a', all_nodes=['a','b','c','d'], f=1)
        bft.init_view(view=1, primary='a')

        # On receiving a request from the primary:
        bft.receive_request(request_hash='abc', proof='...', payload_hash='xyz')

        # On receiving PRE-PREPARE from primary:
        bft.receive_pre_prepare(request_hash='abc', view=1, sequence=1, primary_sig='...')

        # Each node receives and forwards PREPARE messages from others:
        bft.receive_prepare(vote)

        # After receiving ≥ 2f+1 PREPARE votes:
        bft.check_prepared(request_hash)

        # Each node receives and forwards COMMIT messages:
        bft.receive_commit(vote)

        # After receiving ≥ 2f+1 COMMIT votes:
        can_commit = bft.check_committable(request_hash)
        if can_commit:
            bft.finalize_commit(request_hash)
    """

    def __init__(
        self,
        node_id: str,
        all_nodes: list[str],
        f: int | None = None,
    ):
        self.node_id = node_id
        self.n = len(all_nodes)
        self._f = f if f is not None else (self.n - 1) // 3
        self._prepare_quorum = 2 * self._f + 1
        self._commit_quorum = 2 * self._f + 1
        self._all_nodes = all_nodes

        # Dynamic state
        self._current_view: int = 0
        self._primary: str = all_nodes[0] if all_nodes else ""
        self._sequence: int = 0

        # Request tracking: request_hash -> RequestState
        self._requests: dict[str, RequestState] = {}

        # Double-sign detection: (node_id, sequence) -> set of conflicting request_hashes
        self._double_sign_history: dict[tuple[str, int], set[str]] = {}

        # Slashed nodes: node_id -> True
        self._slashed: set[str] = set()

        # Locks for thread-safe mutations
        import threading
        self._lock = threading.Lock()

    # ── View Management ───────────────────────────────────────────────────

    def init_view(self, view: int, primary: str) -> None:
        with self._lock:
            self._current_view = view
            self._primary = primary
            self._sequence = 0

    @property
    def is_primary(self) -> bool:
        return self.node_id == self._primary

    @property
    def f(self) -> int:
        return self._f

    @property
    def honest_count(self) -> int:
        """Number of nodes we assume are honest (n - f)."""
        return self.n - self._f

    # ── Request Lifecycle ─────────────────────────────────────────────────

    def receive_request(
        self,
        request_hash: str,
        proof: str,
        payload_hash: str,
    ) -> None:
        """
        Called when this node receives a new execution request.
        If we are the primary, we initiate PRE-PREPARE; otherwise forward to primary.
        """
        with self._lock:
            if request_hash in self._requests:
                return  # already being processed

            self._requests[request_hash] = RequestState(
                request_hash=request_hash,
                proof=proof,
                payload_hash=payload_hash,
                view=self._current_view,
                phase=Phase.INITIAL,
                prepare_votes=[],
                commit_votes=[],
                pre_prepare_broadcast=False,
                prepared_certificate=None,
                commit_certificate=None,
            )

            if self.is_primary:
                self._issue_pre_prepare(request_hash)

    def _issue_pre_prepare(self, request_hash: str) -> None:
        """Primary issues PRE-PREPARE for a validated request."""
        rs = self._requests[request_hash]
        self._sequence += 1
        seq = self._sequence

        vote = BFTVote(
            node_id=self.node_id,
            phase=Phase.PRE_PREPARED,
            request_hash=request_hash,
            view=self._current_view,
            sequence=seq,
            vote=VoteValue.COMMIT,
            signature=self._sign(request_hash, seq),
            timestamp=time.time(),
        )

        rs.pre_prepare_vote = vote
        rs.phase = Phase.PRE_PREPARED

        # In production: broadcast PRE-PREPARE to all other nodes
        # Here we record it as a self-receive (simulating the broadcast)
        self._receive_pre_prepare(vote)

    def _receive_pre_prepare(self, vote: BFTVote) -> None:
        """Process a PRE-PREPARE vote (from primary or propagation)."""
        with self._lock:
            rs = self._requests.get(vote.request_hash)
            if rs is None:
                # We haven't seen the request — buffer the PRE-PREPARE
                return  # in production: add to waiting queue

            # Only PREPARE if we haven't already
            if rs.phase.value >= Phase.PREPARED.value:
                return

            # Check: node not slashed, view matches, sequence valid
            if vote.node_id in self._slashed:
                return
            if vote.view != self._current_view:
                return
            if vote.sequence < 0:
                return

            rs.phase = Phase.PRE_PREPARED

    def receive_prepare(self, vote: BFTVote) -> None:
        """
        Receive a PREPARE vote from another node.
        Accumulate until we reach prepare_quorum.
        """
        with self._lock:
            if vote.node_id in self._slashed:
                return  # slashed nodes ignored

            rs = self._requests.get(vote.request_hash)
            if rs is None:
                return

            if vote.view != self._current_view:
                return

            # Detect double-sign: same node+sequence but different request
            key = (vote.node_id, vote.sequence)
            if key in self._double_sign_history:
                conflicting = self._double_sign_history[key]
                if vote.request_hash not in conflicting:
                    # Node signed TWO different requests at the same sequence → Byzantine
                    conflicting.add(vote.request_hash)
                    # Keep the NEWER violation detected in receive_prepare
                    # already recorded — slashing handled externally
            else:
                self._double_sign_history[key] = {vote.request_hash}

            # Record the vote if not duplicate
            if not any(v.node_id == vote.node_id and v.phase == Phase.PREPARED
                       for v in rs.prepare_votes):
                rs.prepare_votes.append(vote)

            if len(rs.prepare_votes) >= self._prepare_quorum and rs.phase != Phase.PREPARED:
                rs.phase = Phase.PREPARED
                # Broadcast our own COMMIT intent (in production: send COMMIT message)
                self._broadcast_commit_intent(rs)

    def _broadcast_commit_intent(self, rs: RequestState) -> None:
        """When we reach PREPARED, broadcast COMMIT vote."""
        vote = BFTVote(
            node_id=self.node_id,
            phase=Phase.COMMITTED,
            request_hash=rs.request_hash,
            view=self._current_view,
            sequence=rs.pre_prepare_vote.sequence if rs.pre_prepare_vote else 0,
            vote=VoteValue.COMMIT,
            signature=self._sign(rs.request_hash, rs.sequence),
            timestamp=time.time(),
        )
        rs.commit_votes.append(vote)
        # In production: broadcast COMMIT message to all nodes

    def receive_commit(self, vote: BFTVote) -> None:
        """Receive a COMMIT vote from another node."""
        with self._lock:
            if vote.node_id in self._slashed:
                return

            rs = self._requests.get(vote.request_hash)
            if rs is None:
                return

            if vote.view != self._current_view:
                return

            # Detect double-sign at commit phase
            key = (vote.node_id, vote.sequence)
            if key in self._double_sign_history:
                conflicting = self._double_sign_history[key]
                if vote.request_hash not in conflicting:
                    conflicting.add(vote.request_hash)
            else:
                self._double_sign_history[key] = {vote.request_hash}

            if not any(v.node_id == vote.node_id and v.phase == Phase.COMMITTED
                       for v in rs.commit_votes):
                rs.commit_votes.append(vote)

            if (len(rs.commit_votes) >= self._commit_quorum
                    and rs.phase != Phase.COMMITTED):
                rs.phase = Phase.COMMITTED

    def check_prepared(self, request_hash: str) -> PreparedCertificate | None:
        """
        Return PreparedCertificate if quorum reached, else None.
        """
        with self._lock:
            rs = self._requests.get(request_hash)
            if rs is None or rs.phase != Phase.PREPARED:
                return None

            if rs.prepared_certificate is None:
                rs.prepared_certificate = PreparedCertificate(
                    request_hash=request_hash,
                    view=self._current_view,
                    sequence=rs.sequence,
                    prepare_votes=tuple(rs.prepare_votes),
                    quorum_size=self.n,
                    threshold=self._prepare_quorum,
                )
            return rs.prepared_certificate

    def check_committable(self, request_hash: str) -> bool:
        """
        Returns True if we have received ≥ 2f+1 COMMIT votes.
        """
        with self._lock:
            rs = self._requests.get(request_hash)
            if rs is None:
                return False
            return (
                rs.phase == Phase.COMMITTED
                and len(rs.commit_votes) >= self._commit_quorum
            )

    def finalize_commit(self, request_hash: str) -> CommitCertificate | None:
        """
        Finalize the commit. Returns CommitCertificate for the distributed ledger.
        """
        with self._lock:
            rs = self._requests.get(request_hash)
            if rs is None or rs.phase != Phase.COMMITTED:
                return None

            if rs.commit_certificate is None:
                seq = rs.pre_prepare_vote.sequence if rs.pre_prepare_vote else rs.sequence
                rs.commit_certificate = CommitCertificate(
                    request_hash=request_hash,
                    view=self._current_view,
                    sequence=seq,
                    commit_votes=tuple(rs.commit_votes),
                    quorum_size=self.n,
                    threshold=self._commit_quorum,
                )

            rs.phase = Phase.DECIDED
            return rs.commit_certificate

    # ── Double-Sign Detection ─────────────────────────────────────────────

    def detect_double_sign(self, node_id: str, sequence: int) -> list[str]:
        """
        Return list of conflicting request hashes for given node+sequence.
        If len > 1 → Byzantine behaviour confirmed.
        """
        with self._lock:
            key = (node_id, sequence)
            return list(self._double_sign_history.get(key, set()))

    # ── Slashing ──────────────────────────────────────────────────────────

    def slash(self, node_id: str) -> None:
        """Mark a node as slashed (excluded from future quorums)."""
        with self._lock:
            self._slashed.add(node_id)

    @property
    def is_slashed(self) -> bool:
        return self.node_id in self._slashed

    # ── Query ─────────────────────────────────────────────────────────────

    def get_status(self, request_hash: str) -> dict[str, Any]:
        with self._lock:
            rs = self._requests.get(request_hash)
            if rs is None:
                return {"known": False}
            return {
                "known": True,
                "phase": rs.phase.name,
                "prepare_votes": len(rs.prepare_votes),
                "commit_votes": len(rs.commit_votes),
                "prepare_quorum": self._prepare_quorum,
                "commit_quorum": self._commit_quorum,
                "quorum_reached": (
                    len(rs.prepare_votes) >= self._prepare_quorum
                    if rs.phase == Phase.PREPARED
                    else len(rs.commit_votes) >= self._commit_quorum
                ),
            }

    # ── Helpers ──────────────────────────────────────────────────────────

    def _sign(self, *data: Any) -> str:
        """Placeholder signature — in production use ed25519/BLS."""
        blob = "".join(str(x) for x in data).encode()
        return hashlib.sha256(blob).hexdigest()[:16]

    def can_satisfy_quorum(self, n_total: int, n_faulty: int) -> bool:
        """
        Check if honest nodes can reach quorum despite faulty nodes.

        Requirement: honest >= 2f + 1
        where honest = n_total - n_faulty
        """
        honest = n_total - n_faulty
        return honest >= (2 * self._f + 1)


@dataclass
class RequestState:
    request_hash: str
    proof: str
    payload_hash: str
    view: int
    phase: Phase = Phase.INITIAL
    sequence: int = 0
    pre_prepare_vote: BFTVote | None = None
    prepare_votes: list[BFTVote] = field(default_factory=list)
    commit_votes: list[BFTVote] = field(default_factory=list)
    pre_prepare_broadcast: bool = False
    prepared_certificate: PreparedCertificate | None = None
    commit_certificate: CommitCertificate | None = None

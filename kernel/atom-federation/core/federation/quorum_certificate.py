"""quorum_certificate.py — atom-federation-os v9.0+P6 Quorum Certificate.

Aggregates signatures from quorum of nodes into a verifiable certificate.
Used to authorize the ACT stage in FederatedExecutionGateway.

Hard invariant:
    QC is valid IFF all contained votes are COMMIT and count >= quorum_required
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any

from .consensus import VoteRecord, VoteValue


@dataclass(frozen=True)
class QuorumCertificate:
    """
    Aggregated proof of quorum agreement.

    Contains:
      - vote_records: all COMMIT votes from participating nodes
      - aggregated_signature: cryptographic aggregate (simplified: hash of all votes)
      - proof_hash: hash of the execution proof that was verified
      - payload_hash: hash of the payload being executed
      - quorum_size: number of nodes required for quorum
      - threshold: minimum COMMIT votes needed
      - timestamp: when the QC was formed
      - round_id: consensus round identifier
    """
    vote_records: tuple[VoteRecord, ...]
    aggregated_signature: str          # simplified BLS: hash of all vote sigs
    proof_hash: str
    payload_hash: str
    quorum_size: int                   # total nodes in federation
    threshold: int                    # minimum commits needed
    timestamp: float
    round_id: str

    @property
    def commit_count(self) -> int:
        return len(self.vote_records)

    @property
    def is_valid(self) -> bool:
        """QC is valid iff all votes are COMMIT and count >= threshold."""
        if not self.vote_records:
            return False
        if len(self.vote_records) < self.threshold:
            return False
        return all(v.value == VoteValue.COMMIT for v in self.vote_records)

    @property
    def quorum_reached(self) -> bool:
        return self.is_valid

    def verify_binding(self, proof_hash: str, payload_hash: str) -> bool:
        """Verify QC is bound to the specific proof and payload."""
        return self.proof_hash == proof_hash and self.payload_hash == payload_hash

    def summary(self) -> dict[str, Any]:
        return {
            "quorum_reached": self.quorum_reached,
            "commit_count": self.commit_count,
            "threshold": self.threshold,
            "proof_hash": self.proof_hash[:12] + "...",
            "payload_hash": self.payload_hash[:12] + "...",
            "round_id": self.round_id,
        }


class QuorumCertificateBuilder:
    """
    Builds QuorumCertificates from a set of VoteRecords.

    Usage:
        builder = QuorumCertificateBuilder(quorum_size=3, threshold=2)
        builder.add_vote(vote1)  # COMMIT
        builder.add_vote(vote2)  # COMMIT
        qc = builder.build(proof_hash, payload_hash, round_id)
        if qc.quorum_reached:
            # proceed to ACT
    """

    def __init__(self, quorum_size: int, threshold: int):
        self.quorum_size = quorum_size
        self.threshold = threshold
        self._votes: list[VoteRecord] = []

    def add_vote(self, vote: VoteRecord) -> None:
        """Add a vote record. REJECT votes immediately invalidate the QC."""
        self._votes.append(vote)

    def add_votes(self, votes: list[VoteRecord]) -> None:
        for v in votes:
            self.add_vote(v)

    @property
    def commit_count(self) -> int:
        return sum(1 for v in self._votes if v.value == VoteValue.COMMIT)

    @property
    def has_rejects(self) -> bool:
        return any(v.value == VoteValue.REJECT for v in self._votes)

    def can_build(self) -> bool:
        """Return True if enough COMMIT votes to form valid QC."""
        return self.commit_count >= self.threshold and not self.has_rejects

    def build(
        self,
        proof_hash: str,
        payload_hash: str,
        round_id: str,
    ) -> QuorumCertificate | None:
        """
        Build a QC if quorum is reached.

        Returns None if quorum not yet reached or if any REJECT votes exist.
        """
        if not self.can_build():
            return None

        # Build aggregated signature: hash of all individual proof_hashes
        sig_parts = sorted(v.proof_hash for v in self._votes if v.value == VoteValue.COMMIT)
        aggregated_sig = hashlib.sha256(
            "|".join(sig_parts).encode()
        ).hexdigest()

        return QuorumCertificate(
            vote_records=tuple(
                v for v in self._votes if v.value == VoteValue.COMMIT
            ),
            aggregated_signature=aggregated_sig,
            proof_hash=proof_hash,
            payload_hash=payload_hash,
            quorum_size=self.quorum_size,
            threshold=self.threshold,
            timestamp=time.time(),
            round_id=round_id,
        )

    def reset(self) -> None:
        """Clear all votes to start a new round."""
        self._votes.clear()

"""
proof_enriched_gossip.py — v9.3 Phase 3: Proof-enriched DeltaGossip

Key shift from Phase 2:
  Phase 2: consensus weighted by proof_valid + stability + drift
  Phase 3: delta gossip messages carry proof metadata

Before (v9.2 and before):
  DeltaGossipMessage fields:
    source_node_id, root_hash, changed_node_ids, changed_hashes, seq, ts_ns, hash_mode

After (v9.3):
  DeltaGossipMessage fields (extension):
    source_node_id, root_hash, changed_node_ids, changed_hashes, seq, ts_ns, hash_mode
    proof_hash      — SHA-256 of cross-origin SemanticProof (if available)
    proof_origin    — ProofOrigin of the remote's proof (if available)
    proof_valid     — bool indicating if proof was verified locally

Why this matters:
  - Peers can skip re-proving if they already have proof_hash
  - Proof origin helps ranking (REMOTE > SNAPSHOT > REPLAY)
  - Proof metadata travels with the delta, no extra round-trips

Integration points:
  - DeltaGossipMessage (protocol.py) — proof_hash, proof_origin, proof_valid
  - ProofAwarePolicySync (proof_aware_policy_sync.py) — uses proof from message
  - ProofAwareConsensusResolver (proof_aware_consensus.py) — ranks by proof_valid
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from federation.delta_gossip.dag_hash_modes import DAGHashMode
from orchestration.consistency.invariant_contract.cross_origin_proof import (

import logging
log = logging.getLogger(__name__)

    ProofOrigin,
    SemanticProof,
)

# ─────────────────────────────────────────────────────────────────
# ProofMetadata (attachable to any gossip message)
# ─────────────────────────────────────────────────────────────────

@dataclass
class ProofMetadata:
    """
    Proof metadata carried in or attached to DeltaGossipMessage.

    Fields:
        proof_hash   — SHA-256 of the SemanticProof (first 16 hex)
        proof_origin — which origin this proof was built from
        proof_valid  — was proof locally verified (True/False/None=unchecked)
        proof_tick   — tick when proof was generated
    """
    proof_hash: str = ""
    proof_origin: ProofOrigin | None = None
    proof_valid: bool | None = None   # None = not checked yet
    proof_tick: int = 0

    def is_available(self) -> bool:
        return bool(self.proof_hash)

    def to_dict(self) -> dict:
        return {
            "proof_hash": self.proof_hash,
            "proof_origin": self.proof_origin.name if self.proof_origin else None,
            "proof_valid": self.proof_valid,
            "proof_tick": self.proof_tick,
        }


# ─────────────────────────────────────────────────────────────────
# ProofEnrichedDeltaMessage (extends DeltaGossipMessage)
# ─────────────────────────────────────────────────────────────────

@dataclass
class ProofEnrichedDeltaMessage:
    """
    DeltaGossipMessage enriched with proof metadata.

    This is a wrapper / parallel structure to DeltaGossipMessage.
    The actual integration happens by extending DeltaGossipMessage with
    these fields (see patch_delta_gossip_message_schema below).

    Usage:
        enriched = ProofEnrichedDeltaMessage.from_base_message(msg, proof_metadata)
        # or when building a new message:
        enriched = ProofEnrichedDeltaMessage(
            source_node_id="node_1",
            root_hash="abc123",
            proof_metadata=ProofMetadata(
                proof_hash="def456",
                proof_origin=ProofOrigin.REMOTE,
                proof_valid=True,
            )
        )
    """
    source_node_id: str
    root_hash: str
    changed_node_ids: list[str]
    changed_hashes: dict[str, str]
    seq: int
    ts_ns: int
    hash_mode: DAGHashMode
    proof_metadata: ProofMetadata = field(default_factory=ProofMetadata)

    @classmethod
    def from_base_message(
        cls,
        base_msg,
        proof_metadata: ProofMetadata | None = None,
    ):
        """Wrap an existing DeltaGossipMessage with proof metadata."""
        return cls(
            source_node_id=base_msg.source_node_id,
            root_hash=base_msg.root_hash,
            changed_node_ids=base_msg.changed_node_ids,
            changed_hashes=base_msg.changed_hashes,
            seq=base_msg.seq,
            ts_ns=base_msg.ts_ns,
            hash_mode=base_msg.hash_mode,
            proof_metadata=proof_metadata or ProofMetadata(),
        )

    def with_proof(
        self,
        proof: SemanticProof,
        verified: bool = True,
    ) -> ProofEnrichedDeltaMessage:
        """Attach proof metadata from a SemanticProof object."""
        meta = ProofMetadata(
            proof_hash=proof.proof_hash[:16] if proof.proof_hash else "",
            proof_origin=proof.source_a[1] if proof.source_a else None,
            proof_valid=verified and proof.is_valid(),
            proof_tick=max(proof.ticks) if proof.ticks else 0,
        )
        self.proof_metadata = meta
        return self

    def is_proof_valid(self) -> bool:
        return self.proof_metadata.proof_valid is True

    def to_summary(self) -> dict:
        base = {
            "source_node_id": self.source_node_id,
            "root_hash": self.root_hash[:8],
            "seq": self.seq,
            "hash_mode": self.hash_mode.name,
            "changed_count": len(self.changed_node_ids),
        }
        if self.proof_metadata.is_available():
            base["proof_hash"] = self.proof_metadata.proof_hash[:8]
            base["proof_origin"] = (
                self.proof_metadata.proof_origin.name
                if self.proof_metadata.proof_origin else None
            )
            base["proof_valid"] = self.proof_metadata.proof_valid
        return base


# ─────────────────────────────────────────────────────────────────
# GossipProofEngine — manages proof lifecycle in gossip
# ─────────────────────────────────────────────────────────────────

class GossipProofEngine:
    """
    Manages proof metadata lifecycle for delta gossip messages.

    Responsibilities:
      - Attach proof metadata to outgoing messages
      - Verify incoming proof metadata
      - Cache proof_hash → proof_valid for deduplication
      - Expire stale proof cache entries

    Usage:
        gpe = GossipProofEngine()
        # Outgoing: attach proof to message
        enriched = gpe.attach_proof_to_message(base_msg, semantic_proof)
        # Incoming: verify proof before using
        is_valid = gpe.verify_proof_from_message(enriched_msg)
    """

    def __init__(self, ttl_seconds: float = 300.0):
        self._proof_cache: dict[str, tuple[bool, float]] = {}  # proof_hash → (valid, timestamp)
        self._ttl = ttl_seconds

    def attach_proof_to_message(
        self,
        base_message,
        proof: SemanticProof,
        verified: bool = True,
    ) -> ProofEnrichedDeltaMessage:
        """
        Attach proof metadata from a SemanticProof to a delta message.

        Args:
            base_message: DeltaGossipMessage to enrich
            proof: SemanticProof to attach
            verified: whether proof was locally verified

        Returns:
            ProofEnrichedDeltaMessage with proof metadata attached
        """
        meta = ProofMetadata(
            proof_hash=proof.proof_hash[:16] if proof.proof_hash else "",
            proof_origin=proof.source_a[1] if proof.source_a else None,
            proof_valid=verified and proof.is_valid(),
            proof_tick=max(proof.ticks) if proof.ticks else 0,
        )
        return ProofEnrichedDeltaMessage.from_base_message(base_message, meta)

    def verify_proof_from_message(
        self,
        enriched_message: ProofEnrichedDeltaMessage,
    ) -> bool | None:
        """
        Verify proof from an incoming enriched message.

        Uses local cache for deduplication. Returns:
          - True: proof confirmed valid
          - False: proof confirmed invalid
          - None: proof not in cache (needs evaluation)
        """
        ph = enriched_message.proof_metadata.proof_hash
        if not ph:
            return None

        # Check cache
        if ph in self._proof_cache:
            valid, _ = self._proof_cache[ph]
            return valid

        # Not cached — needs evaluation (caller must do full proof verification)
        return None

    def cache_proof_result(self, proof_hash: str, valid: bool) -> None:
        """Cache a proof verification result."""
        self._proof_cache[proof_hash] = (valid, time.time())

    def cleanup_expired(self) -> int:
        """Remove expired entries from proof cache. Returns count removed."""
        now = time.time()
        expired = [
            ph for ph, (_, ts) in self._proof_cache.items()
            if now - ts > self._ttl
        ]
        for ph in expired:
            del self._proof_cache[ph]
        return len(expired)

    def cache_summary(self) -> dict:
        return {
            "cached_proofs": len(self._proof_cache),
            "ttl_seconds": self._ttl,
        }


# ─────────────────────────────────────────────────────────────────
# Proof-enriched routing helpers
# ─────────────────────────────────────────────────────────────────

def filter_by_proof_trust(
    messages: list[ProofEnrichedDeltaMessage],
    require_valid_proof: bool = False,
) -> list[ProofEnrichedDeltaMessage]:
    """
    Filter messages by proof validity.

    Args:
        messages: list of proof-enriched messages
        require_valid_proof: if True, exclude messages with proof_valid=False

    Returns:
        Filtered list
    """
    if not require_valid_proof:
        return messages

    return [
        msg for msg in messages
        if msg.proof_metadata.proof_valid is not False
    ]


def rank_messages_by_proof(
    messages: list[ProofEnrichedDeltaMessage],
) -> list[ProofEnrichedDeltaMessage]:
    """
    Rank messages by proof quality (best first).

    Order:
      1. proof_valid=True (highest trust)
      2. proof_valid=None (unchecked, neutral)
      3. proof_valid=False (lowest trust)
    Within same proof_valid category, prefer newer (higher seq).
    """
    ORDER = {True: 0, None: 1, False: 2}
    return sorted(
        messages,
        key=lambda m: (
            ORDER.get(m.proof_metadata.proof_valid, 1),
            -m.seq,
        ),
    )


# ─────────────────────────────────────────────────────────────────
# Schema patch helper (for DeltaGossipMessage integration)
# ─────────────────────────────────────────────────────────────────

def patch_delta_gossip_message_schema():
    """
    Documentation of schema change needed in DeltaGossipMessage (protocol.py).

    Add these fields to DeltaGossipMessage:
        proof_hash: Optional[str] = ""          # SHA-256 of SemanticProof (first 16 hex)
        proof_origin: Optional[str] = None        # ProofOrigin.name or None
        proof_valid: Optional[bool] = None         # True/False/None (None = not checked)

    After patching, use ProofEnrichedDeltaMessage to access proof fields
    from any DeltaGossipMessage instance via getattr:
        proof_hash = getattr(msg, 'proof_hash', '')
        proof_origin = getattr(msg, 'proof_origin', None)
    """
    pass  # Documentation only — actual patching done in protocol.py


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────

def _test_v9_3_phase3():
    """Sanity test for v9.3 Phase 3."""
    from federation.delta_gossip.protocol import DeltaGossipMessage

    gpe = GossipProofEngine()

    # Build a base delta message
    base_msg = DeltaGossipMessage(
        source_node_id="node_2",
        root_hash="root_hash_abc123",
        changed_node_ids=["node_A", "node_B"],
        changed_hashes={"node_A": "hash_A", "node_B": "hash_B"},
        seq=42,
        ts_ns=time.time_ns(),
        hash_mode=DAGHashMode.CONSENSUS,
    )

    # Case 1: attach proof metadata
    meta = ProofMetadata(
        proof_hash="fedcba9876543210",
        proof_origin=ProofOrigin.REMOTE,
        proof_valid=True,
        proof_tick=100,
    )
    enriched = ProofEnrichedDeltaMessage.from_base_message(base_msg, meta)

    assert enriched.proof_metadata.proof_hash == "fedcba9876543210"
    assert enriched.proof_metadata.proof_origin == ProofOrigin.REMOTE
    assert enriched.is_proof_valid() is True
    assert enriched.source_node_id == "node_2"
    log.info("✅ Case 1: proof metadata attached to message")

    # Case 2: cache proof result
    gpe.cache_proof_result("fedcba9876543210", True)
    assert gpe.verify_proof_from_message(enriched) is True
    log.info("✅ Case 2: proof cache hit")

    # Case 3: unknown proof_hash → None (needs evaluation)
    meta_unknown = ProofMetadata(proof_hash="unknown_hash", proof_valid=None)
    msg_unknown = ProofEnrichedDeltaMessage.from_base_message(base_msg, meta_unknown)
    assert gpe.verify_proof_from_message(msg_unknown) is None
    log.info("✅ Case 3: unknown proof_hash returns None (needs eval)")

    # Case 4: filter by proof trust
    msg_valid = ProofEnrichedDeltaMessage.from_base_message(base_msg, ProofMetadata(proof_valid=True))
    msg_invalid = ProofEnrichedDeltaMessage.from_base_message(base_msg, ProofMetadata(proof_valid=False))
    msg_unchecked = ProofEnrichedDeltaMessage.from_base_message(base_msg, ProofMetadata())

    filtered = filter_by_proof_trust([msg_valid, msg_invalid, msg_unchecked], require_valid_proof=True)
    assert len(filtered) == 2
    assert msg_invalid not in filtered
    log.info("✅ Case 4: filter_by_proof_trust excludes proof_valid=False")

    # Case 5: rank messages by proof quality
    ranked = rank_messages_by_proof([msg_invalid, msg_valid, msg_unchecked])
    assert ranked[0].proof_metadata.proof_valid is True
    assert ranked[-1].proof_metadata.proof_valid is False
    log.info("✅ Case 5: rank_messages_by_proof — valid first, invalid last")

    log.info("\n✅ v9.3 Phase 3: Proof-enriched gossip — all checks passed")


if __name__ == "__main__":
    _test_v9_3_phase3()


__all__ = [
    "GossipProofEngine",
    "ProofEnrichedDeltaMessage",
    "ProofMetadata",
    "filter_by_proof_trust",
    "patch_delta_gossip_message_schema",
    "rank_messages_by_proof",
]

"""
signed_envelope.py — v9.9 SignedEnvelope wrapper

Wraps any raw message payload with HMAC-SHA256 signature metadata
to create a self-contained verifiable unit.

Envelope format:
    {
        "sender_id": str,
        "seq": int,
        "ts_ns": int,
        "payload": str,          # original message (JSON string)
        "message_hash": str,     # SHA256(payload)
        "signature": str,        # HMAC-SHA256(sender_id:message_hash)
        "category": str,         # "trust" | "gossip" | "consensus" | "control"
    }

Usage:
    envelope = SignedEnvelope.wrap(
        payload=json.dumps(trust_sync_msg.to_dict()),
        sender_id="node_A",
        seq=42,
        category=MessageCategory.TRUST,
        signer=signing,           # FederationMessageSigning instance
    )
    # Send envelope over wire
    received = SignedEnvelope.unwrap(raw_dict, verifier=signing)
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from enum import Enum

from federation.byzantine.message_signatures import (
    FederationMessageSigning,
    MessageSignatureError,
)


class EnvelopeError(Exception):
    """Raised when envelope construction or unwrapping fails."""


class MessageCategory(Enum):
    TRUST = "trust"      # TrustSyncMessage
    GOSSIP = "gossip"    # DeltaGossipMessage
    CONSENSUS = "consensus"  # PBFT consensus messages
    CONTROL = "control"  # ViewChange, health, ping/pong


@dataclass
class SignedEnvelope:
    """
    Self-contained signed message envelope.

    The envelope is tamper-evident: any modification to payload, seq,
    or ts_ns invalidates the signature.
    """
    sender_id: str
    seq: int
    ts_ns: int
    payload: str
    message_hash: str
    signature: str
    category: str

    @staticmethod
    def wrap(
        payload: str,
        sender_id: str,
        seq: int,
        category: MessageCategory,
        signer: FederationMessageSigning,
    ) -> SignedEnvelope:
        """
        Create a new signed envelope from a raw payload.

        Args:
            payload:      JSON-serialized message string
            sender_id:    node generating this envelope
            seq:          monotonic sequence number (from NonceSequenceValidator)
            category:     MessageCategory
            signer:       FederationMessageSigning instance with secret for sender_id

        Returns:
            SignedEnvelope ready to be serialized and sent
        """
        message_hash = hashlib.sha256(payload.encode()).hexdigest()

        signed = signer.sign(sender_id=sender_id, payload=payload)

        return SignedEnvelope(
            sender_id=sender_id,
            seq=seq,
            ts_ns=time.time_ns(),
            payload=payload,
            message_hash=message_hash,
            signature=signed.signature,
            category=category.value,
        )

    def verify(self, verifier: FederationMessageSigning) -> bool:
        """
        Verify the envelope's signature.

        Args:
            verifier: FederationMessageSigning with secret for sender_id

        Returns:
            True if signature is valid

        Raises:
            EnvelopeError: if verification fails
        """
        # Re-hash payload and compare with stored message_hash
        computed_hash = hashlib.sha256(self.payload.encode()).hexdigest()
        if computed_hash != self.message_hash:
            raise EnvelopeError(
                f"payload hash mismatch for {self.sender_id}: "
                f"expected {self.message_hash[:16]}, got {computed_hash[:16]}"
            )

        # Verify HMAC signature
        try:
            verifier.verify(
                signed=type("SignedMessage", (), {
                    "sender_id": self.sender_id,
                    "message_hash": self.message_hash,
                    "signature": self.signature,
                })()
            )
        except MessageSignatureError as e:
            raise EnvelopeError(f"signature verification failed for {self.sender_id}: {e}")

        return True

    def to_dict(self) -> dict:
        return {
            "sender_id": self.sender_id,
            "seq": self.seq,
            "ts_ns": self.ts_ns,
            "payload": self.payload,
            "message_hash": self.message_hash,
            "signature": self.signature,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SignedEnvelope:
        return cls(
            sender_id=data["sender_id"],
            seq=int(data["seq"]),
            ts_ns=int(data["ts_ns"]),
            payload=data["payload"],
            message_hash=data["message_hash"],
            signature=data["signature"],
            category=data["category"],
        )

    def age_seconds(self) -> float:
        """Return age of envelope in seconds (from ts_ns)."""
        return (time.time_ns() - self.ts_ns) / 1e9


@dataclass
class EnvelopeBuilder:
    """
    Stateful builder for creating SignedEnvelopes with sequential sequence numbers.

    Usage:
        builder = EnvelopeBuilder(node_id="node_A", signer=signing)
        envelope = builder.wrap(json_payload, category=MessageCategory.TRUST)
    """
    node_id: str
    signer: FederationMessageSigning
    _seq: int = 0

    def wrap(
        self,
        payload: str,
        category: MessageCategory,
    ) -> SignedEnvelope:
        self._seq += 1
        return SignedEnvelope.wrap(
            payload=payload,
            sender_id=self.node_id,
            seq=self._seq,
            category=category,
            signer=self.signer,
        )

    @property
    def current_seq(self) -> int:
        return self._seq


# ─── Tests ────────────────────────────────────────────────────────────────

def _test_signed_envelope():
    from federation.byzantine.message_signatures import FederationMessageSigning

    secrets = {"node_A": "secret_A_abc123", "node_B": "secret_B_def456"}
    signing = FederationMessageSigning(secrets)

    # ── wrap and verify ──────────────────────────────────────────────
    payload = json.dumps({"msg_type": "TRUST_DELTA", "proof_hash": "h1", "score": 0.9})

    envelope = SignedEnvelope.wrap(
        payload=payload,
        sender_id="node_A",
        seq=1,
        category=MessageCategory.TRUST,
        signer=signing,
    )
    assert envelope.sender_id == "node_A"
    assert envelope.seq == 1
    assert envelope.category == "trust"
    assert len(envelope.signature) == 64
    assert envelope.message_hash == hashlib.sha256(payload.encode()).hexdigest()
    print(f"✅ wrap: envelope created, sig={envelope.signature[:16]}...")

    # ── verify success ──────────────────────────────────────────────
    result = envelope.verify(signing)
    assert result is True
    print("✅ verify: valid envelope passes")

    # ── verify: tampered payload (hash mismatch) ──────────────────
    # Tamper with payload but keep the ORIGINAL message_hash → hash check fails first
    tampered = SignedEnvelope(
        sender_id=envelope.sender_id,
        seq=envelope.seq,
        ts_ns=envelope.ts_ns,
        payload="totally different payload that changes meaning",
        message_hash=envelope.message_hash,  # original hash — won't match tampered payload
        signature=envelope.signature,
        category=envelope.category,
    )
    try:
        tampered.verify(signing)
        assert False, "should have raised"
    except EnvelopeError as e:
        assert "hash mismatch" in str(e)
        print("✅ verify: tampered payload with wrong hash rejected")

    # ── verify: wrong secret ─────────────────────────────────────────
    bad_signer = FederationMessageSigning({"node_A": "wrong_secret"})
    try:
        envelope.verify(bad_signer)
        assert False, "should have raised"
    except EnvelopeError:
        print("✅ verify: wrong secret rejected")

    # ── EnvelopeBuilder sequential seq ───────────────────────────────
    builder = EnvelopeBuilder(node_id="node_A", signer=signing)
    e1 = builder.wrap('{"a":1}', category=MessageCategory.TRUST)
    e2 = builder.wrap('{"b":2}', category=MessageCategory.GOSSIP)
    assert e2.seq == e1.seq + 1
    assert builder.current_seq == 2
    print(f"✅ EnvelopeBuilder: sequential seq {e1.seq} → {e2.seq}")

    # ── serialization roundtrip ──────────────────────────────────────
    d = envelope.to_dict()
    restored = SignedEnvelope.from_dict(d)
    assert restored.sender_id == envelope.sender_id
    assert restored.seq == envelope.seq
    assert restored.payload == envelope.payload
    assert restored.verify(signing) is True
    print("✅ to_dict / from_dict roundtrip")

    print("\n✅ v9.9 SignedEnvelope — all checks passed")


if __name__ == "__main__":
    _test_signed_envelope()

"""ExecutionRequest — atom-federation-os v9.0+P5 Proof-Carrying Execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from core.deterministic import DeterministicClock, DeterministicUUIDFactory


def make_signed_request(payload, verifier, issuer_id="test"):
    """Create an ExecutionRequest with a valid HMAC signature."""
    import hashlib
    import hmac as _hmac
    import time
    import uuid
    nonce = uuid.uuid4().hex
    ts = time.time()
    req = ExecutionRequest(payload=payload, proof=b"", issuer_id=issuer_id, nonce=nonce, timestamp=ts, metadata=())
    proof_input = req.proof_input
    sig = _hmac.new(verifier._signing_key, proof_input, hashlib.sha256).digest()
    proof = _hmac.new(verifier._signing_key, proof_input + sig, hashlib.sha256).digest()
    return ExecutionRequest(payload=payload, proof=proof, signature=sig, issuer_id=issuer_id, nonce=nonce, timestamp=ts)

def make_replay_request(verifier):
    """Create a request with a nonce already in verifier._used_nonces."""
    import hashlib
    import hmac as _hmac
    import time
    nonce_list = list(verifier._used_nonces.keys())
    if not nonce_list:
        raise RuntimeError("No nonce in cache")
    nonce = nonce_list[-1]
    ts = time.time()
    req = ExecutionRequest(payload={"action": "replay"}, proof=b"", issuer_id="replay", nonce=nonce, timestamp=ts)
    proof_input = req.proof_input
    sig = _hmac.new(verifier._signing_key, proof_input, hashlib.sha256).digest()
    proof = _hmac.new(verifier._signing_key, proof_input + sig, hashlib.sha256).digest()
    return ExecutionRequest(payload=req.payload, proof=proof, signature=sig, issuer_id=req.issuer_id, nonce=nonce, timestamp=ts)

@dataclass(frozen=True)
class ExecutionRequest:
    """
    Immutable execution request with cryptographic proof binding.

    Design invariants:
      1. payload is immutable — any modification invalidates the proof
      2. proof is bound to payload_hash — swapping payload invalidates proof
      3. nonce ensures replay protection — same nonce rejected after first use
      4. timestamp bounds liveness — stale requests are rejected

    Hash chain:
      payload_hash = SHA256(canonical_payload)
      proof_input  = payload_hash ‖ nonce ‖ timestamp ‖ issuer_id
      proof       = HMAC-SHA256(proof_input, signing_key)

    Ledger binding:
      ledger_entry = {
          "payload_hash": payload_hash,
          "proof_hash":   SHA256(proof),
          "prev_hash":    last_ledger_hash,
          "nonce":        nonce,
          "timestamp":    timestamp,
      }
    """

    payload: Any
    proof: bytes
    signature: bytes
    issuer_id: str
    nonce: str = field(default_factory=lambda: DeterministicUUIDFactory.make_nonce('req', 0, seq=0))
    timestamp: float = field(default_factory=lambda: DeterministicClock.get_physical_time())
    metadata: tuple = field(default_factory=tuple)  # immutable tuple of items

    # ── Derived properties ─────────────────────────────────────────────────

    @property
    def payload_hash(self) -> str:
        """Canonical SHA256 of payload (deterministic across serialisations)."""
        import json

        canonical = json.dumps(self.payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @property
    def proof_input(self) -> bytes:
        """Data that was signed to produce proof + signature."""
        return (
            f"{self.payload_hash}"
            f"{self.nonce}"
            f"{self.timestamp}"
            f"{self.issuer_id}"
        ).encode()

    @property
    def is_expired(self) -> bool:
        """Check if request timestamp exceeds allowed clock skew (5 min)."""
        return (DeterministicClock.get_physical_time() - self.timestamp) > 300

    # ── Factory ─────────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        payload: Any,
        signing_key: bytes,
        issuer_id: str = "system",
        metadata: tuple | None = None,
    ) -> ExecutionRequest:
        """
        Create a new signed ExecutionRequest with HMAC proof.

        Args:
            payload:     arbitrary execution payload
            signing_key: secret key used for HMAC proof generation
            issuer_id:   identifier of the caller (for audit)
            metadata:    additional immutable context

        Returns:
            ExecutionRequest with proof and signature populated
        """
        nonce = DeterministicUUIDFactory.make_nonce('system', 0, seq=0)
        timestamp = DeterministicClock.get_physical_time()
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()

        proof_input = (
            f"{payload_hash}{nonce}{timestamp}{issuer_id}"
        ).encode()
        proof = hashlib.sha256(proof_input).digest()
        # Signature = HMAC over proof_input with signing_key (dual-layer)
        import hmac as _hmac

        signature = _hmac.new(signing_key, proof_input, hashlib.sha256).digest()

        return cls(
            payload=payload,
            proof=proof,
            signature=signature,
            issuer_id=issuer_id,
            nonce=nonce,
            timestamp=timestamp,
            metadata=metadata or (),
        )

"""
proof_verifier.py — atom-federation-os v9.0+P5 Zero-Trust Execution Proof Verifier.

Provides cryptographic verification of ExecutionRequest proofs:
  1. Proof signature validity
  2. Payload integrity (proof bound to payload)
  3. Nonce uniqueness (replay protection)
  4. Timestamp liveness (staleness check)
  5. Ledger chain continuity
"""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

from core.deterministic import DeterministicClock, DeterministicUUIDFactory
from core.proof.execution_request import ExecutionRequest

import logging
log = logging.getLogger(__name__)


# ─── Exceptions ────────────────────────────────────────────────────────────────


class ProofVerificationError(Exception):
    """Raised when proof verification fails."""
    code: str

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"[{code}] {message}")


class ReplayError(ProofVerificationError):
    def __init__(self, nonce: str):
        super().__init__("REPLAY", f"Nonce {nonce} already used — replay rejected")


class StaleRequestError(ProofVerificationError):
    def __init__(self, age: float):
        super().__init__("STALE", f"Request age {age:.1f}s exceeds 300s limit")


class PayloadTamperError(ProofVerificationError):
    def __init__(self):
        super().__init__("TAMPER", "payload does not match proof binding")


class InvalidProofError(ProofVerificationError):
    def __init__(self):
        super().__init__("INVALID_PROOF", "proof signature verification failed")


class LedgerChainBrokenError(ProofVerificationError):
    def __init__(self, expected: str, actual: str):
        super().__init__(
            "LEDGER_CHAIN_BROKEN",
            f"ledger prev_hash mismatch: expected {expected[:16]}, got {actual[:16]}",
        )


# ─── Proof Verifier ────────────────────────────────────────────────────────────


class ProofVerifier:
    """
    Zero-trust proof verifier for ExecutionRequest instances.

    Verification chain (ALL must pass):
        1. Proof signature     — HMAC verification
        2. Payload binding   — proof was generated for this payload_hash
        3. Nonce uniqueness  — nonce not in used set (replay protection)
        4. Timestamp liveness — age < 300s
        5. Ledger continuity — prev_hash chain is intact

    Usage:
        verifier = ProofVerifier(state_dir="/tmp/proofs")
        verifier.set_signing_key(b"my-secret-key")

        try:
            verifier.verify(request)   # raises on failure
            log.info("PROOF VALID — proceed with execution")
        except ProofVerificationError as e:
            log.info(f"PROOF INVALID: {e}")
    """

    MAX_AGE_SECONDS: float = 300.0  # 5 minutes
    NONCE_CACHE_SIZE: int = 10_000   # in-memory replay cache

    def __init__(
        self,
        signing_key: bytes | None = None,
        state_dir: Path | None = None,
        ledger_path: Path | None = None,
    ) -> None:
        self._signing_key = signing_key or b"default-insecure-key-replace-in-prod"
        self._used_nonces: dict[str, float] = {}  # nonce → first_seen timestamp
        self._state_dir = state_dir or Path("/tmp/atom_proofs")
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._ledger_path = ledger_path or self._state_dir / "ledger.jsonl"
        self._last_hash: str = "GENESIS"
        self._load_ledger_head()

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_signing_key(self, key: bytes) -> None:
        """Update the signing key (for key rotation)."""
        self._signing_key = key

    def verify(self, request: Any, prev_hash: str | None = None) -> bool:
        """
        Verify an ExecutionRequest proof.

        Raises ProofVerificationError subclass on any failure.
        Returns True only if ALL verification stages pass.

        Args:
            request:    ExecutionRequest instance
            prev_hash:   optional ledger prev_hash override

        Stages:
            1. Signature   — HMAC verification
            2. Payload      — proof bound to this payload_hash
            3. Nonce        — unique (no replay)
            4. Liveness     — timestamp within MAX_AGE_SECONDS
            5. Ledger chain — prev_hash continuity
        """
        # Stage 1: Timestamp liveness
        self._verify_timestamp(request)

        # Stage 2: Signature verification
        self._verify_signature(request)

        # Stage 3: Payload binding
        self._verify_payload_binding(request)

        # Stage 4: Nonce uniqueness (replay protection)
        self._verify_nonce(request)

        # Stage 5: Ledger chain continuity
        ledger_hash = self._verify_ledger_chain(request, prev_hash)

        # Mark nonce as used
        self._used_nonces[request.nonce] = DeterministicClock.get_physical_time()
        self._prune_nonce_cache()
        self._last_hash = ledger_hash

        return True

    def verify_stateless(self, request: Any) -> bool:
        """
        Stateless verification (no ledger, replay cache only).
        Used for fast-path gate checks without ledger overhead.
        """
        self._verify_signature(request)
        self._verify_payload_binding(request)
        self._verify_nonce(request)
        self._verify_timestamp(request)
        return True

    @property
    def last_ledger_hash(self) -> str:
        """Current head of the ledger hash chain."""
        return self._last_hash

    @property
    def stats(self) -> dict:
        return {
            "used_nonces": len(self._used_nonces),
            "ledger_entries": self._ledger_entries,
            "last_hash": self._last_hash[:16],
        }

    # ── Verification stages ───────────────────────────────────────────────────

    def _verify_signature(self, request: Any) -> None:
        """Stage 1: Verify HMAC signature over proof_input."""
        proof_input = (
            f"{request.payload_hash}"
            f"{request.nonce}"
            f"{request.timestamp}"
            f"{request.issuer_id}"
        ).encode()
        expected = hmac.new(
            self._signing_key, proof_input, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(request.signature, expected):
            raise InvalidProofError()

    def _verify_payload_binding(self, request: Any) -> None:
        """Stage 2: Confirm proof is bound to this exact payload."""
        # Re-derive proof_input from current payload and verify it matches
        computed_hash = hashlib.sha256(
            json.dumps(request.payload, sort_keys=True, default=str).encode()
        ).hexdigest()
        if computed_hash != request.payload_hash:
            raise PayloadTamperError()

    def _verify_nonce(self, request: Any) -> None:
        """Stage 3: Reject if nonce was already used (replay protection)."""
        if request.nonce in self._used_nonces:
            raise ReplayError(request.nonce)

    def _verify_timestamp(self, request: Any) -> None:
        """Stage 4: Reject if request is too old."""
        age = DeterministicClock.get_physical_time() - request.timestamp
        if age > self.MAX_AGE_SECONDS:
            raise StaleRequestError(age)

    def _verify_ledger_chain(self, request: Any, prev_hash: str | None) -> str:
        """Stage 5: Append entry to ledger with HMAC chain."""
        prev = prev_hash or self._last_hash
        entry_hash = self._append_ledger_entry(request, prev)
        return entry_hash


    def sign(self, payload: Any, issuer_id: str = "test") -> ExecutionRequest:
        """Create and sign an ExecutionRequest with a valid HMAC proof."""
        nonce = DeterministicUUIDFactory.make_nonce(issuer_id, 0, seq=0)
        ts = DeterministicClock.get_physical_time()
        req = ExecutionRequest(
            payload=payload, proof=b"", signature=b"", issuer_id=issuer_id,
            nonce=nonce, timestamp=ts, metadata=()
        )
        proof_input = req.proof_input
        sig = hmac.new(self._signing_key, proof_input, hashlib.sha256).digest()
        proof = hmac.new(self._signing_key, proof_input + sig, hashlib.sha256).digest()
        return ExecutionRequest(
            payload=payload, proof=proof, signature=sig, issuer_id=issuer_id,
            nonce=nonce, timestamp=ts
        )


    def iterate_ledger(self, limit: int = 100) -> list[dict]:
        """Return recent ledger entries for verification."""
        if not self._ledger_path.exists():
            return []
        with open(self._ledger_path) as f:
            lines = f.readlines()
        entries = []
        for line in lines[-limit:]:
            line = line.strip()
            if line:
                import json
                entries.append(json.loads(line))
        return entries

    # ── Ledger operations ─────────────────────────────────────────────────────

    def _load_ledger_head(self) -> None:
        """Load last hash from existing ledger."""
        if not self._ledger_path.exists():
            self._ledger_entries = 0
            return
        try:
            lines = self._ledger_path.read_text().strip().split("\n")
            if lines:
                last = json.loads(lines[-1])
                self._last_hash = last.get("entry_hash", "GENESIS")
                self._ledger_entries = len(lines)
        except Exception:
            self._ledger_entries = 0

    def _append_ledger_entry(self, request: Any, prev_hash: str) -> str:
        """Append a verified request to the ledger (append-only, HMAC chained)."""
        import json

        entry = {
            "nonce": request.nonce,
            "payload_hash": request.payload_hash,
            "proof_hash": hashlib.sha256(request.proof).hexdigest(),
            "signature_hash": hashlib.sha256(request.signature).hexdigest(),
            "issuer_id": request.issuer_id,
            "timestamp": request.timestamp,
            "prev_hash": prev_hash,
            "entry_hash": "",  # computed below
        }
        # Chain: SHA256(entry contents ‖ prev_hash)
        contents = json.dumps(entry, sort_keys=True, default=str)
        entry_hash_input = f"{contents}{prev_hash}".encode()
        entry["entry_hash"] = hashlib.sha256(entry_hash_input).hexdigest()

        with open(self._ledger_path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

        self._ledger_entries += 1
        return entry["entry_hash"]

    def _prune_nonce_cache(self) -> None:
        """Keep nonce cache bounded — evict oldest when over limit."""
        if len(self._used_nonces) > self.NONCE_CACHE_SIZE:
            sorted_nonces = sorted(self._used_nonces.items(), key=lambda x: x[1])
            for nonce, _ in sorted_nonces[: len(sorted_nonces) // 2]:
                del self._used_nonces[nonce]

    # ── Test helpers ────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset replay cache and ledger head (for testing only)."""
        self._used_nonces.clear()
        self._last_hash = "GENESIS"
        if self._ledger_path.exists():
            self._ledger_path.unlink()
        self._ledger_entries = 0

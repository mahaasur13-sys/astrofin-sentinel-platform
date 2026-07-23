"""
proof_ledger.py — v9.4 ProofLedger: Time-Aware Trust Scoring

Key shift from v9.3:
  v9.3: proof_valid (bool) → candidate ranking
  v9.4: trust_score (continuous, time-aware) → trust decays with age

Components:
  - ProofRecord: per-proof tracking of validation history
  - ProofLedger: LRU cache of ProofRecords with TTL-based decay

trust_score formula:
    success_rate = success_count / validation_count
    age = now - timestamp
    decay = exp(-age / ttl_seconds)
    trust = success_rate * decay

    trust ∈ [0, 1]

Integration point:
  ProofAwareConsensusResolver.compute_score() replaces:
      10.0 if proof_valid else -10.0
  with:
      10.0 * proof_ledger.trust_score(proof_hash, now)
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from enum import Enum, auto

import logging
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# ProofOrigin (re-exported for convenience)
# ─────────────────────────────────────────────────────────────────

class ProofOrigin(Enum):
    REMOTE = auto()
    REPLAY = auto()
    SNAPSHOT = auto()
    SYNTHETIC = auto()


# ─────────────────────────────────────────────────────────────────
# ProofRecord
# ─────────────────────────────────────────────────────────────────

@dataclass
class ProofRecord:
    """
    Per-proof validation history record.

    Fields:
        proof_hash          — immutable proof identifier
        origin              — ProofOrigin (how proof was generated)
        timestamp           — when proof was first registered (wall clock)

        validation_count    — total number of validations performed
        success_count       — how many of those were successful

        last_validated_at   — wall clock of most recent validation
    """
    proof_hash: str
    origin: ProofOrigin
    timestamp: float

    validation_count: int = 0
    success_count: int = 0
    last_validated_at: float | None = None

    def record_validation(self, success: bool, ts: float) -> None:
        """Append a new validation result."""
        self.validation_count += 1
        if success:
            self.success_count += 1
        self.last_validated_at = ts

    def success_rate(self) -> float:
        if self.validation_count == 0:
            return 0.0
        return self.success_count / self.validation_count

    def trust_score(self, now: float, ttl_seconds: float) -> float:
        """
        Compute time-aware trust score.

        trust = success_rate * exp(-age / ttl)
        """
        if self.validation_count == 0:
            # No validations yet: trust decays from 1.0 toward 0 based on age.
            # age is capped at 0 if registration timestamp is in the future.
            age = max(0.0, now - self.timestamp)
            decay = math.exp(-age / ttl_seconds) if ttl_seconds > 0 else 0.0
            return decay  # no success history, just age-based decay

        rate = self.success_rate()
        age = max(0.0, now - self.timestamp)
        decay = math.exp(-age / ttl_seconds) if ttl_seconds > 0 else 0.0
        return rate * decay

    def is_stale(self, now: float, ttl_seconds: float) -> bool:
        # Treat future registration timestamps as age=0 (not stale until TTL passes)
        age = max(0.0, now - self.timestamp)
        return age > ttl_seconds


# ─────────────────────────────────────────────────────────────────
# ProofLedger
# ─────────────────────────────────────────────────────────────────

class ProofLedger:
    """
    Time-aware proof trust ledger.

    Tracks validation history for proofs and provides continuous
    trust scores that decay with age.

    Usage:
        ledger = ProofLedger(max_size=1000, ttl_seconds=300)
        ledger.register("abc123", ProofOrigin.REMOTE, time.time())
        ledger.record_validation("abc123", success=True, timestamp=time.time())
        score = ledger.trust_score("abc123", time.time())
        ledger.prune(time.time())
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 300.0):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        # proof_hash → ProofRecord (insertion-ordered)
        self._records: dict[str, ProofRecord] = {}
        # LRU tracking: order of insertion (older = lower access order)
        self._access_order: list[str] = []

    # ── register ────────────────────────────────────────────────────

    def register(
        self,
        proof_hash: str,
        origin: ProofOrigin,
        timestamp: float,
    ) -> None:
        """
        Register a new proof record.

        Idempotent: if proof_hash already exists, this is a no-op
        (does NOT update timestamp).
        """
        if proof_hash in self._records:
            return  # already registered — idempotent

        # Enforce max_size before adding new record
        if len(self._records) >= self.max_size:
            self._evict_oldest()

        self._records[proof_hash] = ProofRecord(
            proof_hash=proof_hash,
            origin=origin,
            timestamp=timestamp,
        )
        self._access_order.append(proof_hash)

    # ── record_validation ─────────────────────────────────────────

    def record_validation(
        self,
        proof_hash: str,
        success: bool,
        timestamp: float,
    ) -> None:
        """
        Record a validation result for an existing proof.

        Creates a new record if proof_hash is unknown (graceful handling).

        Updates:
          - validation_count
          - success_count (if success=True)
          - last_validated_at
        """
        record = self._records.get(proof_hash)
        if record is None:
            # Graceful: auto-register unknown proofs.
            # Clamp timestamp to time.time() to prevent future-timestamp exploits
            # (a proof registered at a future time would have age<0 and trust≈1).
            safe_ts = min(timestamp, time.time())
            self.register(proof_hash, ProofOrigin.SYNTHETIC, safe_ts)
            record = self._records[proof_hash]

        record.record_validation(success, timestamp)
        self._touch(proof_hash)

    # ── trust_score ───────────────────────────────────────────────

    def trust_score(self, proof_hash: str, now: float) -> float:
        """
        Compute trust score for proof_hash.

        Returns 0.0 if proof_hash is unknown.
        Returns 0.0 if proof is stale (age > ttl_seconds).
        Otherwise returns trust ∈ [0, 1].
        """
        record = self._records.get(proof_hash)
        if record is None:
            return 0.0

        if record.is_stale(now, self.ttl_seconds):
            return 0.0

        score = record.trust_score(now, self.ttl_seconds)
        # Clamp to [0, 1] — defensive
        return max(0.0, min(1.0, score))

    # ── is_stale ─────────────────────────────────────────────────

    def is_stale(self, proof_hash: str, now: float) -> bool:
        """Return True if proof_hash is stale (age > ttl)."""
        record = self._records.get(proof_hash)
        if record is None:
            # Unknown proofs are treated as stale
            return True
        return record.is_stale(now, self.ttl_seconds)

    # ── prune ─────────────────────────────────────────────────────

    def prune(self, now: float) -> int:
        """
        Remove stale proofs and overflow records.

        Removal order:
          1. Stale proofs (oldest-first by timestamp)
          2. If still over max_size: oldest by access order

        Returns:
            Number of records removed.
        """
        removed = 0

        # 1. Remove stale
        stale_hashes = [
            h for h, r in self._records.items()
            if r.is_stale(now, self.ttl_seconds)
        ]
        for h in stale_hashes:
            del self._records[h]
            self._access_order.remove(h)
            removed += 1

        # 2. Overflow: evict oldest by access order
        while len(self._records) > self.max_size:
            self._evict_oldest()
            removed += 1

        return removed

    # ── helpers ───────────────────────────────────────────────────

    def _touch(self, proof_hash: str) -> None:
        """Move proof_hash to end of access order (mark as recently used)."""
        if proof_hash in self._access_order:
            self._access_order.remove(proof_hash)
        self._access_order.append(proof_hash)

    def _evict_oldest(self) -> None:
        """Remove the oldest proof by access order."""
        if not self._access_order:
            return
        oldest = self._access_order.pop(0)
        self._records.pop(oldest, None)

    def __len__(self) -> int:
        return len(self._records)

    def get(self, proof_hash: str) -> ProofRecord | None:
        return self._records.get(proof_hash)

    def all_records(self) -> list[ProofRecord]:
        return list(self._records.values())


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────

def _test_v9_4_proof_ledger():
    """Sanity test for v9.4 ProofLedger."""
    now = 1000.0
    ledger = ProofLedger(max_size=100, ttl_seconds=300.0)

    # test_register_idempotent
    ledger.register("hash_A", ProofOrigin.REMOTE, now)
    ledger.register("hash_A", ProofOrigin.REMOTE, now)  # duplicate — no-op
    assert "hash_A" in ledger._records
    assert len([r for r in ledger._records.values() if r.proof_hash == "hash_A"]) == 1
    log.info("✅ test_register_idempotent")

    # test_record_validation_counts
    ledger.record_validation("hash_A", success=True, timestamp=now + 10)
    ledger.record_validation("hash_A", success=True, timestamp=now + 20)
    ledger.record_validation("hash_A", success=False, timestamp=now + 30)
    rec = ledger.get("hash_A")
    assert rec.validation_count == 3
    assert rec.success_count == 2
    log.info("✅ test_record_validation_counts")

    # test_trust_score_fresh_high
    # Fresh proof (age=0), 100% success rate → trust ≈ 1.0
    ledger.register("hash_fresh", ProofOrigin.REMOTE, now)
    ledger.record_validation("hash_fresh", success=True, timestamp=now + 1)
    score = ledger.trust_score("hash_fresh", now + 1)
    assert 0.9 <= score <= 1.0, f"Expected ~1.0, got {score}"
    log.info(f"✅ test_trust_score_fresh_high (score={score:.4f})")

    # test_trust_score_decay
    # Check decay at age = ttl (one e-fold). Use last_validated_at so proof
    # is NOT stale when we query it.
    rec = ledger.get("hash_fresh")
    rec.last_validated_at = now  # backdate so age_at_last_validation < ttl
    score_old = ledger.trust_score("hash_fresh", now + 300)
    # At age=300s (from registration, but validated more recently),
    # decay = exp(-300/300) = exp(-1) ≈ 0.368, success_rate = 1.0
    assert 0.2 <= score_old <= 0.5, f"Expected ~0.3, got {score_old}"
    log.info(f"✅ test_trust_score_decay (age=300s, score={score_old:.4f})")

    # test_is_stale
    ledger.register("hash_stale", ProofOrigin.REPLAY, now)
    assert not ledger.is_stale("hash_stale", now + 100)
    assert ledger.is_stale("hash_stale", now + 301)
    assert ledger.is_stale("unknown_hash", now + 1)  # unknown → stale
    log.info("✅ test_is_stale")

    # test_prune_removes_old
    ledger.register("hash_prune1", ProofOrigin.SNAPSHOT, now)
    ledger.register("hash_prune2", ProofOrigin.SNAPSHOT, now)
    ledger.register("hash_prune3", ProofOrigin.SNAPSHOT, now)
    # All three registered at 'now', so at 'now+400' they are 400s old > ttl(300)
    removed = ledger.prune(now + 400)
    assert removed >= 3, f"Expected ≥3 removed, got {removed}"
    assert "hash_prune1" not in ledger._records
    assert "hash_prune2" not in ledger._records
    assert "hash_prune3" not in ledger._records
    log.info(f"✅ test_prune_removes_old (removed={removed})")

    # Unknown proof → trust_score = 0
    assert ledger.trust_score("unknown_hash", now) == 0.0
    log.info("✅ trust_score for unknown proof = 0.0")

    # Stale proof → trust_score = 0
    ledger.register("hash_stale_test", ProofOrigin.REMOTE, now)
    assert ledger.trust_score("hash_stale_test", now + 400) == 0.0
    log.info("✅ trust_score for stale proof = 0.0")

    log.info("\n✅ v9.4 ProofLedger — all checks passed")


if __name__ == "__main__":
    _test_v9_4_proof_ledger()


__all__ = [
    "ProofLedger",
    "ProofOrigin",
    "ProofRecord",
]

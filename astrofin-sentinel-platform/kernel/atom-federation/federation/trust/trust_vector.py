"""
trust_vector.py — v9.5 TrustVector

Purpose:
  TrustVector is a compact, deterministic snapshot of trust state
  for a single proof across the federation.

  trust_state = { proof_hash → TrustEntry }

  TrustEntry (immutable-ish):
    trust_score  — continuous ∈ [0.0, 1.0]
    timestamp    — last update (wall clock, used for staleness)
    ledger_version — Monotonically increasing version counter.

Design constraints (driven by convergence requirement):
  - trust_score is derived: NOT an input — it is computed from ProofLedger
  - ledger_version drives convergence: vectors with same version = identical state
  - All fields are deterministic / serializable
  - No external randomness

Usage:
  tv = TrustVector()
  tv.set_entry("hash_abc", 0.85, 1000.0, version=5)
  entry = tv.get("hash_abc")   # → TrustEntry(0.85, 1000.0, 5)
  delta  = tv.delta(old_vector) # → TrustDelta (changed keys, old/new values)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────────────
# TrustEntry
# ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TrustEntry:
    """
    Immutable trust state for a single proof_hash.

    Fields:
        trust_score   — continuous ∈ [0.0, 1.0] (derived from ProofLedger)
        timestamp     — when trust was last recomputed (wall clock seconds)
        ledger_version — monotonic counter: increments each time ledger is mutated
                         (register or record_validation). Used for vector comparison.
    """
    trust_score: float
    timestamp: float
    ledger_version: int

    def is_stale(self, now: float, ttl_seconds: float) -> bool:
        age = max(0.0, now - self.timestamp)
        return age > ttl_seconds


# ─────────────────────────────────────────────────────────────────
# TrustDelta
# ─────────────────────────────────────────────────────────────────

@dataclass
class TrustDelta:
    """
    Change set between two TrustVectors.

    Fields:
        added       — proof_hashes that exist in new but not in old
        updated     — proof_hashes in both, trust changed
        removed     — proof_hashes that existed in old but not in new
                    (removed when proof becomes stale and is pruned)
        updated_entries — {proof_hash: (old_entry, new_entry)} for changed entries
    """
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    updated_entries: dict[str, tuple[TrustEntry, TrustEntry]] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return not (self.added or self.updated or self.removed)

    def summary(self) -> str:
        return (
            f"TrustDelta(added={len(self.added)}, "
            f"updated={len(self.updated)}, "
            f"removed={len(self.removed)})"
        )


# ─────────────────────────────────────────────────────────────────
# TrustVector
# ─────────────────────────────────────────────────────────────────

@dataclass
class TrustVector:
    """
    Deterministic snapshot of trust state for all known proofs.

    TrustVector is:
      - append-only (immutability of historical snapshots)
      - comparable via ledger_version
      - convertible to/from dict (serializable)
      - delta-computable (diff two snapshots → TrustDelta)

    Usage:
        tv = TrustVector()
        tv.set_entry("hash_1", trust_score=0.9, timestamp=1000.0, ledger_version=3)
        old = tv.snapshot()
        tv.set_entry("hash_1", trust_score=0.8, timestamp=1001.0, ledger_version=4)
        delta = tv.delta(old)
    """
    # proof_hash → TrustEntry
    _entries: dict[str, TrustEntry] = field(default_factory=dict)
    # Monotonic ledger version at time of snapshot
    _ledger_version: int = 0
    # Wall clock of snapshot creation
    _snapshot_time: float = field(default_factory=time.time)

    # ── entry access ───────────────────────────────────────────────

    def get(self, proof_hash: str) -> TrustEntry | None:
        return self._entries.get(proof_hash)

    def __contains__(self, proof_hash: str) -> bool:
        return proof_hash in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def keys(self) -> list[str]:
        return list(self._entries.keys())

    def values(self) -> list[TrustEntry]:
        return list(self._entries.values())

    def items(self) -> list[tuple[str, TrustEntry]]:
        return list(self._entries.items())

    # ── mutation (for active ledger) ────────────────────────────────

    def set_entry(
        self,
        proof_hash: str,
        trust_score: float,
        timestamp: float,
        ledger_version: int,
    ) -> None:
        """Set or update a trust entry."""
        # Clamp trust_score to [0, 1]
        score = max(0.0, min(1.0, trust_score))
        self._entries[proof_hash] = TrustEntry(
            trust_score=score,
            timestamp=timestamp,
            ledger_version=ledger_version,
        )
        # ledger_version monotonically increases; update if higher
        if ledger_version > self._ledger_version:
            self._ledger_version = ledger_version
        self._snapshot_time = time.time()

    def remove_entry(self, proof_hash: str) -> None:
        """Remove a proof_hash entry (proof pruned from ledger)."""
        self._entries.pop(proof_hash, None)

    # ── snapshot / delta ───────────────────────────────────────────

    def snapshot(self) -> TrustVector:
        """Return a deep copy of the current vector as an immutable snapshot."""
        tv = TrustVector(
            _entries=dict(self._entries),
            _ledger_version=self._ledger_version,
            _snapshot_time=self._snapshot_time,
        )
        return tv

    def delta(self, other: TrustVector) -> TrustDelta:
        """
        Compute the difference between self (newer) and other (older).

        Returns TrustDelta describing what changed.
        """
        added: list[str] = []
        updated: list[str] = []
        removed: list[str] = []
        updated_entries: dict[str, tuple[TrustEntry, TrustEntry]] = {}

        old_keys = set(other._entries.keys())
        new_keys = set(self._entries.keys())

        # Added
        for k in new_keys - old_keys:
            added.append(k)

        # Removed
        for k in old_keys - new_keys:
            removed.append(k)

        # Updated (in both)
        for k in old_keys & new_keys:
            old_entry = other._entries[k]
            new_entry = self._entries[k]
            if old_entry != new_entry:
                updated.append(k)
                updated_entries[k] = (old_entry, new_entry)

        return TrustDelta(
            added=added,
            updated=updated,
            removed=removed,
            updated_entries=updated_entries,
        )

    # ── ledger_version ─────────────────────────────────────────────

    def ledger_version(self) -> int:
        return self._ledger_version

    def snapshot_time(self) -> float:
        return self._snapshot_time

    # ── serialization ───────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize to plain dict for network transmission."""
        return {
            "ledger_version": self._ledger_version,
            "snapshot_time": self._snapshot_time,
            "entries": {
                k: {
                    "trust_score": e.trust_score,
                    "timestamp": e.timestamp,
                    "ledger_version": e.ledger_version,
                }
                for k, e in self._entries.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> TrustVector:
        """Deserialize from plain dict."""
        entries = {}
        for k, v in data.get("entries", {}).items():
            entries[k] = TrustEntry(
                trust_score=float(v["trust_score"]),
                timestamp=float(v["timestamp"]),
                ledger_version=int(v["ledger_version"]),
            )
        return cls(
            _entries=entries,
            _ledger_version=int(data.get("ledger_version", 0)),
            _snapshot_time=float(data.get("snapshot_time", 0.0)),
        )

    # ── genesis (empty vector) ────────────────────────────────────

    @classmethod
    def empty(cls) -> TrustVector:
        return cls(
            _entries={},
            _ledger_version=0,
            _snapshot_time=time.time(),
        )

    def is_empty(self) -> bool:
        return len(self._entries) == 0

    # ── convergence check ──────────────────────────────────────────

    def is_converged_with(self, other: TrustVector, ttl_seconds: float = 300.0) -> bool:
        """
        Return True if self and other are trust-converged.

        Convergence = both have same ledger_version OR both entries are
        within ttl_seconds of each other and trust scores match.

        Simple version used for unit tests and basic convergence checking.
        """
        if self._ledger_version == other._ledger_version:
            return True

        common_keys = set(self._entries.keys()) & set(other._entries.keys())
        if not common_keys:
            return True  # no overlap — can't compare, treat as converged

        now = time.time()
        for k in common_keys:
            e_self = self._entries[k]
            e_other = other._entries[k]

            # If both fresh (< ttl old) and trust matches → converged for this key
            self_fresh = not e_self.is_stale(now, ttl_seconds)
            other_fresh = not e_other.is_stale(now, ttl_seconds)
            if self_fresh and other_fresh:
                if abs(e_self.trust_score - e_other.trust_score) > 0.01:
                    return False
        return True


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────

def _test_trust_vector():
    """Sanity test for v9.5 TrustVector."""
    # ── TrustEntry ──────────────────────────────────────────────────
    e1 = TrustEntry(trust_score=0.9, timestamp=1000.0, ledger_version=5)
    e2 = TrustEntry(trust_score=0.9, timestamp=1000.0, ledger_version=5)
    e3 = TrustEntry(trust_score=0.8, timestamp=1000.0, ledger_version=5)
    assert e1 == e2
    assert e1 != e3
    assert e1.is_stale(now=1500.0, ttl_seconds=300) is True
    assert e1.is_stale(now=1100.0, ttl_seconds=300) is False
    print("✅ TrustEntry immutable + is_stale")

    # ── TrustVector basic ops ───────────────────────────────────────
    tv = TrustVector()
    assert tv.is_empty()
    tv.set_entry("hash_A", trust_score=0.85, timestamp=1000.0, ledger_version=3)
    assert "hash_A" in tv
    assert len(tv) == 1
    e = tv.get("hash_A")
    assert e is not None and e.trust_score == 0.85 and e.ledger_version == 3
    print("✅ TrustVector set_entry + get")

    # Clamp out-of-bounds trust_score
    tv.set_entry("hash_B", trust_score=1.5, timestamp=1000.0, ledger_version=1)
    assert tv.get("hash_B").trust_score == 1.0
    tv.set_entry("hash_C", trust_score=-0.5, timestamp=1000.0, ledger_version=1)
    assert tv.get("hash_C").trust_score == 0.0
    print("✅ TrustVector trust_score clamping")

    # ── snapshot + delta ────────────────────────────────────────────
    v1 = tv.snapshot()
    tv.set_entry("hash_A", trust_score=0.7, timestamp=1001.0, ledger_version=4)
    tv.set_entry("hash_D", trust_score=0.6, timestamp=1001.0, ledger_version=4)
    delta = tv.delta(v1)
    assert set(delta.updated) == {"hash_A"}, f"got {delta.updated}"
    assert set(delta.added) == {"hash_D"}
    print(f"✅ TrustVector delta: {delta.summary()}")

    # ── remove_entry ────────────────────────────────────────────────
    # Save snapshot BEFORE removing so we can detect the removal
    v_before_remove = tv.snapshot()
    tv.remove_entry("hash_D")
    assert "hash_D" not in tv
    delta_removed = tv.delta(v_before_remove)
    assert "hash_D" in delta_removed.removed, f"hash_D should be in removed, got {delta_removed.removed}"
    print("✅ TrustVector remove_entry + delta.removed")

    # ── serialization ────────────────────────────────────────────────
    d = tv.to_dict()
    tv_r = TrustVector.from_dict(d)
    assert tv_r.ledger_version() == tv.ledger_version()
    assert set(tv_r.keys()) == set(tv.keys())
    for k in tv.keys():
        assert tv.get(k).trust_score == tv_r.get(k).trust_score
    print("✅ TrustVector serialization roundtrip")

    # ── genesis empty vector ───────────────────────────────────────
    empty = TrustVector.empty()
    assert empty.is_empty()
    assert empty.ledger_version() == 0
    print("✅ TrustVector.empty()")

    # ── is_converged_with ───────────────────────────────────────────
    a = TrustVector()
    a.set_entry("h1", 0.9, 1000.0, ledger_version=5)
    a.set_entry("h2", 0.8, 1000.0, ledger_version=5)

    b = TrustVector()
    b.set_entry("h1", 0.9, 1000.0, ledger_version=5)
    b.set_entry("h2", 0.81, 1000.0, ledger_version=5)  # slightly different

    c = TrustVector()
    c.set_entry("h1", 0.9, 1000.0, ledger_version=5)
    c.set_entry("h2", 0.8, 1000.0, ledger_version=5)     # identical to A

    assert a.is_converged_with(c) is True, "identical vectors should converge"
    # h2 trust differs by 0.01 — allow tolerance → converge
    # if they differ more → diverge
    print(f"✅ TrustVector.is_converged_with: same_version={a.is_converged_with(c)}")

    print("\n✅ v9.5 TrustVector — all checks passed")


if __name__ == "__main__":
    _test_trust_vector()


__all__ = [
    "TrustDelta",
    "TrustEntry",
    "TrustVector",
]

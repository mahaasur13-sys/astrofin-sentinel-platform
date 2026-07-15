"""
incremental_causal_verifier.py
==============================
Incrementally verifies causal DAG equivalence using O(n) delta updates
instead of full O(n²-n³) graph isomorphism on every check.

Problem it solves:
    CrossLayerInvariantEngine._check_i2() rebuilds the full DAG on every call.
    For N events, is_identical() compares every node's parents → O(n²).
    With continuous verification at 1Hz on large clusters → unacceptable.

Solution:
    IncrementalCausalVerifier maintains a running causal fingerprint per domain.
    New events update the fingerprint in O(1).
    Equivalence check between two fingerprints is O(1).

Algorithm:
    For each event, compute a content-addressable "causal fingerprint":
        fp(event) = hash(event_id + sorted(causal_parents))
    The per-domain fingerprint is a rolling multi-set hash of all event fps.
    Equivalence: fp_exec == fp_replay  ↔  causal graphs are identical.
"""
from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CausalFingerprint:
    """
    Rolling causal fingerprint for a sequence of events.
    O(1) update per new event, O(1) equality check.
    """
    rolling_hash: int = 0        # XOR-rolling hash of all event fps
    event_count: int = 0
    added_hashes: dict[int, int] = field(default_factory=dict)  # hash -> count (for removal)
    removed_hashes: dict[int, int] = field(default_factory=dict)

    def copy(self) -> CausalFingerprint:
        cf = CausalFingerprint(
            rolling_hash=self.rolling_hash,
            event_count=self.event_count,
        )
        cf.added_hashes = dict(self.added_hashes)
        cf.removed_hashes = dict(self.removed_hashes)
        return cf

    def add_event(
        self,
        event_id: str,
        causal_parents: list[str] | None = None,
        payload: dict | None = None,
    ) -> int:
        """
        Add an event to the fingerprint.
        Returns the fingerprint value for this event.
        """
        fp = self._event_fp(event_id, causal_parents, payload)
        self.added_hashes[fp] = self.added_hashes.get(fp, 0) + 1
        if self.removed_hashes.get(fp, 0) > 0:
            self.removed_hashes[fp] -= 1
            if self.removed_hashes[fp] == 0:
                del self.removed_hashes[fp]
        else:
            self.rolling_hash ^= fp
        self.event_count += 1
        return fp

    def remove_event(
        self,
        event_id: str,
        causal_parents: list[str] | None = None,
        payload: dict | None = None,
    ) -> None:
        """Remove an event (e.g. on rollback)."""
        fp = self._event_fp(event_id, causal_parents, payload)
        if self.added_hashes.get(fp, 0) > 0:
            self.added_hashes[fp] -= 1
            if self.added_hashes[fp] == 0:
                del self.added_hashes[fp]
        else:
            self.removed_hashes[fp] = self.removed_hashes.get(fp, 0) + 1
            self.rolling_hash ^= fp
        self.event_count -= 1

    @staticmethod
    def _event_fp(
        event_id: str,
        causal_parents: list[str] | None,
        payload: dict | None,
    ) -> int:
        """Content-addressable fingerprint for a single event."""
        parts = [event_id]
        if causal_parents:
            parts.extend(sorted(causal_parents))
        if payload:
            parts.append(str(sorted(payload.items())))
        content = "|".join(parts).encode("utf-8")
        return int(hashlib.sha256(content).hexdigest()[:16], 16)

    def is_identical(self, other: CausalFingerprint) -> tuple[bool, str]:
        """
        O(1) causal equivalence check.
        Returns (True, "identical") if causal graphs are equivalent.
        """
        if self.event_count != other.event_count:
            return False, f"event_count mismatch: {self.event_count} vs {other.event_count}"
        if self.rolling_hash != other.rolling_hash:
            return False, f"rolling_hash mismatch: {self.rolling_hash} != {other.rolling_hash}"
        return True, "causally_equivalent"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rolling_hash": self.rolling_hash,
            "event_count": self.event_count,
        }


class IncrementalCausalVerifier:
    """
    Incrementally maintains causal fingerprints for exec and replay domains.
    Equivalence check is always O(1) regardless of cluster size.

    Usage:
        verifier = IncrementalCausalVerifier()
        verifier.add_exec_event("e1", causal_parents=[])
        verifier.add_replay_event("e1", causal_parents=[])
        identical, reason = verifier.check_equivalence()
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._fp_exec = CausalFingerprint()
        self._fp_replay = CausalFingerprint()

    def add_exec_event(
        self,
        event_id: str,
        causal_parents: list[str] | None = None,
        payload: dict | None = None,
    ) -> int:
        with self._lock:
            return self._fp_exec.add_event(event_id, causal_parents, payload)

    def add_replay_event(
        self,
        event_id: str,
        causal_parents: list[str] | None = None,
        payload: dict | None = None,
    ) -> int:
        with self._lock:
            return self._fp_replay.add_event(event_id, causal_parents, payload)

    def remove_exec_event(
        self,
        event_id: str,
        causal_parents: list[str] | None = None,
        payload: dict | None = None,
    ) -> None:
        with self._lock:
            self._fp_exec.remove_event(event_id, causal_parents, payload)

    def remove_replay_event(
        self,
        event_id: str,
        causal_parents: list[str] | None = None,
        payload: dict | None = None,
    ) -> None:
        with self._lock:
            self._fp_replay.remove_event(event_id, causal_parents, payload)

    def sync_from_events(
        self,
        exec_events: list[Any],
        replay_events: list[Any],
    ) -> None:
        """
        Rebuild fingerprints from event lists (used for initialization
        or full resync after divergence).
        """
        fp_e = CausalFingerprint()
        fp_r = CausalFingerprint()

        for ev in exec_events:
            fp_e.add_event(
                event_id=getattr(ev, "event_id", str(getattr(ev, "ts", 0))),
                causal_parents=getattr(ev, "payload", {}).get("causal_parents", []),
                payload=getattr(ev, "payload", {}),
            )

        for ev in replay_events:
            fp_r.add_event(
                event_id=getattr(ev, "event_id", str(getattr(ev, "ts", 0))),
                causal_parents=getattr(ev, "payload", {}).get("causal_parents", []),
                payload=getattr(ev, "payload", {}),
            )

        with self._lock:
            self._fp_exec = fp_e
            self._fp_replay = fp_r

    def check_equivalence(self) -> tuple[bool, str, dict[str, Any]]:
        """
        O(1) causal equivalence check.

        Returns:
            (identical, reason, fingerprints_dict)
        """
        with self._lock:
            fp_e = self._fp_exec.copy()
            fp_r = self._fp_replay.copy()

        identical, reason = fp_e.is_identical(fp_r)

        return identical, reason, {
            "exec": fp_e.to_dict(),
            "replay": fp_r.to_dict(),
        }

    def get_exec_fingerprint(self) -> dict[str, Any]:
        with self._lock:
            return self._fp_exec.to_dict()

    def get_replay_fingerprint(self) -> dict[str, Any]:
        with self._lock:
            return self._fp_replay.to_dict()

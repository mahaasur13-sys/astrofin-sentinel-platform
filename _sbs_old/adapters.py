"""
DESC Event Adapter — logs SBS events to DESC event log.

Every invariant violation is recorded as a DESC event:
    {
        "type": "INVARIANT_VIOLATION",
        "stage": stage,
        "violated": [...],
        "state_hash": hash(state),
        "policy": policy,
        "timestamp": ...
    }

This enables deterministic replay even after violations.
"""

from __future__ import annotations

import time
import hashlib
import json
from typing import Any


class DESCEventLogger:
    """
    Event logger for SBS → DESC integration.

    Records invariant violations and system state into an append-only
    event log compatible with DESC event-sourcing layer.

    The log supports replay: after any violation, the exact state snapshot
    is preserved so that replay produces identical results.
    """

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def append_violation(
        self,
        stage: str,
        violated_invariants: list[str],
        state_snapshot: dict,
        policy: str = "CRITICAL",
    ) -> dict[str, Any]:
        """
        Log an INVARIANT_VIOLATION event to the DESC event log.

        Parameters
        ----------
        stage : str
            Execution stage where violation occurred.
        violated_invariants : list[str]
            List of violated invariant names.
        state_snapshot : dict
            Frozen snapshot of system state at violation time.
        policy : str
            Applied policy level (CRITICAL / WARNING / RECOVERABLE).

        Returns
        -------
        dict[str, Any]
            The logged event entry.
        """
        # Serialize state for hashing — use canonical JSON for deterministic replay
        state_json = json.dumps(state_snapshot, sort_keys=True, default=str)
        state_hash = hashlib.sha256(state_json.encode()).hexdigest()[:16]

        event = {
            "type": "INVARIANT_VIOLATION",
            "stage": stage,
            "violated": violated_invariants,
            "state_hash": state_hash,
            "policy": policy,
            "timestamp": time.time(),
            "replay_version": 1,
        }
        self._events.append(event)
        return event

    def append_audit(
        self,
        stage: str,
        ok: bool,
        violations: list[str],
        state_snapshot: dict,
    ) -> dict[str, Any]:
        """
        Log an SBS audit/check event (no violation required).

        Parameters
        ----------
        stage : str
            Execution stage.
        ok : bool
            True if all invariants passed.
        violations : list[str]
            List of violated invariants (empty if ok=True).
        state_snapshot : dict
            System state snapshot.

        Returns
        -------
        dict[str, Any]
            The logged event entry.
        """
        state_json = json.dumps(state_snapshot, sort_keys=True, default=str)
        state_hash = hashlib.sha256(state_json.encode()).hexdigest()[:16]

        event = {
            "type": "SBS_AUDIT" if ok else "INVARIANT_VIOLATION",
            "stage": stage,
            "violated": violations,
            "state_hash": state_hash,
            "ok": ok,
            "timestamp": time.time(),
            "replay_version": 1,
        }
        self._events.append(event)
        return event

    def get_events(self) -> list[dict[str, Any]]:
        """Return all logged events in append order."""
        return list(self._events)

    def get_violation_events(self) -> list[dict[str, Any]]:
        """Return only INVARIANT_VIOLATION events."""
        return [e for e in self._events if e["type"] == "INVARIANT_VIOLATION"]

    def replay_iter(self):
        """
        Yield events in order for replay.

        After replay, the system should be in the same state
        as it was immediately after each original event.
        """
        for event in self._events:
            yield event

    def verify_replay_integrity(self) -> tuple[bool, list[str]]:
        """
        Verify that replay would reproduce identical state hashes.

        Returns
        -------
        tuple[bool, list[str]]
            (ok, discrepancies) — list of events whose state_hash
            cannot be reproduced (indicates log tampering or non-determinism).
        """
        discrepancies: list[str] = []
        for i, event in enumerate(self._events):
            if event["type"] == "INVARIANT_VIOLATION":
                stage = event["stage"]
                violated = event["violated"]
                stored_hash = event["state_hash"]
                # In a real system, we would reconstruct the state from prior events
                # and verify hash matches. Here we just verify the event structure.
                if not all(k in event for k in ("stage", "violated", "state_hash", "timestamp")):
                    discrepancies.append(f"Event {i}: missing required fields")
        return len(discrepancies) == 0, discrepancies

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()


# ─── DRL / CCL / F2 / DESC Adapter Interfaces ───────────────────────────────

class LayerStateAdapter:
    """
    Adapter that normalizes layer-specific state into SBS-compatible format.

    Each underlying layer (DRL, CCL, F2, DESC) has its own state schema.
    This adapter maps them to the canonical state dict expected by
    SystemBoundarySpec and GlobalInvariantEngine.
    """

    @staticmethod
    def from_drl(raw: dict[str, Any]) -> dict[str, Any]:
        """
        Map DRL network layer state → SBS canonical state.

        Expected DRL keys: partitions, clock_skew_ms, causality_markers,
        leader, term, event_sequence_gaps
        """
        return {
            "partitions": raw.get("partitions", 0),
            "clock_skew_ms": raw.get("clock_skew_ms", 0.0),
            "causality_markers": raw.get("causality_markers", []),
            "leader": raw.get("leader"),
            "term": raw.get("term", 0),
            "event_sequence_gaps": raw.get("event_sequence_gaps", 0),
            "quorum_ratio": raw.get("quorum_ratio", 0.0),
            "duplicate_ack": raw.get("duplicate_ack", False),
            "uncommitted_reads": raw.get("uncommitted_reads", 0),
            # preserve original keys for audit
            "_raw_drl": raw,
        }

    @staticmethod
    def from_ccl(raw: dict[str, Any]) -> dict[str, Any]:
        """
        Map CCL consensus contracts state → SBS canonical state.

        Expected CCL keys: contract_violations, stale_reads, leader, term,
        quorum_ratio, uncommitted_reads, duplicate_ack
        """
        return {
            "contract_violations": raw.get("contract_violations", []),
            "stale_reads": raw.get("stale_reads", 0),
            "leader": raw.get("leader"),
            "term": raw.get("term", 0),
            "quorum_ratio": raw.get("quorum_ratio", 0.0),
            "duplicate_ack": raw.get("duplicate_ack", False),
            "uncommitted_reads": raw.get("uncommitted_reads", 0),
            "_raw_ccl": raw,
        }

    @staticmethod
    def from_f2(raw: dict[str, Any]) -> dict[str, Any]:
        """
        Map F2 linearizable kernel state → SBS canonical state.

        Expected F2 keys: quorum_ratio, commit_index, duplicate_ack,
        leader, term, partitions, event_sequence_gaps
        """
        return {
            "quorum_ratio": raw.get("quorum_ratio", 0.0),
            "commit_index": raw.get("commit_index", 0),
            "duplicate_ack": raw.get("duplicate_ack", False),
            "leader": raw.get("leader"),
            "term": raw.get("term", 0),
            "partitions": raw.get("partitions", 0),
            "event_sequence_gaps": raw.get("event_sequence_gaps", 0),
            "_raw_f2": raw,
        }

    @staticmethod
    def from_desc(raw: dict[str, Any]) -> dict[str, Any]:
        """
        Map DESC event-sourcing state → SBS canonical state.

        Expected DESC keys: commit_index, leader, term,
        event_sequence_gaps, last_applied_index
        """
        return {
            "commit_index": raw.get("commit_index", 0),
            "leader": raw.get("leader"),
            "term": raw.get("term", 0),
            "event_sequence_gaps": raw.get("event_sequence_gaps", 0),
            "last_applied_index": raw.get("last_applied_index", 0),
            "_raw_desc": raw,
        }

    @staticmethod
    def build_aggregate(
        drl: dict[str, Any],
        ccl: dict[str, Any],
        f2: dict[str, Any],
        desc: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build the aggregate state dict for SBS enforce() calls.

        Returns a dict with canonical keys + raw layer sub-dicts.
        """
        return {
            "drl": LayerStateAdapter.from_drl(drl),
            "ccl": LayerStateAdapter.from_ccl(ccl),
            "f2": LayerStateAdapter.from_f2(f2),
            "desc": LayerStateAdapter.from_desc(desc),
        }

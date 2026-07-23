"""PolicySync — applies remote theta through local replay validation (H-4).

CRITICAL INVARIANT: no remote θ is applied without local replay validation.
This is the distributed extension of v8.2b's safety invariant.

Workflow:
  remote_vector arrives (via GossipProtocol)
    → ConsensusResolver resolves consensus
    → PolicySync.fetch_remote_theta(remote_node_id)
    → ReplayValidator.run(reconstructed_theta)
    → if PASS: apply via MutationExecutor
    → if FAIL: reject + log + notify
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from federation.consensus_resolver import ConsensusResult
from federation.state_vector import StateVector


class SyncOutcome(Enum):
    APPLIED = "applied"
    REJECTED = "rejected"
    PENDING = "pending"
    STALE = "stale"
    QUARANTINED = "quarantined"


@dataclass
class SyncRecord:
    timestamp_ns: int
    remote_node_id: str
    remote_theta_hash: str
    outcome: SyncOutcome
    confidence: float
    replay_valid: bool
    latency_ms: float | None = None


@dataclass
class QuarantineEntry:
    node_id: str
    reason: str
    quarantined_at_ns: int
    retry_after_ns: int | None = None


class PolicySync:
    """Applies remote θ only after local ReplayValidator approval."""

    def __init__(
        self,
        node_id: str,
        replay_validator: Callable[[dict], tuple[bool, str]],
        apply_fn: Callable[[dict], bool] | None = None,
        quarantine_fn: Callable[[str, str], None] | None = None,
        quarantine_duration_ms: int = 60_000,
    ):
        self.node_id = node_id
        self._validate = replay_validator       # (theta) → (valid, reason)
        self._apply = apply_fn                  # (theta) → success
        self._quarantine_cb = quarantine_fn     # (node_id, reason) → None
        self._quarantine_dur_ms = quarantine_duration_ms
        self._quarantine: dict[str, QuarantineEntry] = {}
        self._history: list[SyncRecord] = []
        self._max_history = 500
        self._pending: dict[str, str] = {}     # theta_hash → remote_node_id

    # ------------------------------------------------------------------ #
    # public API                                                          #
    # ------------------------------------------------------------------ #

    def sync_from_consensus(
        self,
        consensus: ConsensusResult,
        remote_vector: StateVector,
        reconstruct_theta: Callable[[str], dict | None],
    ) -> SyncRecord:
        """Main entry point: apply remote theta if consensus says to."""
        t0 = time.time_ns()

        # Check quarantine
        if self._is_quarantined(remote_vector.node_id):
            record = SyncRecord(
                timestamp_ns=t0,
                remote_node_id=remote_vector.node_id,
                remote_theta_hash=consensus.theta_hash,
                outcome=SyncOutcome.QUARANTINED,
                confidence=consensus.confidence,
                replay_valid=False,
                latency_ms=None,
            )
            self._add_record(record)
            return record

        # H-4: reconstruct theta from remote
        theta = reconstruct_theta(consensus.theta_hash)
        if theta is None:
            record = SyncRecord(
                timestamp_ns=t0,
                remote_node_id=remote_vector.node_id,
                remote_theta_hash=consensus.theta_hash,
                outcome=SyncOutcome.REJECTED,
                confidence=consensus.confidence,
                replay_valid=False,
                latency_ms=(time.time_ns() - t0) / 1_000_000,
            )
            self._add_record(record)
            return record

        # H-4 CRITICAL: local replay validation
        valid, reason = self._validate(theta)
        if not valid:
            self._quarantine_node(remote_vector.node_id, f"replay_failed: {reason}")
            record = SyncRecord(
                timestamp_ns=t0,
                remote_node_id=remote_vector.node_id,
                remote_theta_hash=consensus.theta_hash,
                outcome=SyncOutcome.REJECTED,
                confidence=consensus.confidence,
                replay_valid=False,
                latency_ms=(time.time_ns() - t0) / 1_000_000,
            )
            self._add_record(record)
            return record

        # Apply via MutationExecutor
        applied = self._apply(theta) if self._apply else False
        outcome = SyncOutcome.APPLIED if applied else SyncOutcome.REJECTED

        record = SyncRecord(
            timestamp_ns=t0,
            remote_node_id=remote_vector.node_id,
            remote_theta_hash=consensus.theta_hash,
            outcome=outcome,
            confidence=consensus.confidence,
            replay_valid=True,
            latency_ms=(time.time_ns() - t0) / 1_000_000,
        )
        self._add_record(record)
        return record

    def sync_to_peers(
        self,
        my_theta: dict,
        gossip,
    ) -> list[tuple[str, SyncOutcome]]:
        """Push local theta to peers via gossip, track pending."""
        import hashlib
        import json
        theta_hash = hashlib.sha256(
            json.dumps(my_theta, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]

        self._pending[theta_hash] = self.node_id
        push_results = gossip.push(
            StateVector(
                node_id=self.node_id,
                theta_hash=theta_hash,
                envelope_state="stable",
                drift_score=0.0,
                stability_score=1.0,
                timestamp_ns=time.time_ns(),
            )
        )
        return [(pid, SyncOutcome.PENDING) for pid, _ in push_results]

    # ------------------------------------------------------------------ #
    # quarantine management                                               #
    # ------------------------------------------------------------------ #

    def _is_quarantined(self, node_id: str) -> bool:
        entry = self._quarantine.get(node_id)
        if entry is None:
            return False
        if entry.retry_after_ns and time.time_ns() < entry.retry_after_ns:
            return True
        # expired
        self._quarantine.pop(node_id, None)
        return False

    def _quarantine_node(self, node_id: str, reason: str) -> None:
        retry_ns = time.time_ns() + (self._quarantine_dur_ms * 1_000_000)
        self._quarantine[node_id] = QuarantineEntry(
            node_id=node_id,
            reason=reason,
            quarantined_at_ns=time.time_ns(),
            retry_after_ns=retry_ns,
        )
        if self._quarantine_cb:
            self._quarantine_cb(node_id, reason)

    # ------------------------------------------------------------------ #
    # history / stats                                                     #
    # ------------------------------------------------------------------ #

    def _add_record(self, record: SyncRecord) -> None:
        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history.pop(0)

    @property
    def recent_outcomes(self) -> list[SyncOutcome]:
        return [r.outcome for r in self._history[-50:]]

    def apply_rate(self, window: int = 100) -> float:
        """Fraction of sync attempts that succeeded (applied)."""
        recent = self._history[-window:]
        if not recent:
            return 0.0
        return sum(1 for r in recent if r.outcome == SyncOutcome.APPLIED) / len(recent)

    def quarantine_count(self) -> int:
        return len(self._quarantine)

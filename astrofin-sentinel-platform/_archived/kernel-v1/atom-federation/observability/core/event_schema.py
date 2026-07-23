"""
Event Schema v7.0 — Structured event model for failure replay.

Each event captures:
  - ts: nanosecond timestamp (time.time_ns())
  - node_id: originating node
  - event_type: event category
  - payload: typed fields (event-specific)
  - coherence_state: snapshot of coherence subsystem
  - lattice_snapshot: snapshot of routing state

Event log is the SOURCE OF TRUTH for deterministic replay.
All other observability (metrics, logs) are derived from events.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(Enum):
    # ── Node lifecycle ─────────────────────────────────────────────────────────
    NODE_START = "node.start"
    NODE_READY = "node.ready"
    NODE_HEARTBEAT = "node.heartbeat"
    NODE_SUSPECT = "node.suspect"          # node marked as suspect
    NODE_DOWN = "node.down"                 # node confirmed down
    NODE_RECOVERY = "node.recovery"        # node recovered

    # ── SBS ─────────────────────────────────────────────────────────────────
    SBS_CHECK_START = "sbs.check.start"
    SBS_CHECK_COMPLETE = "sbs.check.complete"
    SBS_VIOLATION = "sbs.violation"
    SBS_INVARIANT_REGISTERED = "sbs.invariant.registered"
    SBS_INVARIANT_DEREGISTERED = "sbs.invariant.deregistered"

    # ── Coherence ─────────────────────────────────────────────────────────────
    COHERENCE_CHECK_START = "coherence.check.start"
    COHERENCE_CHECK_COMPLETE = "coherence.check.complete"
    COHERENCE_DRIFT_DETECTED = "coherence.drift.detected"
    COHERENCE_DRIFT_RESOLVED = "coherence.drift.resolved"

    # ── Lattice ────────────────────────────────────────────────────────────────
    LATTICE_DECISION = "lattice.decision"
    LATTICE_ROUTE_UPDATE = "lattice.route.update"
    LATTICE_FAILOVER = "lattice.failover"
    LATTICE_SPLIT_BRAIN_DETECTED = "lattice.split_brain.detected"
    LATTICE_SPLIT_BRAIN_RESOLVED = "lattice.split_brain.resolved"

    # ── Healer ────────────────────────────────────────────────────────────────
    HEALER_REPAIR_START = "healer.repair.start"
    HEALER_REPAIR_COMPLETE = "healer.repair.complete"
    HEALER_REPAIR_FAILED = "healer.repair.failed"
    HEALER_QUEUE_ADD = "healer.queue.add"
    HEALER_QUEUE_DRAIN = "healer.queue.drain"

    # ── Quorum ────────────────────────────────────────────────────────────────
    QUORUM_VOTE_REQUEST = "quorum.vote.request"
    QUORUM_VOTE_GRANTED = "quorum.vote.granted"
    QUORUM_VOTE_DENIED = "quorum.vote.denied"
    QUORUM_LOST = "quorum.lost"
    QUORUM_RECOVERED = "quorum.recovered"
    QUORUM_MEMBER_ADD = "quorum.member.add"
    QUORUM_MEMBER_REMOVE = "quorum.member.remove"

    # ── RPC ───────────────────────────────────────────────────────────────────
    RPC_REQUEST_SEND = "rpc.request.send"
    RPC_REQUEST_RECV = "rpc.request.recv"
    RPC_RESPONSE_SEND = "rpc.response.send"
    RPC_RESPONSE_RECV = "rpc.response.recv"
    RPC_ERROR = "rpc.error"
    RPC_TIMEOUT = "rpc.timeout"
    RPC_DROP = "rpc.drop"

    # ── Cluster ───────────────────────────────────────────────────────────────
    CLUSTER_FORMING = "cluster.forming"
    CLUSTER_STABLE = "cluster.stable"
    CLUSTER_DEGRADED = "cluster.degraded"
    CLUSTER_PARTITIONED = "cluster.partitioned"

    # ── Replay ─────────────────────────────────────────────────────────────────
    REPLAY_EVENT_APPLIED = "replay.event.applied"   # emitted by ReplayEngine during replay


@dataclass
class CoherenceStateSnapshot:
    """Snapshot of the coherence subsystem state at event time."""
    drift_score: float = 0.0
    self_model_errors: int = 0
    assertions_passed: int = 0
    assertions_failed: int = 0
    last_check_ts: float = 0.0


@dataclass
class LatticeSnapshot:
    """Snapshot of the lattice routing state at event time."""
    active_nodes: set[str] = field(default_factory=set)
    routes: dict[str, str] = field(default_factory=dict)  # dest -> next_hop
    pending_failovers: int = 0
    split_brain_detected: bool = False


@dataclass
class QuorumSnapshot:
    """Snapshot of quorum state at event time."""
    members: set[str] = field(default_factory=set)
    voting_members: set[str] = field(default_factory=set)
    quorum_health: float = 1.0
    term: int = 0
    leader: str | None = None


@dataclass
class SBSStateSnapshot:
    """Snapshot of SBS subsystem state at event time."""
    active_invariants: int = 0
    violations_in_window: int = 0
    last_check_ts: float = 0.0


@dataclass
class Event:
    """
    Canonical event record for ATOMFederationOS.

    ts: nanosecond Unix timestamp
    node_id: originating node identifier
    event_type: EventType enum value (string form)
    payload: event-specific typed fields
    coherence_state: snapshot of coherence subsystem
    lattice_snapshot: snapshot of routing state
    quorum_snapshot: snapshot of quorum state
    sbs_state: snapshot of SBS subsystem
    event_id: globally unique event identifier (uuid4 hex)
    correlation_id: groups related events (e.g., RPC request/response)
    causation_id: the event that directly caused this one
    version: schema version for compatibility
    """
    ts: int                      # nanoseconds since epoch
    node_id: str
    event_type: str              # EventType.value
    payload: dict[str, Any] = field(default_factory=dict)
    coherence_state: CoherenceStateSnapshot | None = None
    lattice_snapshot: LatticeSnapshot | None = None
    quorum_snapshot: QuorumSnapshot | None = None
    sbs_state: SBSStateSnapshot | None = None
    event_id: str = ""           # uuid4 hex
    correlation_id: str | None = None  # groups related events (e.g., RPC request/response)
    causation_id: str | None = None     # the event that directly caused this one
    version: str = "7.0"

    def to_dict(self) -> dict:
        return {
            "ts": self.ts,
            "node_id": self.node_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "coherence_state": _dataclass_to_dict(self.coherence_state),
            "lattice_snapshot": _dataclass_to_dict(self.lattice_snapshot),
            "quorum_snapshot": _dataclass_to_dict(self.quorum_snapshot),
            "sbs_state": _dataclass_to_dict(self.sbs_state),
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Event:
        cs = d.get("coherence_state")
        ls = d.get("lattice_snapshot")
        qs = d.get("quorum_snapshot")
        ss = d.get("sbs_state")
        return cls(
            ts=d["ts"],
            node_id=d["node_id"],
            event_type=d["event_type"],
            payload=d.get("payload", {}),
            coherence_state=CoherenceStateSnapshot(**cs) if cs else None,
            lattice_snapshot=LatticeSnapshot(**ls) if ls else None,
            quorum_snapshot=QuorumSnapshot(**qs) if qs else None,
            sbs_state=SBSStateSnapshot(**ss) if ss else None,
            event_id=d.get("event_id", ""),
            correlation_id=d.get("correlation_id"),
            causation_id=d.get("causation_id"),
            version=d.get("version", "7.0"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=False)

    @classmethod
    def from_json(cls, s: str) -> Event:
        return cls.from_dict(json.loads(s))


def _dataclass_to_dict(obj: Any) -> dict | None:
    if obj is None:
        return None
    if hasattr(obj, "__dataclass_fields__"):
        return {
            f: getattr(obj, f)
            for f in obj.__dataclass_fields__
        }
    return None


# ── Payload schemas per event type (documentation + validation) ───────────────

PAYLOAD_SCHEMAS: dict[str, list[str]] = {
    EventType.SBS_VIOLATION.value: ["invariant_name", "severity", "node_id"],
    EventType.COHERENCE_DRIFT_DETECTED.value: ["drift_score", "expected", "actual"],
    EventType.LATTICE_DECISION.value: ["decision_type", "target_node", "reason"],
    EventType.LATTICE_FAILOVER.value: ["from_node", "to_node", "reason"],
    EventType.HEALER_REPAIR_START.value: ["repair_type", "target_node", "repair_id"],
    EventType.HEALER_REPAIR_COMPLETE.value: ["repair_id", "repair_type", "duration_ms"],
    EventType.QUORUM_VOTE_REQUEST.value: ["candidate_id", "term", "log_pos"],
    EventType.RPC_ERROR.value: ["peer_id", "method", "error_code", "error_msg"],
    EventType.RPC_TIMEOUT.value: ["peer_id", "method", "timeout_ms"],
    EventType.REPLAY_EVENT_APPLIED.value: ["event_id", "lag_ms", "speed"],
}


def validate_payload(event_type: str, payload: dict) -> list[str]:
    """Validate that payload has required fields for event type."""
    required = PAYLOAD_SCHEMAS.get(event_type, [])
    errors = []
    for field in required:
        if field not in payload:
            errors.append(f"Missing payload field '{field}' for event {event_type}")
    return errors

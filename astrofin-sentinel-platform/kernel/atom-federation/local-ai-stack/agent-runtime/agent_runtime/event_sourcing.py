"""
Event Sourcing — v6 core layer.

Design principles:
- Append-only event log (Redis Streams)
- Every state transition is an immutable fact
- Replay is deterministic: same inputs → same outputs
- Global causal ordering via Lamport timestamps
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class EventType(Enum):
    TASK_CREATED      = "TASK_CREATED"
    TASK_CLAIMED      = "TASK_CLAIMED"
    STEP_EXECUTED     = "STEP_EXECUTED"
    STEP_FAILED       = "STEP_FAILED"
    TASK_RETRIED      = "TASK_RETRIED"
    TASK_FAILED       = "TASK_FAILED"
    TASK_COMPLETED    = "TASK_COMPLETED"
    TASK_CANCELLED    = "TASK_CANCELLED"
    IDEMPOTENCY_SET   = "IDEMPOTENCY_SET"
    EPOCH_CHANGED     = "EPOCH_CHANGED"


@dataclass
class TaskEvent:
    """
    Immutable event record.

    Fields:
      event_id    — unique identifier (UUID)
      task_id     — task this event belongs to
      epoch       — task epoch at time of event (for ordering)
      event_type  — EventType enum value
      lamport_ts  — Lamport timestamp (global causal order)
      worker_id   — who triggered this event
      step_id     — optional: step this event refers to
      payload     — event-specific data
      timestamp   — wall-clock time
    """
    event_id:   str
    task_id:    str
    epoch:      int
    event_type: EventType
    lamport_ts: int
    worker_id:  str
    step_id:    str | None = None
    payload:    dict = field(default_factory=dict)
    timestamp:  float = field(default_factory=time.time)

    def to_stream_fields(self) -> dict[str, str]:
        return {
            "event_id":   self.event_id,
            "task_id":    self.task_id,
            "epoch":      str(self.epoch),
            "event_type": self.event_type.value,
            "lamport_ts": str(self.lamport_ts),
            "worker_id":  self.worker_id,
            "step_id":    self.step_id or "",
            "payload":    __import__("json").dumps(self.payload),
            "timestamp":  str(self.timestamp),
        }

    @classmethod
    def from_stream_fields(cls, fields: dict[str, str]) -> TaskEvent:
        import json
        return cls(
            event_id=fields["event_id"],
            task_id=fields["task_id"],
            epoch=int(fields["epoch"]),
            event_type=EventType(fields["event_type"]),
            lamport_ts=int(fields["lamport_ts"]),
            worker_id=fields["worker_id"],
            step_id=fields.get("step_id") or None,
            payload=json.loads(fields.get("payload", "{}")),
            timestamp=float(fields.get("timestamp", "0")),
        )

    @classmethod
    def make(
        cls,
        task_id: str,
        event_type: EventType,
        worker_id: str,
        epoch: int,
        lamport_ts: int,
        step_id: str | None = None,
        payload: dict | None = None,
    ) -> TaskEvent:
        return cls(
            event_id=str(uuid.uuid4()),
            task_id=task_id,
            epoch=epoch,
            event_type=event_type,
            lamport_ts=lamport_ts,
            worker_id=worker_id,
            step_id=step_id,
            payload=payload or {},
        )

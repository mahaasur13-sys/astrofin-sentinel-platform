#!/usr/bin/env python3
"""ACOS Event — immutable record written to EventLog."""
from __future__ import annotations
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from acos.events.types import EventType


@dataclass(frozen=True)
class Event:
    """
    Immutable event record.

    prev_hash is set by EventLog.append() at append time (not at construction).
    This is CRITICAL for hash chain integrity (INV4).

    payload is stored as tuple(sorted(dict.items())) for:
    - hashable serialization in hash()
    - deterministic ordering (sorted keys)
    - immutability (tuple is immutable)
    """
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    trace_id: str = ""
    event_type: EventType = None
    timestamp: float = field(default_factory=time.time)
    payload: tuple = field(default_factory=dict)
    actor: str = "engine"
    prev_hash: str = field(default="0" * 64, repr=False)
    event_hash: str = ""

    def __post_init__(self):
        if isinstance(self.payload, dict):
            object.__setattr__(self, 'payload', tuple(sorted(self.payload.items())))
        if self.event_type is None:
            object.__setattr__(self, 'event_type', EventType.DAG_CREATED)
        if not self.event_hash:
            object.__setattr__(self, 'event_hash', self._compute_hash())

    def _compute_hash(self) -> str:
        et_val = self.event_type.value if hasattr(self.event_type, 'value') else str(self.event_type)
        data = (
            f"{self.event_id}"
            f"{self.trace_id}"
            f"{et_val}"
            f"{self.timestamp}"
            f"{json.dumps(dict(self.payload), sort_keys=True)}"
            f"{self.actor}"
            f"{self.prev_hash}"
        )
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for storage. Does NOT include prev_hash (set at append)."""
        d = asdict(self)
        d["event_type"] = self.event_type.value
        d["payload"] = dict(self.payload)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Event:
        """Deserialize from dict. Handles both dict and tuple payloads."""
        d = dict(d)
        if "event_type" in d:
            et = d.pop("event_type")
            d["event_type"] = EventType(et) if isinstance(et, str) else et
        if "payload" in d and isinstance(d["payload"], dict):
            d["payload"] = tuple(sorted(d["payload"].items()))
        return cls(**d)

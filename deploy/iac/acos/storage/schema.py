#!/usr/bin/env python3
"""
ACOS SCL v6 — TraceRecord (normalized storage schema).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


def _utcnow() -> datetime:
    return datetime.utcnow()


@dataclass
class TraceRecord:
    """
    Normalized trace record for persistent storage.
    All fields are simple types (str, dict, datetime).
    """

    trace_id: str
    metadata: dict
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self):
        # INV9 fix: default_factory only fires when NOT explicitly provided.
        # If user passes created_at=None, we override to factory.
        if self.created_at is None:
            object.__setattr__(self, "created_at", _utcnow())

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "created_at": (
                self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at)
            ),
        }

    @classmethod
    def from_dict(cls, d: dict) -> TraceRecord:
        ca = d.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca.replace("Z", "+00:00"))
        return cls(trace_id=d["trace_id"], metadata=d.get("metadata", {}), created_at=ca or datetime.utcnow())

"""Trace record DTOs (refactor §3.1: split by responsibility).

Pure data — no clock, no I/O, no random. Determinism moved to
`DeterministicTraceStore` in `impl.py`.

Backward compat: `from AsurDev.acos.storage.schema import TraceRecord`
still works via `schema.py` re-export shim.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from common.deterministic import utc_now_deterministic


@dataclass
class TraceRecord:
    """Normalized trace record for persistent storage.

    All fields are simple types (str, dict, datetime).
    `created_at` is optional and may be supplied externally for
    deterministic replay — if omitted or None, the storage layer's
    `DeterministicClock` will fill it in.
    """

    trace_id: str
    metadata: dict[str, Any]
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        # INV9 fix: default_factory only fires when NOT explicitly provided.
        # If caller passes created_at=None, we override to deterministic clock.
        if self.created_at is None:
            self.created_at = utc_now_deterministic()
        elif isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))

    def to_dict(self) -> dict[str, Any]:
        ca = self.created_at
        return {
            "trace_id": self.trace_id,
            "metadata": self.metadata,
            "created_at": ca.isoformat() if isinstance(ca, datetime) else (str(ca) if ca else None),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TraceRecord:
        ca_raw = d.get("created_at")
        ca: datetime | None = None
        if isinstance(ca_raw, str):
            ca = datetime.fromisoformat(ca_raw.replace("Z", "+00:00"))
        elif isinstance(ca_raw, datetime):
            ca = ca_raw
        return cls(
            trace_id=d["trace_id"],
            metadata=d.get("metadata", {}),
            created_at=ca,
        )

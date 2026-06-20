"""Shared data contracts (DTOs + storage protocols).

Originally `AsurDev/acos/storage/types.py` and `protocol.py` from S1.
Extracted to `acos-contracts` in S2 so all repos can depend on the
same data shape without importing each other.

Backward compat: `AsurDev.acos.storage.schema` still re-exports
`TraceRecord` from this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from .deterministic import utc_now_deterministic


@dataclass
class TraceRecord:
    """Normalized trace record for persistent storage.

    `created_at` is optional and may be supplied externally for
    deterministic replay — if omitted or None, the storage layer's
    `DeterministicClock` will fill it in.
    """

    trace_id: str
    metadata: dict[str, Any]
    created_at: datetime | None = None

    def __post_init__(self) -> None:
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
    def from_dict(cls, d: dict[str, Any]) -> "TraceRecord":
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


@runtime_checkable
class TraceStoreProtocol(Protocol):
    """Storage interface for TraceRecord. Implementations: SQL, file, in-memory."""

    def write(self, record: TraceRecord) -> None: ...
    def read(self, trace_id: str) -> TraceRecord | None: ...
    def list(self, limit: int | None = None) -> list[TraceRecord]: ...
    def clear(self) -> None: ...


__all__ = ["TraceRecord", "TraceStoreProtocol"]

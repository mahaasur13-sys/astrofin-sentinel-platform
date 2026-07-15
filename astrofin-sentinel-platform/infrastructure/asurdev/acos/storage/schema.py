"""Backward-compat re-export shim for the old `schema.TraceRecord` API.

All implementation moved to:
- `types.py`      — `TraceRecord` dataclass (DTO)
- `protocol.py`   — `TraceStoreProtocol`
- `impl.py`       — `DeterministicTraceStore`

Existing code keeps working:
    from AsurDev.acos.storage.schema import TraceRecord  # noqa: F401
"""
from __future__ import annotations

from .types import TraceRecord

__all__ = ["TraceRecord"]  # preserve old public surface verbatim

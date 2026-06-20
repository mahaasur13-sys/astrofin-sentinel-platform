"""DEPRECATED compatibility shim — use ``acos_contracts.deterministic``.

All determinism primitives previously defined here (clock, RNG,
context, UUID derivation, contextvars helpers, entropy source) have
been moved to the standalone ``acos_contracts`` package (v0.1.0+).
This module re-exports them for callers that still import from
``common.deterministic`` during the migration window and will be
removed in a future release.
"""
from __future__ import annotations

from acos_contracts.deterministic import (
    DeterministicClockImpl,
    DeterministicContext,
    DeterministicRNG,
    deterministic_uuid,
    require_entropy_source,
    reset_current_context,
    set_current_context,
    utc_now_deterministic,
    uuid4_deterministic,
)

__all__ = [
    "DeterministicClockImpl",
    "DeterministicContext",
    "DeterministicRNG",
    "deterministic_uuid",
    "require_entropy_source",
    "reset_current_context",
    "set_current_context",
    "utc_now_deterministic",
    "uuid4_deterministic",
]

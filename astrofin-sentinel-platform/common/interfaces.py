"""DEPRECATED compatibility shim — use ``acos_contracts.interfaces``.

All Protocol symbols previously defined here have been moved to the
standalone ``acos_contracts`` package (v0.1.0+). This module re-exports
them for callers that still import from ``common.interfaces`` during
the migration window and will be removed in a future release.
"""

from __future__ import annotations

from acos_contracts.interfaces import (
    AgentResponseProtocol,
    BaseAgentProtocol,
    DeterministicClock,
    EphemerisProtocol,
    SignalDirectionProtocol,
)

__all__ = [
    "AgentResponseProtocol",
    "BaseAgentProtocol",
    "DeterministicClock",
    "EphemerisProtocol",
    "SignalDirectionProtocol",
]

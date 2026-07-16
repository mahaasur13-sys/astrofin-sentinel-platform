"""astrofin.common — DEPRECATED compatibility shim.

This package was the historical internal source of truth for cross-module
abstractions. It now re-exports symbols from the standalone
`acos_contracts` package (v0.1.0+). Domain code MUST import from
`acos_contracts` directly; this module exists only to keep a few legacy
import paths (`from common.interfaces import AgentResponseProtocol`,
etc.) working during the migration window.

Importing this package must remain cheap and side-effect-free so it can be
pulled from any layer without creating cycles.
"""

from __future__ import annotations

from acos_contracts import (
    contracts,
    deterministic,
    interfaces,
)

__all__ = [
    "interfaces",
    "contracts",
    "deterministic",
]

"""astrofin.common — shared contracts for AstroFin Sentinel V5.

This package is the **single internal source of truth** for cross-module
abstractions (protocols, deterministic primitives, DTOs). It MUST NOT import
from any domain package (agents/, core/, acos/, trading/, etc.) — only from
the standard library and `typing`.

Importing this package must remain cheap and side-effect-free so it can be
pulled from any layer (including domain code) without creating cycles.
"""
from __future__ import annotations

__all__ = [
    "interfaces",
    "deterministic",
    "contracts",
]

"""Deterministic ID-factory contract.

Lifts the `DeterministicUUIDFactory` interface from
`atom-federation-os/core/deterministic.py` so callers outside the
atom-federation-os repo can compose content-addressed IDs without
importing it directly. The `make_id` / `make_trace_id` / `make_context_id` /
`make_entry_id` / `make_nonce` shape is preserved.

This is a **stateless Protocol** — concrete impls (in atom-federation-os
or anywhere else) must keep the same SHA-256 derivation and the same
`prefix_hex12` output format so IDs stay stable across repos.

See ADR-0002 for the full rationale.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DeterministicUUIDFactoryProtocol(Protocol):
    """Stateless content-addressed ID factory.

    All methods are `@staticmethod` on the concrete impl, but the protocol
    only constrains the *call shape*. The derived format
    `f"{prefix}_{sha256[:12]}"` MUST be preserved by every implementation.
    """

    @staticmethod
    def make_id(prefix: str, content: str, salt: str = ...) -> str: ...

    @staticmethod
    def make_trace_id(trace_content: str, tick: int) -> str: ...

    @staticmethod
    def make_context_id(agent_id: str, tick: int, depth: int) -> str: ...

    @staticmethod
    def make_entry_id(operation: str, tick: int, seq: int) -> str: ...

    @staticmethod
    def make_nonce(request_id: str, tick: int, seq: int) -> str: ...


# Legacy alias.
DeterministicUUIDFactory = DeterministicUUIDFactoryProtocol  # type: ignore[misc, assignment]


__all__ = ["DeterministicUUIDFactoryProtocol"]

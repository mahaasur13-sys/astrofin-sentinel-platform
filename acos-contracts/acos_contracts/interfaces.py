"""Protocols for God Nodes (refactor §3.2).

These protocols decouple consumers from the concrete implementations in
`core/`, `agents/`, and `AsurDev/acos/`. Domain code depends on these
*protocols*, not on the god classes directly — that breaks the
`AgentResponse → everything` fan-out seen in the Graphify audit.

Design rules:
  * No imports from domain packages (agents/, core/, acos/).
  * `@runtime_checkable` so `isinstance(obj, AgentResponseProtocol)` works
    for legacy duck-typed call sites.
  * Methods are minimal — only what 80% of call sites need. Specialised
    behaviour stays on the concrete class.
  * Signatures match the legacy concrete classes so existing code keeps
    compiling without modification.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AgentResponseProtocol(Protocol):
    """Minimal contract for an agent's response.

    Mirrors the public surface of `core.base_agent.AgentResponse` so that
    *either* the legacy class *or* a Protocol-conforming substitute can be
    passed through the orchestrator / synthesis layer.
    """

    agent_name: str
    signal: str
    confidence: int
    reasoning: str
    sources: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class SignalDirectionProtocol(Protocol):
    """Direction enum-like protocol.

    The concrete class is an `enum.Enum`; we expose only the comparison /
    string conversion surface that downstream code actually uses.
    """

    name: str
    value: str

    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...


@runtime_checkable
class BaseAgentProtocol(Protocol):
    """Minimal surface that SynthesisAgent and the orchestrator depend on.

    Domain code should be able to substitute any implementation as long as
    it exposes `name`, `weight`, and an `async run(state) -> response`
    method.
    """

    name: str
    weight: float

    async def run(self, state: dict[str, Any]) -> AgentResponseProtocol: ...


@runtime_checkable
class DeterministicClock(Protocol):
    """Abstract time source — `datetime.utcnow()` / `time.time()` wrapper.

    Production wiring injects `DeterministicClockImpl.frozen(...)`; tests
    inject a manually advanced clock. Domain code never imports
    `datetime.utcnow` directly.
    """

    def now(self) -> datetime: ...  # noqa: F821 — forward ref to datetime
    def monotonic_ns(self) -> int: ...
    def isoformat(self) -> str: ...


@runtime_checkable
class EphemerisProtocol(Protocol):
    """Provider-agnostic abstraction over Swiss Ephemeris.

    Concrete impls: `SwissEphemerisProvider` (production, swisseph-backed),
    `SimpleEphemerisProvider` (fallback, deterministic toy model used
    when swisseph is not installed). Domain code must depend on this
    protocol — not on the concrete module — so the dependency on
    `core.ephemeris` does not become a god-node fan-out.
    """

    def is_available(self) -> bool: ...

    def julian_day(self, dt: datetime) -> float: ...

    def calculate_planet(
        self,
        name: str,
        jd: float,
        flags: int = 1,
    ) -> Any: ...

    def calculate_houses(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        hsys: str = "P",
    ) -> Any: ...

    def get_planetary_positions(
        self,
        dt: datetime,
        latitude: float = 53.2,
        longitude: float = 50.1,
        sidereal: bool = False,
    ) -> dict[str, Any]: ...

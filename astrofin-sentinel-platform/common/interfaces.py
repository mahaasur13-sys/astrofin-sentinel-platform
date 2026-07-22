"""
Local Protocol stubs (formerly acos_contracts.interfaces).
Self-contained — no external package dependency.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable
from datetime import datetime


@runtime_checkable
class SignalDirectionProtocol(Protocol):
    """Protocol for signal direction enum."""
    @property
    def value(self) -> str: ...


@runtime_checkable
class AgentResponseProtocol(Protocol):
    """Protocol for agent response dataclass."""
    agent_id: str
    signal: str
    confidence: float
    reasoning: str
    sources: list[str]
    metadata: dict

    def to_dict(self) -> dict: ...


@runtime_checkable
class BaseAgentProtocol(Protocol):
    """Protocol for base agent class."""
    agent_id: str
    agent_name: str

    async def analyze(self, state: dict) -> AgentResponseProtocol: ...
    def run_sync(self, state: dict) -> AgentResponseProtocol: ...


@runtime_checkable
class DeterministicClock(Protocol):
    """Protocol for deterministic clock."""
    def utc_now(self) -> datetime: ...


@runtime_checkable
class EphemerisProtocol(Protocol):
    """Protocol for ephemeris computation."""
    def get_positions(self, dt: datetime) -> dict: ...
    def get_aspects(self, positions: dict) -> list[dict]: ...


__all__ = [
    "AgentResponseProtocol",
    "BaseAgentProtocol",
    "DeterministicClock",
    "EphemerisProtocol",
    "SignalDirectionProtocol",
]

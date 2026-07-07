"""Event taxonomy and execution-result DTOs.

Cross-repo Surprising Connection:
  * `home-cluster-iac/acos/events/types.py` already has an `EventType(str, Enum)`
    that matches the shape used by `AsurDev/acos/recorder/recorder.py`.
  * `home-cluster-iac/acos/contracts/trace_contract.py` defines `ExecutionResult`
    and `Decision` that are referenced by both `home-cluster-iac` and `AsurDev`.

This module is the *single* definition. Existing local copies will be replaced
by `from acos_contracts import EventType, ExecutionResult, Decision` during
the AsurDev / home-cluster-iac migrations in Etapах 3 и 4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class EventType(str, Enum):
    """Unified event-type taxonomy used by AsurDev, home-cluster-iac, and
    roma-execution-bridge.

    Mirrors `home-cluster-iac/acos/events/types.py:EventType` so existing
    string comparisons (`event.event_type == "DAG_CREATED"`) keep working.
    Only the *canonical* categories are listed here — repos are free to
    subclass this enum locally if they need extra categories, but cross-repo
    producers MUST use the names below.
    """

    # DAG lifecycle
    DAG_CREATED = "DAG_CREATED"
    DAG_VALIDATED = "DAG_VALIDATED"
    DAG_INVALID = "DAG_INVALID"
    DAG_REJECTED = "DAG_REJECTED"

    # Governance
    GOVERNANCE_APPROVED = "GOVERNANCE_APPROVED"
    GOVERNANCE_REJECTED = "GOVERNANCE_REJECTED"
    POLICY_EVALUATED = "POLICY_EVALUATED"

    # Node lifecycle
    NODE_SCHEDULED = "NODE_SCHEDULED"
    NODE_EXECUTED = "NODE_EXECUTED"
    NODE_FAILED = "NODE_FAILED"
    NODE_START = "node_start"
    NODE_END = "node_end"

    # Trace lifecycle
    TRACE_RECORDED = "TRACE_RECORDED"
    STATE_RECONSTRUCTED = "STATE_RECONSTRUCTED"
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"
    SCHEDULER_TIMEOUT = "SCHEDULER_TIMEOUT"
    REPLAY_INCONSISTENT = "REPLAY_INCONSISTENT"

    # Tunnel events (AmneziaWG)
    TUNNEL_UP = "TUNNEL_UP"
    TUNNEL_DOWN = "TUNNEL_DOWN"
    TUNNEL_FAILOVER = "TUNNEL_FAILOVER"
    TUNNEL_HEALTH_CHECK = "TUNNEL_HEALTH_CHECK"
    TUNNEL_CONFIG_ERROR = "TUNNEL_CONFIG_ERROR"


class Decision(str, Enum):
    """Decision enum shared by trace-recorder contract.

    Mirrors `home-cluster-iac/acos/contracts/trace_contract.py:Decision`.
    """

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REJECTED_CONSTRAINT = "REJECTED_CONSTRAINT"
    REJECTED_RISK = "REJECTED_RISK"
    ERROR = "ERROR"


@dataclass
class ExecutionResult:
    """Result of a single ACOS execution.

    Mirrors `home-cluster-iac/acos/contracts/trace_contract.py:ExecutionResult`.
    All fields are optional except `trace_id` and `decision`; downstream
    consumers must tolerate missing `schedule` / `final_state` etc.
    """

    trace_id: str
    decision: Decision
    dag: dict[str, Any]
    schedule: dict[str, Any] | None = None
    execution_trace: list[dict[str, Any]] = field(default_factory=list)
    final_state: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    governance_checks: dict[str, Any] = field(default_factory=dict)
    l9_injections: dict[str, Any] = field(default_factory=dict)
    l11_verification: dict[str, Any] | None = None
    dag_hash: str | None = None
    node_results: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ExecutionResultProtocol(Protocol):
    """Structural contract for `ExecutionResult`-like DTOs.

    Use this when the concrete type may be a stripped-down mock or a
    freshly-instantiated dataclass. Static checkers will accept any
    object that has the listed attributes.
    """

    trace_id: str
    decision: Any
    dag: dict[str, Any]


@runtime_checkable
class EventTypeProtocol(Protocol):
    """Duck-typed contract for `EventType`-like values.

    Repos that subclass `EventType` (e.g. to add local categories) still
    satisfy this protocol as long as they expose `.value` and equality on
    raw strings.
    """

    value: str

    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...


__all__ = [
    "Decision",
    "EventType",
    "EventTypeProtocol",
    "ExecutionResult",
    "ExecutionResultProtocol",
]

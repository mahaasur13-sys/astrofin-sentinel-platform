"""acos-contracts — shared protocols, DTOs, and determinism primitives.

This package is the single cross-repo dependency surface for the
AstroFin Sentinel ecosystem (astrofin-sentinel-platform, AsurDev,
home-cluster-iac, roma-execution-bridge).

Public API:
- Interfaces:   AgentResponseProtocol, BaseAgentProtocol, EphemerisProtocol, ...
- Contracts:    TraceRecord, TraceStoreProtocol
- Determinism:  utc_now_deterministic, DeterministicContext, DeterministicClockImpl,
                DeterministicRNG, deterministic_uuid, require_entropy_source
- Events:       EventType, Decision, ExecutionResult, ExecutionResultProtocol,
                EventTypeProtocol
- State:        StateStoreProtocol, JobStateProtocol, JobStatus
- Feature pipe: WindowEngineProtocol, SlidingWindowProtocol
- Trading:      RiskEngineProtocol, RiskConfigProtocol, StrategyEvaluatorProtocol,
                MarketStateProtocol
- IDs:          DeterministicUUIDFactoryProtocol
- Errors:       ACOSContractsError, EphemerisUnavailableError

Versioning: SemVer; see pyproject.toml. Backward-compat aliases
(`DeterministicUUIDFactory`, `WindowEngine`, `StateStore`,
`MarketState`, `RiskConfigV2`, `RiskEngineV2`, `StrategyEvaluator`)
match the legacy class names from S1.
"""
from __future__ import annotations

from .contracts import TraceRecord, TraceStoreProtocol
from .deterministic import (
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
from .deterministic_factory import DeterministicUUIDFactoryProtocol
from .errors import ACOSContractsError, EphemerisUnavailableError
from .events import (
    Decision,
    EventType,
    EventTypeProtocol,
    ExecutionResult,
    ExecutionResultProtocol,
)
from .feature_pipeline import (
    SlidingWindowProtocol,
    WindowEngineProtocol,
)
from .interfaces import (
    AgentResponseProtocol,
    BaseAgentProtocol,
    DeterministicClock,
    EphemerisProtocol,
    SignalDirectionProtocol,
)
from .state import (
    JobStateProtocol,
    JobStatus,
    StateStoreProtocol,
)
from .trading import (
    MarketStateProtocol,
    RiskConfigProtocol,
    RiskEngineProtocol,
    StrategyEvaluatorProtocol,
)

__version__ = "0.1.0"

__all__ = [
    # Contracts
    "TraceRecord",
    "TraceStoreProtocol",
    # Determinism
    "DeterministicClockImpl",
    "DeterministicContext",
    "DeterministicRNG",
    "deterministic_uuid",
    "require_entropy_source",
    "set_current_context",
    "reset_current_context",
    "utc_now_deterministic",
    "uuid4_deterministic",
    # Interfaces (Protocols)
    "AgentResponseProtocol",
    "BaseAgentProtocol",
    "DeterministicClock",
    "EphemerisProtocol",
    "SignalDirectionProtocol",
    # Events
    "Decision",
    "EventType",
    "EventTypeProtocol",
    "ExecutionResult",
    "ExecutionResultProtocol",
    # State
    "JobStateProtocol",
    "JobStatus",
    "StateStoreProtocol",
    # Feature pipeline
    "SlidingWindowProtocol",
    "WindowEngineProtocol",
    # Trading
    "MarketStateProtocol",
    "RiskConfigProtocol",
    "RiskEngineProtocol",
    "StrategyEvaluatorProtocol",
    # IDs
    "DeterministicUUIDFactoryProtocol",
    # Errors
    "ACOSContractsError",
    "EphemerisUnavailableError",
]

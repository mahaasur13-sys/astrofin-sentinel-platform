"""Trading-domain protocols: risk engine, strategy evaluator, market state.

The God-Node list (top-10 from the Graphify audit) is closed by these
protocols:

  * `RiskEngineV2`        → `RiskEngineProtocol`
  * `RiskConfigV2`        → `RiskConfigProtocol`
  * `StrategyEvaluator`   → `StrategyEvaluatorProtocol`
  * `MarketState`         → `MarketStateProtocol`

Domain code (orchestrators, dashboards, tests) should depend on these
*protocols* rather than on the concrete classes in `trading/risk_v2.py` and
`agents/_impl/amre/trajectory.py`. That breaks the "everything → concrete
class" fan-out the Graphify audit flagged as the main coupling source.

See ADR-0002 for the full rationale.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


# ── Risk config ────────────────────────────────────────────────────────────


@runtime_checkable
class RiskConfigProtocol(Protocol):
    """Surface of `trading/risk_v2.py:RiskConfigV2` (dataclass)."""

    max_drawdown: float
    max_exposure_per_asset: float
    correlation_limit: float
    target_volatility: float
    vol_lookback: int
    kill_switch_enabled: bool
    close_on_kill: bool


# ── Risk engine ────────────────────────────────────────────────────────────


@runtime_checkable
class RiskEngineProtocol(Protocol):
    """Surface of `trading/risk_v2.py:RiskEngineV2`."""

    config: RiskConfigProtocol

    def update_position(self, pos: Any) -> None: ...

    def update_equity(self, equity: float) -> None: ...

    def get_state(self) -> Any: ...

    def check_signal(self, signal: Any, market_state: Any) -> tuple[bool, str]: ...


# ── Strategy evaluator ─────────────────────────────────────────────────────


@runtime_checkable
class StrategyEvaluatorProtocol(Protocol):
    """Surface of `strategies/base.py:BaseStrategy`.

    Strategy implementations may be sync or async; the protocol accepts
    both. Return shape is intentionally `Any` to allow the rich
    `StrategyResult` dataclass to flow through.
    """

    config: Any
    is_enabled: bool

    def evaluate(self, market_data: dict[str, Any]) -> Any: ...

    def record_performance(self, record: Any) -> None: ...

    def enable(self) -> None: ...

    def disable(self) -> None: ...


# ── Market state ───────────────────────────────────────────────────────────


@runtime_checkable
class MarketStateProtocol(Protocol):
    """Surface of `agents/_impl/amre/trajectory.py:MarketState` (dataclass)."""

    symbol: str
    price: float
    timeframe: str
    n_signals: int
    session_id: str
    timestamp: str
    regime: str


__all__ = [
    "MarketStateProtocol",
    "RiskConfigProtocol",
    "RiskEngineProtocol",
    "StrategyEvaluatorProtocol",
]


# Legacy aliases.
MarketState = MarketStateProtocol             # type: ignore[misc, assignment]
RiskConfigV2 = RiskConfigProtocol             # type: ignore[misc, assignment]
RiskEngineV2 = RiskEngineProtocol             # type: ignore[misc, assignment]
StrategyEvaluator = StrategyEvaluatorProtocol  # type: ignore[misc, assignment]

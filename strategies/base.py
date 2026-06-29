"""strategies/base.py — ATOM-STEP-11: Strategy Base Classes"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class Signal(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class Regime(Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    NEUTRAL_R = "NEUTRAL"
    VOLATILE = "VOLATILE"


@dataclass
class StrategyConfig:
    name: str
    description: str
    version: str = "1.0.0"
    enabled: bool = True
    min_confidence: float = 50.0
    max_position_pct: float = 25.0
    params: dict = field(default_factory=dict)


@dataclass
class StrategyResult:
    signal: Signal
    confidence: float
    reasoning: str
    regime: Regime = Regime.NEUTRAL_R
    metadata: dict = field(default_factory=dict)

    @property
    def is_actionable(self) -> bool:
        return self.confidence >= 50.0 and self.signal != Signal.NEUTRAL


@dataclass
class PerformanceRecord:
    strategy_name: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    timestamp: float


class BaseStrategy:
    def __init__(self, config: StrategyConfig):
        self.config = config
        self._performance: list[PerformanceRecord] = []
        self._enabled = config.enabled

    def evaluate(self, market_data: dict) -> StrategyResult:
        raise NotImplementedError

    def record_performance(self, record: PerformanceRecord):
        self._performance.append(record)

    def avg_performance(self) -> PerformanceRecord | None:
        if not self._performance:
            return None
        records = self._performance
        return PerformanceRecord(
            strategy_name=self.config.name,
            total_return=np.mean([r.total_return for r in records]),
            sharpe_ratio=np.mean([r.sharpe_ratio for r in records]),
            max_drawdown=np.mean([r.max_drawdown for r in records]),
            win_rate=np.mean([r.win_rate for r in records]),
            trade_count=int(np.mean([r.trade_count for r in records])),
            timestamp=records[-1].timestamp,
        )

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def update_params(self, params: dict):
        self.config.params.update(params)


__all__ = [
    "Signal",
    "Regime",
    "StrategyConfig",
    "StrategyResult",
    "PerformanceRecord",
    "BaseStrategy",
]

"""meta_rl/distributed/types.py -- ATOM-META-RL-024: Worker task types"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StrategyTask:
    strategy_id: str
    config: dict
    symbol: str
    timeframe: str
    priority: int = 0


@dataclass
class WorkerResult:
    strategy_id: str
    fitness: float
    metrics: dict
    error: str | None = None

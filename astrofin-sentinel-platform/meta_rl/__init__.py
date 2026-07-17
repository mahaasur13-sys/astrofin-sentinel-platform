"""meta_rl — AstroFin Meta-RL Strategy Discovery Engine (ATOM-META-RL-013)"""

from __future__ import annotations

from meta_rl.backtest_adapter import BacktestEngineAdapter
from meta_rl.evolution import EvolutionEngine, EvolutionStats
from meta_rl.git_agent_exporter import (
    GIT_EXPORT_ENABLED,
    ExportResult,
    export_strategy,
    load_strategy,
)
from meta_rl.meta_agent import EvolutionConfig, MetaAgent
from meta_rl.reward import RewardCalculator, RewardConfig
from meta_rl.strategy_evaluator import StrategyEvaluator
from meta_rl.strategy_pool import ScoredStrategy, StrategyPool
from meta_rl.types import EvaluationResult

__all__ = [
    "EvaluationResult",
    "ScoredStrategy",
    "StrategyEvaluator",
    "RewardCalculator",
    "RewardConfig",
    "StrategyPool",
    "MetaAgent",
    "EvolutionConfig",
    "EvolutionEngine",
    "EvolutionStats",
    "BacktestEngineAdapter",
    "GIT_EXPORT_ENABLED",
    "export_strategy",
    "load_strategy",
    "ExportResult",
]

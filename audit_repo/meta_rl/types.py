"""Типы данных для meta_rl."""

from dataclasses import dataclass, field


@dataclass
class EvaluationResult:
    """Результат оценки стратегии."""

    win_rate: float = 0.0
    max_drawdown: float = 0.0
    avg_confidence: float = 0.0
    total_return_pct: float = 0.0
    score: float = 0.0
    pnl: float = 0.0
    risk_adjusted_pnl: float = 0.0
    sharpe: float = 0.0
    trades: int = 0
    equity_curve: list[float] = field(default_factory=list)
    execution_cost: float = 0.0
    risk_adjustment_reason: str = ""
    adjusted_drawdown: float = 0.0
    metadata: dict | None = None

    @classmethod
    def fail(cls) -> "EvaluationResult":
        """Возвращает экземпляр с нулевыми метриками."""
        return cls()


@dataclass
class BasketMetrics:
    """Метрики корзины стратегий."""

    win_rate: float = 0.0
    max_drawdown: float = 0.0
    avg_confidence: float = 0.0
    total_return_pct: float = 0.0
    num_strategies: int = 1


@dataclass
class ScoredStrategy:
    """Стратегия с оценкой (используется в эволюции и пулах)."""

    strategy_id: str = ""
    agent_name: str = ""
    fitness: float = 0.0
    generation: int = 0
    config: dict = field(default_factory=dict)
    metrics: EvaluationResult | None = None
    metadata: dict | None = None

    def to_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "agent_name": self.agent_name,
            "fitness": self.fitness,
            "generation": self.generation,
            "config": self.config,
            "metrics": self.metrics.__dict__ if self.metrics else None,
            "metadata": self.metadata,
        }

"""Типы данных для meta_rl."""

from dataclasses import dataclass, field, asdict
from typing import Any


def _to_jsonable(value: Any) -> Any:
    """Преобразует значение в JSON-сериализуемое (np.ndarray → list, и т.п.)."""
    if value is None:
        return None
    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except Exception:
            pass
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


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
    equity_curve: list = field(default_factory=list)
    execution_cost: float = 0.0
    risk_adjustment_reason: str = ""
    adjusted_drawdown: float = 0.0
    metadata: dict | None = None

    @classmethod
    def fail(cls) -> "EvaluationResult":
        """Возвращает экземпляр с явным drawdown=1.0 (худший случай)."""
        return cls(max_drawdown=1.0, win_rate=0.0, sharpe=0.0, pnl=0.0, trades=0)

    def to_dict(self) -> dict:
        """Сериализация в dict (np.array → list, и т.п.)."""
        data = asdict(self)
        data["equity_curve"] = _to_jsonable(self.equity_curve)
        if data.get("metadata") is not None:
            data["metadata"] = _to_jsonable(self.metadata)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationResult":
        """Обратная сериализация."""
        if data is None:
            return cls.fail()
        clean = dict(data)
        ec = clean.get("equity_curve", [])
        clean["equity_curve"] = _to_jsonable(ec) if ec is not None else []
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


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
            "config": _to_jsonable(self.config),
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "metadata": _to_jsonable(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScoredStrategy":
        if data is None:
            return cls()
        m = data.get("metrics")
        return cls(
            strategy_id=data.get("strategy_id", ""),
            agent_name=data.get("agent_name", ""),
            fitness=float(data.get("fitness", 0.0)),
            generation=int(data.get("generation", 0)),
            config=data.get("config") or {},
            metrics=EvaluationResult.from_dict(m) if m else None,
            metadata=data.get("metadata"),
        )

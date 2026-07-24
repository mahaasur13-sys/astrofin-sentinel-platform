"""Типы данных для meta_rl."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


def _safe_float(value: float | int | None) -> float | None:
    """
    Safely convert a numeric value to float, replacing NaN/Inf with None.

    ATOM-META-RL-004: Used by EvaluationResult.to_dict() to ensure that
    serialised metrics are always JSON-safe (no NaN, no Inf).
    """
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


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
    adjusted_drawdown: Optional[float] = None
    metadata: dict | None = None

    def __post_init__(self) -> None:
        """
        Normalise equity_curve on construction.

        - If a numpy ndarray is provided, convert it to a plain list[float].
        - Replace NaN and Inf entries with None to keep the result
          JSON-serialisable downstream (ATOM-META-RL-004).
        """
        if isinstance(self.equity_curve, np.ndarray):
            self.equity_curve = self.equity_curve.tolist()
        if self.equity_curve is not None:
            cleaned: list[Optional[float]] = []
            for x in self.equity_curve:
                cleaned.append(_safe_float(x))
            self.equity_curve = cleaned

    @classmethod
    def fail(cls) -> "EvaluationResult":
        """
        Sentinel result used when an evaluation cannot be produced.

        Values are deliberately pessimistic so that downstream code (notably
        RewardCalculator) treats a failed result as the worst-case input:

        - max_drawdown = 1.0       (100 % drawdown)
        - adjusted_drawdown = 1.0  (100 % risk-adjusted drawdown)
        - risk_adjusted_pnl = -1.0 (total loss of risk-adjusted capital)
        """
        return cls(
            max_drawdown=1.0,
            adjusted_drawdown=1.0,
            risk_adjusted_pnl=-1.0,
        )

    def to_dict(self) -> dict:
        """
        Serialise to a JSON-safe dict.

        All numeric fields are passed through `_safe_float`, which maps
        NaN/Inf to None. ``equity_curve`` is stored as a list of
        ``float | None`` to keep it serialisable.
        """
        return {
            "win_rate": _safe_float(self.win_rate),
            "max_drawdown": _safe_float(self.max_drawdown),
            "avg_confidence": _safe_float(self.avg_confidence),
            "total_return_pct": _safe_float(self.total_return_pct),
            "score": _safe_float(self.score),
            "pnl": _safe_float(self.pnl),
            "risk_adjusted_pnl": _safe_float(self.risk_adjusted_pnl),
            "sharpe": _safe_float(self.sharpe),
            "trades": int(self.trades),
            "equity_curve": [_safe_float(x) for x in (self.equity_curve or [])],
            "execution_cost": _safe_float(self.execution_cost),
            "risk_adjustment_reason": self.risk_adjustment_reason,
            "adjusted_drawdown": _safe_float(self.adjusted_drawdown),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EvaluationResult":
        """
        Reconstruct an EvaluationResult from a dict produced by ``to_dict``.

        ``None`` values for ``float`` fields are preserved as ``None`` (not
        coerced to ``0.0``) so that downstream consumers can distinguish
        "missing / not computed" from "genuine zero".
        """
        if not isinstance(d, dict):
            return cls.fail()

        ec = d.get("equity_curve", []) or []
        if isinstance(ec, np.ndarray):
            ec = ec.tolist()
        ec_clean: list[Optional[float]] = []
        for x in ec:
            if x is None:
                ec_clean.append(None)
            else:
                ec_clean.append(_safe_float(x))

        return cls(
            win_rate=_safe_float(d.get("win_rate", 0.0)) or 0.0,
            max_drawdown=_safe_float(d.get("max_drawdown", 0.0)) or 0.0,
            avg_confidence=_safe_float(d.get("avg_confidence", 0.0)) or 0.0,
            total_return_pct=_safe_float(d.get("total_return_pct", 0.0)) or 0.0,
            score=_safe_float(d.get("score", 0.0)) or 0.0,
            pnl=_safe_float(d.get("pnl", 0.0)) or 0.0,
            risk_adjusted_pnl=_safe_float(d.get("risk_adjusted_pnl", 0.0)) or 0.0,
            sharpe=_safe_float(d.get("sharpe", 0.0)) or 0.0,
            trades=int(d.get("trades", 0) or 0),
            equity_curve=ec_clean,
            execution_cost=_safe_float(d.get("execution_cost", 0.0)) or 0.0,
            risk_adjustment_reason=d.get("risk_adjustment_reason", "") or "",
            adjusted_drawdown=_safe_float(d.get("adjusted_drawdown")),
            metadata=d.get("metadata"),
        )


@dataclass
class SymbolMetrics:
    """Метрики одной стратегии/символа внутри корзины (basket + MAS)."""

    symbol: str = ""
    pnl: float = 0.0
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    trades: int = 0
    win_rate: float = 0.0
    exposure_pct: float = 0.0
    evaluation: Optional["EvaluationResult"] = None
    metadata: dict | None = None


@dataclass
class BasketMetrics:
    """Агрегированные метрики корзины стратегий/символов."""

    symbols: list[str] = field(default_factory=list)
    symbol_metrics: dict[str, SymbolMetrics] = field(default_factory=dict)
    portfolio_pnl: float = 0.0
    portfolio_sharpe: float = 0.0
    portfolio_max_drawdown: float = 0.0
    correlation_penalty: float = 0.0
    diversification_bonus: float = 0.0
    active_symbols: int = 0
    portfolio_equity_curve: list[float] = field(default_factory=list)
    metadata: dict | None = None

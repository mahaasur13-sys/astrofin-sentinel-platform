"""
agents._impl.types — Unified types for AstroFin Sentinel v5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Signal(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

    @property
    def score(self) -> float:
        """Map signal to numeric score for weighted calculation."""
        scores = {
            "STRONG_BUY": 100,
            "BUY": 75,
            "NEUTRAL": 50,
            "HOLD": 50,
            "SELL": 25,
            "STRONG_SELL": 0,
        }
        return scores.get(self.value, 50)


@dataclass
class TradingSignal:
    """Final trading signal from weighted agent responses."""

    signal: str
    confidence: float
    symbol: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_agents(
        cls,
        symbol: str,
        responses: list[Any],
        entry_price: float = 0.0,
        weights: dict[str, float] | None = None,
    ) -> "TradingSignal":
        weights = weights or {}
        scores = {"LONG": 1.0, "SHORT": -1.0, "NEUTRAL": 0.0, "BUY": 1.0, "SELL": -1.0}
        weighted_score = 0.0
        total_weight = 0.0
        confidences: list[float] = []
        for response in responses:
            name = getattr(response, "agent_name", "")
            raw_signal = getattr(response, "signal", "NEUTRAL")
            signal = getattr(raw_signal, "value", raw_signal)
            direction = str(signal).upper()
            weight = float(weights.get(name, 0.0))
            if weight <= 0:
                continue
            weighted_score += scores.get(direction, 0.0) * weight
            total_weight += weight
            confidences.append(float(getattr(response, "confidence", 0.0)))

        normalized = weighted_score / total_weight if total_weight else 0.0
        if normalized >= 0.25:
            signal = "LONG"
        elif normalized <= -0.25:
            signal = "SHORT"
        else:
            signal = "NEUTRAL"
        agreement = abs(normalized)
        confidence = (sum(confidences) / len(confidences) if confidences else 30.0) * max(agreement, 0.5)
        return cls(
            signal=signal,
            confidence=round(max(0.0, min(100.0, confidence)), 2),
            symbol=symbol,
            metadata={"entry_price": entry_price, "weighted_score": weighted_score, "total_weight": total_weight},
        )

    @property
    def summary(self) -> str:
        return f"{self.signal} signal for {self.symbol} ({self.confidence:.0f}% confidence)"

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "confidence": self.confidence,
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "summary": self.summary,
        }

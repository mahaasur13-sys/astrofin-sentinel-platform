"""Unified signal types for AstroFin Sentinel v5."""

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
        return {
            "STRONG_BUY": 100,
            "BUY": 75,
            "NEUTRAL": 50,
            "HOLD": 50,
            "SELL": 25,
            "STRONG_SELL": 0,
        }.get(self.value, 50)


@dataclass
class TradingSignal:
    """Final trading signal from weighted agent responses."""

    signal: str
    confidence: float
    symbol: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def summary(self) -> str:
        return f"{self.signal} signal for {self.symbol} ({self.confidence:.0f}% confidence)"

    @classmethod
    def from_agents(
        cls,
        symbol: str,
        responses: list[Any],
        entry_price: float = 0.0,
        weights: dict[str, float] | None = None,
        astro_weights: dict[str, float] | None = None,
    ) -> "TradingSignal":
        """Build a percentage-confidence signal from weighted responses."""
        all_weights: dict[str, float] = {}
        all_weights.update(weights or {})
        all_weights.update(astro_weights or {})
        long_signals = {"LONG", "BUY", "STRONG_BUY", "BULL", "BULLISH"}
        short_signals = {"SHORT", "SELL", "STRONG_SELL", "BEAR", "BEARISH"}
        bullish = 0.0
        bearish = 0.0
        total_weight = 0.0

        for response in responses:
            name = getattr(response, "agent_name", "unknown")
            raw_signal = getattr(response, "signal", "NEUTRAL")
            direction = str(getattr(raw_signal, "value", raw_signal)).upper()
            raw_confidence = float(getattr(response, "confidence", 50.0) or 50.0)
            confidence = raw_confidence / 100.0 if raw_confidence > 1.0 else raw_confidence
            weight = float(all_weights.get(name, 0.10))
            if weight <= 0:
                continue
            total_weight += weight
            if direction in long_signals:
                bullish += weight * confidence
            elif direction in short_signals:
                bearish += weight * confidence

        if total_weight == 0:
            return cls(signal="NEUTRAL", confidence=50.0, symbol=symbol)

        net = (bullish - bearish) / total_weight
        confidence = min(100.0, ((bullish + bearish) / total_weight) * 100.0)
        if net > 0.15:
            signal = "LONG"
        elif net < -0.15:
            signal = "SHORT"
        else:
            signal = "NEUTRAL"

        return cls(
            signal=signal,
            confidence=round(confidence, 2),
            symbol=symbol,
            metadata={
                "entry_price": entry_price,
                "agent_count": len(responses),
                "weighted_score": net,
                "total_weight": total_weight,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "confidence": self.confidence,
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "summary": self.summary,
        }

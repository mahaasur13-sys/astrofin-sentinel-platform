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

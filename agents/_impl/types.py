"""
agents._impl.types — Unified types for AstroFin Sentinel v5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# Score map covers both Signal (STRONG_BUY/BUY/NEUTRAL/HOLD/SELL/STRONG_SELL)
# and SignalDirection (LONG/SHORT/NEUTRAL/AVOID) so sub-agent directions
# (LONG/SHORT) map to directional scores instead of defaulting to NEUTRAL=50.
_SIGNAL_SCORES = {
    "STRONG_BUY": 100.0,
    "BUY": 75.0,
    "LONG": 75.0,
    "NEUTRAL": 50.0,
    "HOLD": 50.0,
    "AVOID": 50.0,
    "SELL": 25.0,
    "SHORT": 25.0,
    "STRONG_SELL": 0.0,
}


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
        return _SIGNAL_SCORES.get(self.value, 50.0)


@dataclass
class TradingSignal:
    """Final trading signal from weighted agent responses."""

    signal: str
    confidence: float
    symbol: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    entry_price: float = 0.0

    @classmethod
    def from_agents(
        cls,
        symbol: str,
        responses: list[Any],
        entry_price: float = 0.0,
        weights: dict[str, float] | None = None,
    ) -> "TradingSignal":
        """Weighted aggregation of sub-agent responses.

        Each response contributes ``weights[agent_name] * signal_score``, where
        ``signal_score`` maps STRONG_BUY=100 … STRONG_SELL=0 (NEUTRAL/HOLD=50).
        Returns a NEUTRAL signal if no response carries weight.
        """
        weights = weights or {}
        total = 0.0
        score = 0.0
        parts: list[str] = []

        for r in responses:
            agent_name = getattr(r, "agent_name", "unknown")
            w = weights.get(agent_name, 0.0)
            if w == 0:
                continue
            raw = getattr(r, "signal", "NEUTRAL")
            sig_val = raw.value if hasattr(raw, "value") else str(raw)
            sig_score = _SIGNAL_SCORES.get(sig_val, 50.0)
            score += w * sig_score
            total += w
            parts.append(f"{agent_name}: {sig_val}")

        if total == 0:
            return cls(
                signal="NEUTRAL",
                confidence=50.0,
                symbol=symbol,
                entry_price=entry_price,
                summary="No weighted signals",
                metadata={"weights": weights, "responses": len(responses)},
            )

        avg = score / total
        if avg >= 70:
            final = "BUY"
        elif avg <= 30:
            final = "SELL"
        else:
            final = "NEUTRAL"

        return cls(
            signal=final,
            confidence=round(max(0.0, min(100.0, avg)), 1),
            symbol=symbol,
            entry_price=entry_price,
            summary=" | ".join(parts),
            metadata={"weights": weights, "responses": len(responses)},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "confidence": self.confidence,
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "summary": self.summary,
            "entry_price": self.entry_price,
        }

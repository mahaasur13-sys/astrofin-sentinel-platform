"""core/council/types.py — AstroCouncil data types"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from agents._impl.synthesis.weights import CATEGORY_WEIGHTS as _CATEGORY_WEIGHTS


class Signal(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


@dataclass
class CouncilMember:
    name: str
    domain: str  # fundamental | quant | macro | technical | sentiment | astro
    vote: Signal
    confidence: float  # 0-100
    reasoning: str
    weight: float  # policy weight (sum to 1.0)
    aligned: bool = False  # astro-aligned indicator

    @property
    def signal(self) -> Signal:
        return self.vote  # alias


@dataclass
class CouncilResult:
    timestamp: datetime
    symbol: str
    weighted_signal: float  # -1.0 to +1.0
    final_signal: Signal
    confidence: float  # 0-100
    consensus: float  # 0.0-1.0 (agreement fraction)
    members: list[CouncilMember]
    deliberation: str  # council reasoning log
    conflict_resolved: bool
    dissent: list[dict]  # dissenting opinions


# ── Agent registry ──────────────────────────────────────────────────────────
AGENT_WEIGHTS = {
    "fundamental": _CATEGORY_WEIGHTS["fundamental"],
    "quant": _CATEGORY_WEIGHTS["quant"],
    "macro": _CATEGORY_WEIGHTS["macro"],
    "technical": _CATEGORY_WEIGHTS["technical"],
    "sentiment": _CATEGORY_WEIGHTS["sentiment"],
    "optionsflow": _CATEGORY_WEIGHTS["options"],
    "astro": _CATEGORY_WEIGHTS["astro"],
}

AGENT_DESCRIPTIONS = {
    "fundamental": "Value investing, earnings, revenue, P/E ratios",
    "quant": "Statistical arbitrage, ML predictions, backtested signals",
    "macro": "Fed policy, VIX, DXY, geopolitical risk",
    "technical": "RSI, MACD, support/resistance, chart patterns",
    "sentiment": "News, social media, fear & greed index",
    "optionsflow": "Unusual options activity, gamma exposure",
    "astro": "Planetary aspects, Muhurta timing, Bradley model",
}

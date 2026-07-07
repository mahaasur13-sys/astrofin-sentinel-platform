"""
Insider Agent — insider trading and 13F filings analysis.
"""

from __future__ import annotations

import logging

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class InsiderAgent(BaseAgent[AgentResponse]):
    """
    InsiderAgent — анализ инсайдерских сделок и 13F-файлингов.

    Responsibilities:
    1. Track insider buying/selling (Form 4)
    2. Analyze 13F institutional holdings changes
    3. Detect unusual insider activity
    4. Cross-reference with price action

    Weight: 8% (part of 20% Fundamental+Macro block)
    """

    def __init__(self):
        super().__init__(
            name="InsiderAgent",
            instructions_path="agents/InsiderAgent_instructions.md",
            domain="fundamental",
            weight=0.08,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        state.get("current_price", 50000)

        # Fetch insider data (requires paid API for real data)
        insider_data = await self._fetch_insider_data(symbol)
        filings_data = await self._fetch_13f_data(symbol)

        # Analyze insider sentiment
        insider_analysis = self._analyze_insider_trades(insider_data)
        filings_analysis = self._analyze_filings(filings_data)

        # Combine signals
        signals = []
        scores = []

        if insider_analysis["signal"] == "bullish":
            signals.append(SignalDirection.LONG)
            scores.append(0.70)
        elif insider_analysis["signal"] == "bearish":
            signals.append(SignalDirection.SHORT)
            scores.append(0.70)
        else:
            signals.append(SignalDirection.NEUTRAL)
            scores.append(0.50)

        if filings_analysis["signal"] == "bullish":
            signals.append(SignalDirection.LONG)
            scores.append(0.60)
        elif filings_analysis["signal"] == "bearish":
            signals.append(SignalDirection.SHORT)
            scores.append(0.60)
        else:
            signals.append(SignalDirection.NEUTRAL)
            scores.append(0.50)

        long_count = signals.count(SignalDirection.LONG)
        short_count = signals.count(SignalDirection.SHORT)

        if long_count > short_count:
            direction = SignalDirection.LONG
        elif short_count > long_count:
            direction = SignalDirection.SHORT
        else:
            direction = SignalDirection.NEUTRAL

        confidence = int(sum(scores) / len(scores) * 100)

        reasoning = f"Insider: {insider_analysis['summary']}. 13F: {filings_analysis['summary']}"

        return AgentResponse(
            agent_name="InsiderAgent",
            signal=direction,
            confidence=confidence,
            reasoning=reasoning,
            sources=["fundamental/insider.md", "fundamental/13f.md"],
            metadata={
                "insider": insider_analysis,
                "filings": filings_analysis,
            },
        )

    @track_agent_metrics
    async def run(self, state: dict) -> AgentResponse:
        """Public entry point. Wraps analyze() with the latency histogram
                and defensive error handling so a single agent can never crash
        the orchestrator."""
        try:
            return await self.analyze(state)
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:  # noqa: BLE001 — last-resort guard
            logger.exception("agent_run_unhandled", extra={"agent": self.name})
            return self._degraded(UNKNOWN, repr(e))

    async def _fetch_insider_data(self, symbol: str) -> dict:
        """
        Fetch insider trading data.
        Note: Real data requires paid API (OpenInsider, Finviz, etc.)
        This is a placeholder.
        """
        return {
            "total_buys": 0,
            "total_sells": 0,
            "recent_trades": [],
        }

    async def _fetch_13f_data(self, symbol: str) -> dict:
        """
        Fetch 13F filings data.
        Note: SEC EDGAR is free but parsing is complex.
        """
        return {
            "institutional_holdings_pct": 0,
            "changes": [],
            "top_holders": [],
        }

    def _analyze_insider_trades(self, data: dict) -> dict:
        """Analyze insider trading activity."""
        buys = data.get("total_buys", 0)
        sells = data.get("total_sells", 0)

        if buys > sells * 2:
            signal = "bullish"
            summary = f"Heavy buying {buys} vs {sells} sells"
        elif sells > buys * 2:
            signal = "bearish"
            summary = f"Heavy selling {sells} vs {buys} buys"
        elif buys > sells:
            signal = "bullish"
            summary = f"More buying {buys} vs {sells} sells"
        elif sells > buys:
            signal = "bearish"
            summary = f"More selling {sells} vs {buys} buys"
        else:
            signal = "neutral"
            summary = "No insider activity"

        return {"signal": signal, "buys": buys, "sells": sells, "summary": summary}

    def _analyze_filings(self, data: dict) -> dict:
        """Analyze 13F institutional holdings."""
        holdings_pct = data.get("institutional_holdings_pct", 0)

        if holdings_pct > 80:
            signal = "bullish"
            summary = f"High institutional ownership {holdings_pct}%"
        elif holdings_pct > 50:
            signal = "neutral"
            summary = f"Moderate ownership {holdings_pct}%"
        elif holdings_pct > 20:
            signal = "neutral"
            summary = f"Low institutional ownership {holdings_pct}%"
        else:
            signal = "bearish"
            summary = f"Very low ownership {holdings_pct}%"

        return {"signal": signal, "holdings_pct": holdings_pct, "summary": summary}


async def run_insider_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = InsiderAgent()
    result = await agent.analyze(state)
    return {"insider_signal": result.to_dict()}


def create() -> InsiderAgent:
    """Factory for 6-fn test contract."""
    return InsiderAgent()

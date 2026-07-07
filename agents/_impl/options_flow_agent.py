"""
Options Flow Agent — options flow analysis, gamma exposure, unusual activity.
"""

from __future__ import annotations

import logging

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class OptionsFlowAgent(BaseAgent[AgentResponse]):
    """
    OptionsFlowAgent — анализ опционных потоков и gamma exposure.

    Responsibilities:
    1. Detect large unusual options trades
    2. Calculate gamma exposure (GEX)
    3. Identify dealer positioning
    4. Spot short squeeze candidates

    Weight: 15%
    """

    def __init__(self):
        super().__init__(
            name="OptionsFlowAgent",
            instructions_path="agents/OptionsFlowAgent_instructions.md",
            domain="options",
            weight=0.15,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        # Fetch options data (requires paid API in production)
        options_data = await self._fetch_options_data(symbol)

        # Analyze gamma exposure
        gex_analysis = self._analyze_gex(options_data, current_price)

        # Analyze unusual activity
        activity_analysis = self._analyze_unusual_activity(options_data)

        # Detect squeeze potential
        squeeze_analysis = self._detect_short_squeeze(options_data)

        # Combine signals
        signals = []
        scores = []

        if gex_analysis["signal"] == "bullish":
            signals.append(SignalDirection.LONG)
            scores.append(0.65)
        elif gex_analysis["signal"] == "bearish":
            signals.append(SignalDirection.SHORT)
        else:
            signals.append(SignalDirection.NEUTRAL)
            scores.append(0.5)

        if activity_analysis["signal"] == "bullish":
            signals.append(SignalDirection.LONG)
            scores.append(0.60)
        elif activity_analysis["signal"] == "bearish":
            signals.append(SignalDirection.SHORT)
            scores.append(0.60)
        else:
            signals.append(SignalDirection.NEUTRAL)
            scores.append(0.5)

        long_count = signals.count(SignalDirection.LONG)
        short_count = signals.count(SignalDirection.SHORT)

        if long_count > short_count:
            direction = SignalDirection.LONG
        elif short_count > long_count:
            direction = SignalDirection.SHORT
        else:
            direction = SignalDirection.NEUTRAL

        confidence = int(sum(scores) / len(scores) * 100)

        reasoning = f"GEX: {gex_analysis['summary']}. Activity: {activity_analysis['summary']}. Squeeze: {squeeze_analysis['probability']}"

        return AgentResponse(
            agent_name="OptionsFlowAgent",
            signal=direction,
            confidence=confidence,
            reasoning=reasoning,
            sources=["options/gex.md", "options/flow.md"],
            metadata={
                "gex": gex_analysis,
                "activity": activity_analysis,
                "squeeze": squeeze_analysis,
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

    async def _fetch_options_data(self, symbol: str) -> dict:
        """
        Fetch options data.
        Note: Real options data requires paid APIs (Tradier, CBOE, etc.)
        This is a placeholder with simulated data.
        """
        # Simulated options data
        return {
            "gex": 0.0,  # Gamma Exposure (positive = dealers long gamma)
            "net_call_volume": 0,
            "net_put_volume": 0,
            "put_call_ratio": 1.0,
            "unusual_activity": [],
        }

    def _analyze_gex(self, data: dict, current_price: float) -> dict:
        """Analyze gamma exposure."""
        gex = data.get("gex", 0)

        if gex > 500_000_000:
            signal = "bullish"
            summary = f"High +GEX ${gex / 1e6:.0f}M (dealers hedging upside)"
        elif gex < -500_000_000:
            signal = "bearish"
            summary = f"High -GEX ${gex / 1e6:.0f}M (dealers hedging downside)"
        else:
            signal = "neutral"
            summary = f"Low GEX ${gex / 1e6:.0f}M (balanced)"

        return {"signal": signal, "gex": gex, "summary": summary}

    def _analyze_unusual_activity(self, data: dict) -> dict:
        """Analyze unusual options activity."""
        put_call = data.get("put_call_ratio", 1.0)

        if put_call < 0.5:
            signal = "bullish"
            summary = f"Low PCR {put_call:.2f} (calls dominant)"
        elif put_call > 1.5:
            signal = "bearish"
            summary = f"High PCR {put_call:.2f} (puts dominant)"
        else:
            signal = "neutral"
            summary = f"Normal PCR {put_call:.2f}"

        return {"signal": signal, "put_call_ratio": put_call, "summary": summary}

    def _detect_short_squeeze(self, data: dict) -> dict:
        """Detect short squeeze potential."""
        # Simplified squeeze detection
        return {
            "probability": "low",
            "factors": [],
            "summary": "No short squeeze signals",
        }


async def run_options_flow_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = OptionsFlowAgent()
    result = await agent.analyze(state)
    return {"options_flow_signal": result.to_dict()}

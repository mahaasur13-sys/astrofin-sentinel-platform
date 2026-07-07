"""
Elliot Agent — Elliott Wave analysis.
"""

from __future__ import annotations

import logging

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class ElliotAgent(BaseAgent[AgentResponse]):
    """
    ElliotAgent — анализ волн Эллиотта.

    Responsibilities:
    1. Identify 5-wave impulse patterns
    2. Count corrective waves (ABC, zigzag, flat)
    3. Detect wave extensions and truncations
    4. Predict wave targets using Fibonacci ratios

    Weight: 3% (minor agent)
    """

    def __init__(self):
        super().__init__(
            name="ElliotAgent",
            instructions_path=None,
            domain="technical",
            weight=0.03,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Analyze Elliott Wave structure.
        """
        symbol = state.get("symbol", "BTCUSDT")
        state.get("current_price", 50000)

        price_data = await self._fetch_ohlcv(symbol, "1d", 120)
        if not price_data:
            return AgentResponse(
                agent_name="ElliotAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=20,
                reasoning="No market data for Elliott Wave analysis",
                sources=[],
            )

        closes = [d[0] for d in price_data]
        highs = [d[1] for d in price_data]
        lows = [d[2] for d in price_data]

        wave_count = self._count_waves(highs, lows, closes)
        fib_targets = self._calculate_fib_targets(wave_count, highs, lows, closes)
        corrective = self._detect_corrective_phase(closes)

        # Elliott score
        elliot_score = wave_count["score"] * 0.50 + fib_targets["score"] * 0.30 + corrective["score"] * 0.20

        if wave_count["suggestion"] == "long":
            signal = SignalDirection.LONG
            confidence = min(int(elliot_score * 100 + 10), 70)
        elif wave_count["suggestion"] == "short":
            signal = SignalDirection.SHORT
            confidence = min(int(elliot_score * 100 + 10), 70)
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 40

        reasoning = f"Wave structure: {wave_count['summary']}. Fib targets: {fib_targets['summary']}. Corrective phase: {corrective['summary']}. Elliot score: {elliot_score:.2f}"

        return AgentResponse(
            agent_name="ElliotAgent",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["technical/elliott_wave.md"],
            metadata={
                "elliot_score": elliot_score,
                "wave_count": wave_count,
                "fib_targets": fib_targets,
                "corrective": corrective,
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

    async def _fetch_ohlcv(self, symbol: str, interval: str, limit: int) -> list:
        """Fetch OHLCV data from OKX asynchronously."""
        import httpx

        try:
            url = f"https://www.okx.com/api/v5/market/candles?symbol={symbol}-USDT&interval={interval}&limit={limit}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                return [[float(x[4]), float(x[5])] for x in data.get("data", [])]
        except Exception:
            logger.warning(f"Failed to fetch OHLCV data for {symbol}-USDT with interval {interval} and limit {limit}")
            return []

    def _count_waves(self, highs: list, lows: list, closes: list) -> dict:
        """
        Simplified wave counting.
        """
        if len(closes) < 30:
            return {
                "score": 0.5,
                "summary": "insufficient data",
                "suggestion": "neutral",
            }

        # Detect swings
        swing_highs = []
        swing_lows = []

        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                swing_highs.append((i, highs[i]))
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                swing_lows.append((i, lows[i]))

        # Simplified wave detection
        if len(swing_highs) < 3 or len(swing_lows) < 3:
            return {
                "score": 0.5,
                "summary": "no clear wave pattern",
                "suggestion": "neutral",
            }

        # Check trend
        recent_trend = closes[-1] - closes[-20]

        # Simplified wave counting
        num_swings = min(len(swing_highs), len(swing_lows))

        if num_swings >= 5 and recent_trend > 0:
            suggestion = "long"
            score = 0.65
            summary = "5-wave impulse detected, currently in wave 5+"
        elif num_swings >= 5 and recent_trend < 0:
            suggestion = "short"
            score = 0.65
            summary = "5-wave impulse to downside, currently in wave 5+"
        elif num_swings >= 3:
            suggestion = "neutral"
            score = 0.50
            summary = "3-wave structure, corrective phase likely"
        else:
            suggestion = "neutral"
            score = 0.40
            summary = f"wave count unclear ({num_swings} swings)"

        return {
            "score": score,
            "summary": summary,
            "suggestion": suggestion,
            "num_swings": num_swings,
        }

    def _calculate_fib_targets(self, wave_count: dict, highs: list, lows: list, closes: list) -> dict:
        """
        Calculate Fibonacci retracement/extension targets.
        """
        if len(closes) < 20:
            return {"score": 0.5, "summary": "insufficient data"}

        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        current = closes[-1]

        range_size = recent_high - recent_low
        if range_size == 0:
            return {"score": 0.5, "summary": "no range"}

        # Fibonacci levels
        fib_levels = [0.382, 0.500, 0.618, 0.786, 1.000, 1.272, 1.618]

        current_level = (current - recent_low) / range_size if range_size > 0 else 0.5

        # Check proximity to Fib levels
        near_level = None
        for fib in fib_levels:
            if abs(current_level - fib) < 0.05:
                near_level = fib
                break

        if near_level is not None:
            score = 0.65
            summary = f"price at {near_level * 100:.1f}% Fibonacci level"
        else:
            score = 0.50
            summary = f"price at {current_level * 100:.1f}% of recent range"

        return {"score": score, "summary": summary, "current_level": current_level}

    def _detect_corrective_phase(self, closes: list) -> dict:
        """
        Detect if we're in a corrective phase.
        """
        if len(closes) < 20:
            return {"score": 0.5, "summary": "insufficient data"}

        # Simple corrective detection — overlapping waves
        wave1 = closes[-20] - closes[-15]
        wave2 = closes[-15] - closes[-10]
        wave3 = closes[-10] - closes[-5]

        # Check for 3-wave structure (A-B-C)
        if wave1 * wave3 < 0:  # Direction change
            # Could be ABC corrective
            if abs(wave2) < abs(wave1) and abs(wave2) < abs(wave3):
                score = 0.60
                summary = "possible ABC corrective pattern"
            else:
                score = 0.50
                summary = "3-wave structure detected"
        else:
            score = 0.45
            summary = "no clear corrective pattern"

        return {"score": score, "summary": summary}


async def run_elliot_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = ElliotAgent()
    result = await agent.analyze(state)
    return {"elliot_signal": result.to_dict()}

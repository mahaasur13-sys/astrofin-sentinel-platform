"""
Bear Researcher Agent — bearish case for trading opportunities.
"""

from __future__ import annotations

import logging

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class BearResearcherAgent(BaseAgent[AgentResponse]):
    """
    BearResearcher — ищет медвежий кейс для актива.

    Responsibilities:
    1. Scan for bearish chart patterns
    2. Analyze negative fundamental/news catalysts
    3. Identify resistance zones and distribution
    4. Cross-reference with astro indicators (Saturn, Mars aspects)

    Weight: 15%
    """

    def __init__(self):
        super().__init__(
            name="BearResearcher",
            instructions_path="agents/BearResearcher_instructions.md",
            domain="trading",
            weight=0.15,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Analyze bearish case for the symbol.

        Returns: SHORT / NEUTRAL signal with confidence and reasoning.
        """
        symbol = state.get("symbol", "BTCUSDT")
        state.get("current_price", 50000)
        timeframe = state.get("timeframe_requested", "SWING")

        price_data = await self._fetch_ohlcv(symbol, "1d", 60)
        if not price_data:
            return AgentResponse(
                agent_name="BearResearcher",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="No market data available for bear case analysis",
                sources=[],
            )

        patterns = self._detect_bearish_patterns(price_data)
        volume_profile = self._analyze_volume_bearish(price_data)
        resistance_zones = self._find_resistance_zones(price_data)
        astro_signal = await self._check_astro_bearish(state)

        bearish_score = (
            patterns["score"] * 0.30
            + volume_profile["score"] * 0.25
            + resistance_zones["score"] * 0.20
            + astro_signal["score"] * 0.25
        )

        if bearish_score >= 0.65:
            signal = SignalDirection.SHORT
            confidence = min(int(bearish_score * 100 + 10), 85)
        elif bearish_score >= 0.45:
            signal = SignalDirection.NEUTRAL
            confidence = 50
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 35

        reasoning = (
            f"Bearish patterns: {patterns['summary']}. "
            f"Volume: {volume_profile['summary']}. "
            f"Resistance zones: {resistance_zones['summary']}. "
            f"Astro: {astro_signal['summary']}. "
            f"Bear score: {bearish_score:.2f}"
        )

        return AgentResponse(
            agent_name="BearResearcher",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["trading/bearish_patterns.md", "astrology/financial.md"],
            metadata={
                "bearish_score": bearish_score,
                "patterns": patterns,
                "volume": volume_profile,
                "resistance": resistance_zones,
                "astro": astro_signal,
                "symbol": symbol,
                "timeframe": timeframe,
            },
        )

    @track_agent_metrics
    async def run(self, state: dict) -> AgentResponse:
        """Public entry point. Wraps analyze() with the latency histogram and defensive error handling."""
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
                return [
                    [
                        float(x[1]),  # open
                        float(x[2]),  # high
                        float(x[3]),  # low
                        float(x[4]),  # close
                        float(x[5]),  # volume
                    ]
                    for x in data.get("data", [])
                ]
        except Exception:
            logger.warning(f"Failed to fetch OHLCV data for {symbol}-USDT on {interval} with limit {limit}")
            return []

    def _detect_bearish_patterns(self, data: list) -> dict:
        """Detect bearish candlestick patterns."""
        if len(data) < 20:
            return {"score": 0.4, "summary": "insufficient data"}

        closes = [d[3] for d in data]
        highs = [d[2] for d in data]
        lows = [d[1] for d in data]

        # Lower highs pattern
        lh_count = 0
        for i in range(3, len(highs)):
            if highs[i] < highs[i - 1] < highs[i - 2]:
                lh_count += 1

        # Breakdown below recent low
        recent_low = min(lows[-20:-5])
        current_low = min(lows[-5:])
        breakdown = current_low < recent_low

        score = 0.5
        if lh_count >= 2:
            score += 0.15
        if breakdown:
            score += 0.20
        if closes[-1] < closes[-10]:
            score += 0.15

        summary = f"Lower highs: {lh_count}, breakdown: {'yes' if breakdown else 'no'}"

        return {"score": min(score, 1.0), "summary": summary}

    def _analyze_volume_bearish(self, data: list) -> dict:
        """Analyze volume for bearish confirmation."""
        if len(data) < 20:
            return {"score": 0.4, "summary": "insufficient data"}

        volumes = [d[4] for d in data[-20:]]
        recent_vol = sum(volumes[-5:]) / 5
        older_vol = sum(volumes[-20:-5]) / 15

        if recent_vol > older_vol * 1.3:
            score = 0.70
            summary = f"volume increasing +{((recent_vol / older_vol) - 1) * 100:.0f}%"
        elif recent_vol > older_vol * 1.1:
            score = 0.55
            summary = f"volume stable +{((recent_vol / older_vol) - 1) * 100:.0f}%"
        else:
            score = 0.40
            summary = f"volume declining {((recent_vol / older_vol) - 1) * 100:.0f}%"

        return {"score": min(score, 1.0), "summary": summary}

    def _find_resistance_zones(self, data: list) -> dict:
        """Find bearish resistance zones."""
        if len(data) < 20:
            return {"score": 0.4, "summary": "insufficient data"}

        highs = [d[2] for d in data[-30:]]
        current_price = highs[-1]

        swing_highs = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                swing_highs.append(highs[i])

        if not swing_highs:
            return {"score": 0.5, "summary": "no clear resistance identified"}

        nearest_resistance = min([r for r in swing_highs if r > current_price], default=highs[-5])

        distance_pct = ((nearest_resistance - current_price) / current_price) * 100

        if distance_pct < 2:
            score = 0.75
        elif distance_pct < 5:
            score = 0.60
        else:
            score = 0.45

        summary = f"resistance at ${nearest_resistance:,.0f} ({distance_pct:.1f}% above)"

        return {"score": min(score, 1.0), "summary": summary}

    async def _check_astro_bearish(self, state: dict) -> dict:
        """Check astro indicators for bearish bias."""
        from datetime import datetime

        from core.ephemeris import HAS_SWISS_EPHEMERIS, _julian_day, calculate_planet

        if not HAS_SWISS_EPHEMERIS:
            return {"score": 0.5, "summary": "ephemeris unavailable"}

        now = datetime.utcnow()
        jd = _julian_day(now)

        saturn = calculate_planet("saturn", jd)
        mars = calculate_planet("mars", jd)

        bearish_signs_saturn = [1, 3, 6]  # Taurus, Cancer, Capricorn
        saturn_score = 0.5
        if int(saturn.longitude / 30) in bearish_signs_saturn:
            saturn_score = 0.70

        # Mars in challenging aspect
        if mars.retrograde:
            mars_score = 0.65

        total = saturn_score * 0.6 + mars_score * 0.4

        summary = f"Saturn: {saturn.longitude:.1f}°, Mars retrograde: {mars.retrograde}"

        return {"score": total, "summary": summary}


async def run_bear_researcher(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = BearResearcherAgent()
    result = await agent.analyze(state)
    return {"bear_signal": result.to_dict()}

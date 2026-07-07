"""
Bull Researcher Agent — bullish case for trading opportunities.
"""

from __future__ import annotations

import logging

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class BullResearcherAgent(BaseAgent[AgentResponse]):
    """
    BullResearcher — ищет бычий кейс для актива.

    Responsibilities:
    1. Scan for bullish chart patterns
    2. Analyze positive fundamental/news catalysts
    3. Identify support zones and accumulation
    4. Cross-reference with astro indicators (Jupiter, Moon phases)

    Weight: 15%
    """

    def __init__(self):
        super().__init__(
            name="BullResearcher",
            instructions_path="agents/BullResearcher_instructions.md",
            domain="trading",
            weight=0.15,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Analyze bullish case for the symbol.

        Returns: LONG / NEUTRAL signal with confidence and reasoning.
        """
        symbol = state.get("symbol", "BTCUSDT")
        state.get("current_price", 50000)
        timeframe = state.get("timeframe_requested", "SWING")

        # Fetch market data for pattern recognition
        price_data = await self._fetch_ohlcv(symbol, "1d", 60)
        if not price_data:
            return AgentResponse(
                agent_name="BullResearcher",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="No market data available for bull case analysis",
                sources=[],
            )

        # Analyze price action for bullish patterns
        patterns = self._detect_bullish_patterns(price_data)
        volume_profile = self._analyze_volume_bullish(price_data)
        support_zones = self._find_support_zones(price_data)

        # Astro overlay — Jupiter, Moon in Taurus/Libra
        astro_signal = await self._check_astro_bullish(state)

        # Aggregate bullish score
        bullish_score = patterns["score"] * 0.30 + volume_profile["score"] * 0.25 + support_zones["score"] * 0.20 + astro_signal["score"] * 0.25

        if bullish_score >= 0.65:
            signal = SignalDirection.LONG
            confidence = min(int(bullish_score * 100 + 10), 85)
        elif bullish_score >= 0.45:
            signal = SignalDirection.NEUTRAL
            confidence = 50
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 35

        reasoning = (
            f"Bullish patterns: {patterns['summary']}. "
            f"Volume: {volume_profile['summary']}. "
            f"Support zones: {support_zones['summary']}. "
            f"Astro: {astro_signal['summary']}. "
            f"Bull score: {bullish_score:.2f}"
        )

        return AgentResponse(
            agent_name="BullResearcher",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["trading/bullish_patterns.md", "astrology/financial.md"],
            metadata={
                "bullish_score": bullish_score,
                "patterns": patterns,
                "volume": volume_profile,
                "supports": support_zones,
                "astro": astro_signal,
                "symbol": symbol,
                "timeframe": timeframe,
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
                # OKX возвращает [timestamp, open, high, low, close, volume]
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

    def _detect_bullish_patterns(self, data: list) -> dict:
        """Detect bullish candlestick patterns."""
        if len(data) < 20:
            return {"score": 0.4, "summary": "insufficient data"}

        closes = [d[3] for d in data]
        highs = [d[2] for d in data]
        lows = [d[1] for d in data]

        # Higher lows pattern
        hl_count = 0
        for i in range(3, len(lows)):
            if lows[i] > lows[i - 1] > lows[i - 2]:
                hl_count += 1

        # Breakout above recent high
        recent_high = max(highs[-20:-5])
        current_high = max(highs[-5:])
        breakout = current_high > recent_high

        score = 0.5
        if hl_count >= 2:
            score += 0.15
        if breakout:
            score += 0.20
        if closes[-1] > closes[-10]:
            score += 0.15

        summary = f"Higher lows: {hl_count}, breakout: {'yes' if breakout else 'no'}"

        return {"score": min(score, 1.0), "summary": summary}

    def _analyze_volume_bullish(self, data: list) -> dict:
        """Analyze volume for bullish confirmation."""
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

    def _find_support_zones(self, data: list) -> dict:
        """Find bullish support zones."""
        if len(data) < 20:
            return {"score": 0.4, "summary": "insufficient data"}

        lows = [d[1] for d in data[-30:]]
        current_price = lows[-1]

        # Find recent swing lows
        swing_lows = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                swing_lows.append(lows[i])

        if not swing_lows:
            return {"score": 0.5, "summary": "no clear support identified"}

        nearest_support = max([s for s in swing_lows if s < current_price], default=lows[-5])

        distance_pct = ((current_price - nearest_support) / current_price) * 100

        if distance_pct < 2:
            score = 0.75
        elif distance_pct < 5:
            score = 0.60
        else:
            score = 0.45

        summary = f"support at ${nearest_support:,.0f} ({distance_pct:.1f}% below)"

        return {"score": min(score, 1.0), "summary": summary}

    async def _check_astro_bullish(self, state: dict) -> dict:
        """Check astro indicators for bullish bias."""
        from datetime import datetime

        from core.ephemeris import HAS_SWISS_EPHEMERIS, _julian_day, calculate_planet

        if not HAS_SWISS_EPHEMERIS:
            return {"score": 0.5, "summary": "ephemeris unavailable"}

        now = datetime.utcnow()
        jd = _julian_day(now)

        jupiter = calculate_planet("jupiter", jd)
        moon = calculate_planet("moon", jd)

        # Jupiter in bullish sign
        bullish_signs_jupiter = [0, 2, 4, 8]  # Aries, Gemini, Leo, Pisces approximate
        jupiter_score = 0.5
        if int(jupiter.longitude / 30) in bullish_signs_jupiter:
            jupiter_score = 0.70

        # Moon waxing (first half of cycle)
        moon_phase = (moon.longitude / 360) * 100
        moon_score = 0.55 if moon_phase < 50 else 0.45

        total = jupiter_score * 0.6 + moon_score * 0.4

        summary = f"Jupiter: {jupiter.longitude:.1f}°, Moon phase: {moon_phase:.0f}%"

        return {"score": total, "summary": summary}


async def run_bull_researcher(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = BullResearcherAgent()
    result = await agent.analyze(state)
    return {"bull_signal": result.to_dict()}


def create() -> BullResearcherAgent:
    """Factory for 6-fn test contract."""
    return BullResearcherAgent()

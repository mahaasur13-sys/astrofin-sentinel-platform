"""
Bradley Agent — Bradley Model (S&P 500 seasonality/cyccles).
"""

from __future__ import annotations

import logging

from agents._impl.ephemeris_decorator import (
    EphemerisUnavailableError,
    require_ephemeris,
)
from agents.metrics import track_agent_metrics
from core.base_agent import (
    EPHEMERIS_UNAVAILABLE,
    UNKNOWN,
    AgentResponse,
    BaseAgent,
    SignalDirection,
)

logger = logging.getLogger(__name__)


class BradleyAgent(BaseAgent[AgentResponse]):
    """
    BradleyAgent — модель Брэдли (сезонность S&P 500).

    Responsibilities:
    1. Calculate Bradley seasonality index
    2. Identify high-probability seasonal turning points
    3. Cross-reference with planetary aspects

    Weight: 3% (minor agent)
    Note: Most accurate for S&P 500, adapted for crypto.
    """

    def __init__(self):
        super().__init__(
            name="BradleyAgent",
            instructions_path=None,
            domain="technical",
            weight=0.03,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Analyze using Bradley Model.
        """
        symbol = state.get("symbol", "BTCUSDT")

        price_data = state.get("_price_data", []) or await self._fetch_ohlcv(symbol, "1D", 365)
        if not price_data:
            return AgentResponse(
                agent_name="BradleyAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=20,
                reasoning="No market data for Bradley Model analysis",
                sources=[],
            )

        # Bradley seasonality
        seasonality = self._calculate_seasonality(price_data)
        planetary_aspects = await self._check_planetary_aspects(state)

        # Bradley score
        bradley_score = seasonality["score"] * 0.50 + planetary_aspects["score"] * 0.50

        if bradley_score >= 0.60:
            signal = SignalDirection.LONG
            confidence = min(int(bradley_score * 100), 75)
        elif bradley_score <= 0.35:
            signal = SignalDirection.SHORT
            confidence = min(int((1 - bradley_score) * 100), 75)
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 40

        reasoning = f"Bradley seasonality: {seasonality['summary']}. Planetary aspects: {planetary_aspects['summary']}. Bradley score: {bradley_score:.2f}"

        return AgentResponse(
            agent_name="BradleyAgent",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["technical/bradley_model.md", "astrology/planetary_aspects.md"],
            metadata={
                "bradley_score": bradley_score,
                "seasonality": seasonality,
                "planetary_aspects": planetary_aspects,
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
            url = f"https://www.okx.com/api/v5/market/candles?instId={symbol if "-" in symbol else symbol + "-USDT"}&bar={interval}&limit={limit}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                return [[float(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])] for x in data.get("data", [])]
        except Exception:
            logger.warning(
                f"Failed to fetch OHLCV data for {symbol} with interval {interval} and limit {limit}"
            )
            return []

    def _calculate_seasonality(self, data: list) -> dict:
        """
        Calculate Bradley-like seasonality index.
        Based on day-of-year performance patterns.
        """
        if len(data) < 90:
            return {"score": 0.5, "summary": "insufficient data for seasonality"}

        from datetime import datetime

        # Map closes to day of year
        daily_returns = {}
        for i in range(1, len(data)):
            # Approximate day of year
            day = i % 365
            if data[i][0] > data[i - 1][0]:
                daily_returns[day] = daily_returns.get(day, []) + [1]
            else:
                daily_returns[day] = daily_returns.get(day, []) + [-1]

        # Find current period's historical performance
        now = datetime.utcnow()
        current_day = now.timetuple().tm_yday

        # Check past 30 days of current period
        period_returns = []
        for offset in range(-30, 1):
            check_day = (current_day + offset) % 365
            if check_day in daily_returns:
                period_returns.extend(daily_returns[check_day])

        if not period_returns:
            return {"score": 0.5, "summary": f"day {current_day}: no historical data"}

        avg_return = sum(period_returns) / len(period_returns)

        if avg_return > 0.1:
            score = 0.70
            summary = f"day {current_day}: historically bullish ({avg_return * 100:.1f}% avg return)"
        elif avg_return < -0.1:
            score = 0.30
            summary = f"day {current_day}: historically bearish ({avg_return * 100:.1f}% avg return)"
        else:
            score = 0.50
            summary = f"day {current_day}: historically neutral ({avg_return * 100:.1f}% avg return)"

        return {"score": score, "summary": summary, "avg_return": avg_return}

    async def _check_planetary_aspects(self, state: dict) -> dict:
        """
        Check major planetary aspects for Bradley-style forecasts.
        """
        from datetime import datetime

        from core.ephemeris import HAS_SWISS_EPHEMERIS, _julian_day, calculate_planet

        if not HAS_SWISS_EPHEMERIS:
            return {"score": 0.5, "summary": "ephemeris unavailable"}

        now = datetime.utcnow()
        jd = _julian_day(now)

        # Get major planets
        jupiter = calculate_planet("jupiter", jd)
        saturn = calculate_planet("saturn", jd)
        uranus = calculate_planet("uranus", jd)
        calculate_planet("neptune", jd)

        # Check Jupiter-Saturn aspect (major cycle)
        js_angle = abs(jupiter.longitude - saturn.longitude) % 360
        aspects_found = []

        # Jupiter-Saturn
        for aspect_deg in [0, 60, 90, 120, 180]:
            if abs(js_angle - aspect_deg) < 8:
                aspects_found.append(f"J-S {aspect_deg}°")

        # Jupiter-Uranus
        ju_angle = abs(jupiter.longitude - uranus.longitude) % 360
        for aspect_deg in [0, 60, 90, 120, 180]:
            if abs(ju_angle - aspect_deg) < 8:
                aspects_found.append(f"J-U {aspect_deg}°")

        # Saturn-Uranus
        su_angle = abs(saturn.longitude - uranus.longitude) % 360
        for aspect_deg in [0, 60, 90, 120, 180]:
            if abs(su_angle - aspect_deg) < 8:
                aspects_found.append(f"S-U {aspect_deg}°")

        if len(aspects_found) >= 2:
            score = 0.65
            summary = f"Multiple aspects active: {', '.join(aspects_found)}"
        elif aspects_found:
            score = 0.55
            summary = f"Single aspect: {aspects_found[0]}"
        else:
            score = 0.45
            summary = f"No major aspects currently (J-S: {js_angle:.0f}°)"

        return {"score": score, "summary": summary, "aspects": aspects_found}


async def run_bradley_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = BradleyAgent()
    result = await agent.analyze(state)
    return {"bradley_signal": result.to_dict()}


def create() -> BradleyAgent:
    """Factory for 6-fn test contract."""
    return BradleyAgent()

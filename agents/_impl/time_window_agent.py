"""
Time Window Agent — entry timing and best trading windows.
"""

from __future__ import annotations

import logging
from datetime import datetime

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class TimeWindowAgent(BaseAgent[AgentResponse]):
    """
    TimeWindowAgent — определение лучших окон для входа.

    Responsibilities:
    1. Scan multiple timeframes for confluence
    2. Identify optimal entry windows (4H, 1D, 1W)
    3. Cross-reference with astro timing (Choghadiya, Muhurta)
    4. Avoid low-liquidity periods

    Weight: 2% (minor agent)
    """

    def __init__(self):
        super().__init__(
            name="TimeWindowAgent",
            instructions_path=None,
            domain="astrology",
            weight=0.02,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Find optimal time windows for entry.
        """
        symbol = state.get("symbol", "BTCUSDT")
        state.get("timeframe_requested", "SWING")

        # Scan windows across timeframes
        window_4h = await self._scan_4h_window(symbol)
        window_1d = await self._scan_daily_window(symbol)
        window_1w = await self._scan_weekly_window(symbol)
        astro_window = await self._check_astro_timing(state)

        # Find confluence
        windows = [window_4h, window_1d, window_1w, astro_window]
        bullish_windows = sum(1 for w in windows if w["direction"] == "bullish")
        bearish_windows = sum(1 for w in windows if w["direction"] == "bearish")

        if bullish_windows >= 3:
            signal = SignalDirection.LONG
            confidence = 65
            direction = "bullish"
        elif bearish_windows >= 3:
            signal = SignalDirection.SHORT
            confidence = 65
            direction = "bearish"
        elif bullish_windows > bearish_windows:
            signal = SignalDirection.LONG
            confidence = 50
            direction = "slight_bullish"
        elif bearish_windows > bullish_windows:
            signal = SignalDirection.SHORT
            confidence = 50
            direction = "slight_bearish"
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 40
            direction = "neutral"

        reasoning = (
            f"4H window: {window_4h['summary']}. "
            f"1D window: {window_1d['summary']}. "
            f"1W window: {window_1w['summary']}. "
            f"Astro timing: {astro_window['summary']}. "
            f"Overall: {direction} ({bullish_windows} bullish / {bearish_windows} bearish windows)"
        )

        return AgentResponse(
            agent_name="TimeWindowAgent",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["astrology/muhurta.md", "technical/timeframes.md"],
            metadata={
                "direction": direction,
                "window_4h": window_4h,
                "window_1d": window_1d,
                "window_1w": window_1w,
                "astro_window": astro_window,
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
        except Exception:  # noqa: BLE001
            logger.warning(f"Failed to fetch OHLCV data for {symbol}-USDT with interval {interval} and limit {limit}")
            return []

    async def _scan_4h_window(self, symbol: str) -> dict:
        """Scan 4-hour windows for entry opportunity."""
        data = await self._fetch_ohlcv(symbol, "4h", 30)
        if len(data) < 10:
            return {"direction": "neutral", "summary": "insufficient 4H data"}

        closes = [d[0] for d in data]
        now = datetime.utcnow()
        hour = now.hour

        # Check if we're at start of 4H candle (higher volume expected)
        is_candle_start = hour % 4 == 0

        # Check recent trend
        trend = closes[-4] > closes[-8] if len(closes) >= 8 else False

        if is_candle_start and trend:
            direction = "bullish"
            summary = "4H candle start + uptrend"
            score = 0.65
        elif is_candle_start and not trend:
            direction = "bearish"
            summary = "4H candle start + downtrend"
            score = 0.65
        elif trend:
            direction = "bullish"
            summary = "4H trend up, no candle start"
            score = 0.55
        else:
            direction = "neutral"
            summary = "4H no clear setup"
            score = 0.50

        return {"direction": direction, "summary": summary, "score": score}

    async def _scan_daily_window(self, symbol: str) -> dict:
        """Scan daily windows."""
        data = await self._fetch_ohlcv(symbol, "1d", 20)
        if len(data) < 10:
            return {"direction": "neutral", "summary": "insufficient 1D data"}

        closes = [d[0] for d in data]
        now = datetime.utcnow()
        weekday = now.weekday()  # 0=Monday

        # Check day-of-week patterns
        # Monday-Tuesday: often continuation
        # Wednesday-Thursday: often range-bound
        # Friday: often reversal

        if weekday in [0, 1]:  # Monday, Tuesday
            # Check if recent trend continues
            if closes[-1] > closes[-5]:
                direction = "bullish"
                summary = "1D: continuation bias (start of week)"
            else:
                direction = "bearish"
                summary = "1D: continuation bias (start of week)"
            score = 0.55
        elif weekday == 4:  # Friday
            # Often reversal day
            if closes[-1] > closes[-3]:
                direction = "bearish"
                summary = "1D: Friday reversal (profit taking likely)"
            else:
                direction = "bullish"
                summary = "1D: Friday rebound"
            score = 0.55
        else:
            direction = "neutral"
            summary = f"1D: midweek ({['Mon', 'Tue', 'Wed', 'Thu', 'Fri'][weekday]})"
            score = 0.50

        return {"direction": direction, "summary": summary, "score": score}

    async def _scan_weekly_window(self, symbol: str) -> dict:
        """Scan weekly windows."""
        data = await self._fetch_ohlcv(symbol, "1d", 60)  # Use daily for weekly
        if len(data) < 20:
            return {"direction": "neutral", "summary": "insufficient 1W data"}

        closes = [d[0] for d in data]

        # Check weekly trend
        if len(closes) >= 7:
            weekly_close = closes[-7]
            prev_week_close = closes[-14] if len(closes) >= 14 else closes[0]

            if weekly_close > prev_week_close:
                direction = "bullish"
                summary = "1W: bullish weekly close"
                score = 0.60
            else:
                direction = "bearish"
                summary = "1W: bearish weekly close"
                score = 0.60
        else:
            direction = "neutral"
            summary = "1W: insufficient data"
            score = 0.50

        return {"direction": direction, "summary": summary, "score": score}

    async def _check_astro_timing(self, state: dict) -> dict:
        """Check astro timing windows."""
        from datetime import datetime

        from astrology.vedic import get_choghadiya, get_current_nakshatra

        now = datetime.utcnow()

        choghadiya = get_choghadiya(now)
        nakshatra = get_current_nakshatra(now)

        good_choghadiya = ["Amrita", "Shubha", "Labha"]
        bad_choghadiya = ["Marana", "Vyatipata", "Parivesha", "Mrityu"]

        if choghadiya["name"] in good_choghadiya:
            direction = "bullish"
            summary = f"Astro: {choghadiya['name']} + Nakshatra {nakshatra['name']}"
            score = 0.65
        elif choghadiya["name"] in bad_choghadiya:
            direction = "bearish"
            summary = f"Astro: avoid {choghadiya['name']}"
            score = 0.35
        else:
            direction = "neutral"
            summary = f"Astro: {choghadiya['name']} (neutral)"
            score = 0.50

        return {"direction": direction, "summary": summary, "score": score}


async def run_time_window_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = TimeWindowAgent()
    result = await agent.analyze(state)
    return {"time_window_signal": result.to_dict()}


def create() -> TimeWindowAgent:
    """Factory for 6-fn test contract."""
    return TimeWindowAgent()

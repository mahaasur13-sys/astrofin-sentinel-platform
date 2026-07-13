"""
AstroFin Sentinel v5 — Market Analyst Agent
Technical analysis: RSI, MACD, Bollinger, Volume.
"""

from __future__ import annotations

import logging

from agents._impl.ephemeris_decorator import EphemerisUnavailableError
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection
from agents.metrics import track_agent_duration

logger = logging.getLogger(__name__)


class MarketAnalystAgent(BaseAgent[AgentResponse]):
    """
    MarketAnalyst — главный технический аналитик.
    Вес: 25%
    """

    def __init__(self):
        super().__init__(
            name="MarketAnalyst",
            instructions_path="agents/MarketAnalyst_instructions.md",
            domain="technical",
            weight=0.25,
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

    async def analyze(self, state: dict) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        # Fetch market data
        price_data = await self._fetch_ohlcv(symbol, "1d", 50)
        if not price_data:
            return AgentResponse(
                agent_name="MarketAnalyst",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="No market data available",
                sources=[],
            )

        # Calculate indicators
        rsi = self._calculate_rsi(price_data)
        macd = self._calculate_macd(price_data)
        bb = self._calculate_bollinger(price_data)
        volume_profile = self._calculate_volume_profile(price_data)

        # Determine signal
        signals = []
        confidences = []

        # RSI
        if rsi < 30:
            signals.append(SignalDirection.LONG)
            confidences.append(70)
        else:
            signals.append(SignalDirection.NEUTRAL)
            confidences.append(50)

        # MACD
        if macd["histogram"] > 0:
            signals.append(SignalDirection.LONG)
            confidences.append(60)
        else:
            signals.append(SignalDirection.SHORT)
            confidences.append(60)

        # Bollinger
        if current_price < bb["lower"]:
            signals.append(SignalDirection.LONG)
            confidences.append(65)
        elif current_price > bb["upper"]:
            signals.append(SignalDirection.SHORT)
            confidences.append(65)
        else:
            signals.append(SignalDirection.NEUTRAL)
            confidences.append(40)

        # Aggregate
        long_count = signals.count(SignalDirection.LONG)
        short_count = signals.count(SignalDirection.SHORT)

        if long_count > short_count:
            direction = SignalDirection.LONG
        elif short_count > long_count:
            direction = SignalDirection.SHORT
        else:
            direction = SignalDirection.NEUTRAL

        avg_confidence = int(sum(confidences) / len(confidences))

        reasoning = (
            f"RSI(14)={rsi:.1f} {'(oversold)' if rsi < 30 else '(overbought)' if rsi > 70 else ''}. "
            f"MACD={'bullish' if macd['histogram'] > 0 else 'bearish'} "
            f"(signal={macd['macd']:.2f}, histogram={macd['histogram']:.2f}). "
            f"BB: price={'below' if current_price < bb['lower'] else 'above' if current_price > bb['upper'] else 'inside'} "
            f"bands [{bb['lower']:.0f}-{bb['upper']:.0f}]. "
            f"Vol: {volume_profile['trend']}"
        )

        return AgentResponse(
            agent_name="MarketAnalyst",
            signal=direction,
            confidence=avg_confidence,
            reasoning=reasoning,
            sources=["technical/rsi_macd.md", "technical/bollinger.md"],
            metadata={
                "rsi": rsi,
                "macd": macd,
                "bollinger": bb,
                "volume": volume_profile,
            },
        )

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
                return [[float(x[4]), float(x[5])] for x in data.get("data", [])]
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as e:
            logger.warning(f"Failed to fetch OHLCV data for {symbol}-USDT: {e}")
            return []

    def _calculate_rsi(self, data: list, period: int = 14) -> float:
        """Calculate RSI."""
        if len(data) < period + 1:
            return 50.0

        closes = [d[0] for d in data]
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, data: list, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """Calculate MACD."""
        if len(data) < slow + signal:
            return {"macd": 0, "signal": 0, "histogram": 0}

        closes = [d[0] for d in data]

        def ema(values: list, period: int) -> float:
            if len(values) < period:
                return values[-1] if values else 0
            multiplier = 2 / (period + 1)
            ema_val = sum(values[:period]) / period
            for price in values[period:]:
                ema_val = (price - ema_val) * multiplier + ema_val
            return ema_val

        ema_fast = ema(closes, fast)
        ema_slow = ema(closes, slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line * 0.9  # упрощённая сигнальная линия

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": macd_line - signal_line,
        }

    def _calculate_bollinger(self, data: list, period: int = 20, std_dev: int = 2) -> dict:
        """Calculate Bollinger Bands."""
        if len(data) < period:
            return {"upper": 0, "middle": 0, "lower": 0}

        closes = [d[0] for d in data][-period:]
        middle = sum(closes) / period

        variance = sum((c - middle) ** 2 for c in closes) / period
        std = variance**0.5

        return {
            "upper": middle + std_dev * std,
            "middle": middle,
            "lower": middle - std_dev * std,
        }

    def _calculate_volume_profile(self, data: list) -> dict:
        """Simple volume analysis."""
        if len(data) < 20:
            return {"trend": "insufficient data"}

        volumes = [d[1] for d in data[-20:]]
        recent_vol = sum(volumes[-5:]) / 5
        older_vol = sum(volumes[-20:-5]) / 15

        if recent_vol > older_vol * 1.2:
            trend = "increasing (bullish volume)"
        elif recent_vol < older_vol * 0.8:
            trend = "decreasing (bearish volume)"
        else:
            trend = "stable"

        return {"trend": trend, "recent_avg": recent_vol, "older_avg": older_vol}


@track_agent_duration("MarketAnalyst")
async def run_market_analyst(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = MarketAnalystAgent()
    result = await agent.run(state)
    return {"market_analyst_signal": result.to_dict()}


def create() -> MarketAnalystAgent:
    """Factory for 6-fn test contract."""
    return MarketAnalystAgent()

"""
AstroFin Sentinel v5 — Technical Agent
Технический анализ: RSI, MACD, Bollinger, Volume.
Вес в гибридном сигнале: 10% (как фильтр).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from agents._impl.ephemeris_decorator import (
    EphemerisUnavailableError,
    require_ephemeris,
)
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class TechnicalAgent(BaseAgent[AgentResponse]):
    """
    TechnicalAgent — технический анализ (используется как фильтр).
    85% technical + 15% астрологический бонус.
    """

    def __init__(self):
        super().__init__(
            name="Technical",
            instructions_path=None,
            domain="technical",
            weight=0.10,
        )

    @track_agent_metrics
    async def run(self, state: dict[str, Any]) -> AgentResponse:
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

    @require_ephemeris
    async def analyze(self, state: dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price") or state.get("price") or 50000
        dt = state.get("datetime") or datetime.utcnow()

        # 1. Астрологические данные
        eph = self._call_ephemeris(dt)

        # 2. Загрузка OHLCV
        price_data = await self._fetch_ohlcv(symbol, "1d", 50)

        # 3. Расчёт индикаторов
        indicators = self._calculate_indicators(price_data, current_price)

        # 4. Гибридный скоринг
        score = self._calculate_technical_score(indicators, eph)

        # 5. Определение сигнала
        if score >= 80:
            signal = "STRONG_BUY"
        elif score >= 65:
            signal = "BUY"
        elif score >= 50:
            signal = "NEUTRAL"
        elif score >= 35:
            signal = "SELL"
        else:
            signal = "STRONG_SELL"

        return AgentResponse(
            agent_name="Technical",
            signal=signal,
            confidence=min(88, int(score)),
            reasoning=self._build_reasoning(indicators, score),
            sources=["Binance API", "Technical analysis"],
            metadata={
                "technical_score": score,
                "rsi": indicators.get("rsi"),
                "macd": indicators.get("macd"),
                "bollinger": indicators.get("bollinger"),
                "volume": indicators.get("volume_trend"),
                "astro_influence": self._get_astro_influence(eph),
                "source": "binance + astrological_bonus",
            },
        )

    def _call_ephemeris(self, dt: datetime) -> dict:
        """Критичный вызов Swiss Ephemeris."""
        try:
            from core.ephemeris import (
                HAS_SWISS_EPHEMERIS,
                _julian_day,
                calculate_planet,
            )

            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown", "score": 50}

            jd = _julian_day(dt)
            mars = calculate_planet("mars", jd)
            moon = calculate_planet("moon", jd)
            venus = calculate_planet("venus", jd)

            # Mars = action, momentum
            score = 50
            mars_moon = abs(mars.longitude - moon.longitude) % 360

            if mars_moon < 30 or mars_moon > 330:
                score += 10  # Mars trine Moon = momentum
            elif 85 < mars_moon < 95:
                score -= 10  # Mars square Moon = volatility

            # Venus = stability
            ven_moon = abs(venus.longitude - moon.longitude) % 360
            if ven_moon < 30 or ven_moon > 330:
                score += 5

            return {
                "yoga": "mars_venus_moon",
                "score": max(0, min(100, score)),
                "mars": mars.longitude,
                "moon": moon.longitude,
            }
        except Exception as e:
            logger.warning(f"[TechnicalAgent] Error calculating ephemeris: {e}")
            return {"yoga": "unknown", "score": 50}

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
            logger.warning(
                f"Failed to fetch OHLCV data for {symbol}-USDT with interval {interval} and limit {limit}"
            )
            return []

    def _calculate_indicators(self, data: list, current_price: float) -> dict:
        """Расчёт RSI, MACD, Bollinger."""
        indicators = {
            "rsi": 50.0,
            "macd": {"histogram": 0},
            "bollinger": {"position": 0.5},
            "volume_trend": "stable",
        }

        if len(data) < 26:
            return indicators

        closes = [d[0] for d in data]

        # RSI(14)
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-14:]]
        losses = [-d if d < 0 else 0 for d in deltas[-14:]]
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        indicators["rsi"] = 100 - (100 / (1 + rs))

        # MACD(12, 26, 9)
        ema_fast = self._ema(closes, 12)
        ema_slow = self._ema(closes, 26)
        macd_line = ema_fast - ema_slow
        indicators["macd"] = {"histogram": macd_line, "signal": macd_line * 0.9}

        # Bollinger Bands
        period = 20
        if len(closes) >= period:
            bb_closes = closes[-period:]
            middle = sum(bb_closes) / period
            std = (sum((c - middle) ** 2 for c in bb_closes) / period) ** 0.5
            upper = middle + 2 * std
            lower = middle - 2 * std
            pos = (current_price - lower) / (upper - lower) if upper > lower else 0.5
            indicators["bollinger"] = {
                "upper": upper,
                "lower": lower,
                "middle": middle,
                "position": pos,
            }

        # Volume profile
        if len(data) >= 20:
            recent_vol = sum(d[1] for d in data[-5:]) / 5
            older_vol = sum(d[1] for d in data[-20:-5]) / 15
            if recent_vol > older_vol * 1.3:
                indicators["volume_trend"] = "increasing (bullish)"
            elif recent_vol < older_vol * 0.7:
                indicators["volume_trend"] = "decreasing (bearish)"
            else:
                indicators["volume_trend"] = "stable"

        return indicators

    def _ema(self, values: list, period: int) -> float:
        if len(values) < period:
            return values[-1] if values else 0
        multiplier = 2 / (period + 1)
        ema_val = sum(values[:period]) / period
        for price in values[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val
        return ema_val

    def _calculate_technical_score(self, ind: dict, eph: dict) -> float:
        """
        Гибридный скоринг: 85% technical + 15% астрология.
        """
        score = 50.0

        # RSI
        rsi = ind.get("rsi", 50)
        if rsi < 30:
            score += 20  # Oversold = bullish
        elif rsi < 40:
            score += 10
        elif rsi > 70:
            score -= 20  # Overbought = bearish
        elif rsi > 60:
            score -= 10

        # MACD histogram
        macd_hist = ind.get("macd", {}).get("histogram", 0)
        if macd_hist > 0:
            score += 15
        else:
            score -= 15

        # Bollinger position
        bb_pos = ind.get("bollinger", {}).get("position", 0.5)
        if bb_pos < 0.2:
            score += 15  # Near lower band = oversold
        elif bb_pos > 0.8:
            score += 15  # Near upper band = overbought warning
        elif bb_pos < 0.4:
            score += 5
        elif bb_pos > 0.6:
            score -= 5

        # Volume
        vol = ind.get("volume_trend", "stable")
        if "increasing" in vol:
            score += 5
        elif "decreasing" in vol:
            score -= 5

        # Астрологический бонус (15%)
        astro_score = eph.get("score", 50)
        astro_bonus = (astro_score - 50) * 0.3

        return max(0, min(100, score + astro_bonus))

    def _get_astro_influence(self, eph: dict) -> str:
        return f"Yoga: {eph.get('yoga', 'unknown')}, score: {eph.get('score', 50)}"

    def _build_reasoning(self, ind: dict, score: float) -> str:
        parts = []
        rsi = ind.get("rsi")
        if rsi:
            label = "oversold" if rsi < 40 else "overbought" if rsi > 60 else "neutral"
            parts.append(f"RSI(14)={rsi:.1f} ({label})")
        macd = ind.get("macd", {}).get("histogram")
        if macd is not None:
            parts.append(f"MACD={'bullish' if macd > 0 else 'bearish'}")
        bb = ind.get("bollinger", {})
        if bb.get("position") is not None:
            pos = bb["position"]
            label = "lower" if pos < 0.3 else "upper" if pos > 0.7 else "middle"
            parts.append(f"BB: {label}")
        vol = ind.get("volume_trend")
        if vol:
            parts.append(f"Vol: {vol}")
        parts.append(f"Tech score={score:.0f}/100")
        return ", ".join(parts)


async def run_technical_agent(state: dict) -> dict:
    """Runner для оркестратора."""
    agent = TechnicalAgent()
    result = await agent.run(state)
    return {"technical_signal": result.to_dict()}


def create() -> TechnicalAgent:
    """Factory for 6-fn test contract."""
    return TechnicalAgent()

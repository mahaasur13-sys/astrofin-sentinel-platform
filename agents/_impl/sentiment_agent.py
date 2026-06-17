"""
Sentiment Agent — fear/greed and market sentiment analysis.
"""

from __future__ import annotations

import logging

import httpx

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent[AgentResponse]):
    """
    SentimentAgent — анализ настроений рынка.
    """

    def __init__(self):
        super().__init__(
            name="SentimentAgent",
            instructions_path=None,
            domain="trading",
            weight=0.02,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Analyze market sentiment.
        """
        symbol = state.get("symbol", "BTCUSDT")
        state.get("current_price", 50000)

        # Fetch multiple sentiment sources
        fear_greed = await self._fetch_fear_greed()
        funding_rate = await self._fetch_funding_rate(symbol)
        price_momentum = self._analyze_price_momentum(state)

        # Combine sentiment
        sentiment_score = fear_greed["score"] * 0.40 + funding_rate["score"] * 0.30 + price_momentum["score"] * 0.30

        if sentiment_score >= 0.65:
            signal = SignalDirection.LONG
            confidence = min(int(sentiment_score * 100 + 10), 75)
        elif sentiment_score <= 0.35:
            signal = SignalDirection.SHORT
            confidence = min(int((1 - sentiment_score) * 100 + 10), 75)
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 45

        reasoning = (
            f"Fear & Greed: {fear_greed['summary']}. "
            f"Funding rate: {funding_rate['summary']}. "
            f"Price momentum: {price_momentum['summary']}. "
            f"Sentiment score: {sentiment_score:.2f}"
        )

        return AgentResponse(
            agent_name="SentimentAgent",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["trading/sentiment.md"],
            metadata={
                "sentiment_score": sentiment_score,
                "fear_greed": fear_greed,
                "funding_rate": funding_rate,
                "price_momentum": price_momentum,
            },
        )

    @track_agent_metrics
    async def run(self, state: dict) -> AgentResponse:
        """Public entry point. Wraps analyze() with the latency histogram and defensive error handling."""
        try:
            return await self.analyze(state)
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:
            return self._degraded(UNKNOWN, repr(e))

    async def _fetch_fear_greed(self) -> dict:
        """Fetch Fear & Greed Index asynchronously."""
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=5)
                data = resp.json()

                if data and "data" in data and len(data["data"]) > 0:
                    fng_value = int(data["data"][0]["value"])
                    fng_class = data["data"][0]["value_classification"]

                    score = fng_value / 100.0

                    if fng_value <= 20:
                        summary = f"Extreme Fear ({fng_value}) — contrarian BUY signal"
                    elif fng_value >= 80:
                        summary = f"Extreme Greed ({fng_value}) — contrarian SELL signal"
                    else:
                        summary = f"Fear & Greed: {fng_value} ({fng_class})"

                    return {"score": score, "summary": summary, "raw_value": fng_value}

        except Exception as e:
            logger.warning(f"[SentimentAgent] Failed to fetch Fear & Greed: {e}")

        return {
            "score": 0.5,
            "summary": "Fear & Greed data unavailable",
            "raw_value": 50,
        }

    async def _fetch_funding_rate(self, symbol: str = "BTCUSDT") -> dict:
        """Fetch funding rate from Bybit asynchronously."""
        url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)

                if resp.status_code != 200:
                    logger.warning(f"[SentimentAgent] HTTP {resp.status_code} from Bybit")
                    return {
                        "score": 0.5,
                        "summary": f"HTTP {resp.status_code}",
                        "raw_rate": 0.0,
                    }

                data = resp.json()
                funding_rate = float(data.get("result", {}).get("list", [{}])[0].get("fundingRate", 0.0))

                if funding_rate > 0.001:
                    score = 0.65
                    summary = f"Positive funding ({funding_rate * 100:.3f}%) — bullish"
                elif funding_rate > 0:
                    score = 0.57
                    summary = f"Slight positive funding ({funding_rate * 100:.3f}%)"
                elif funding_rate < -0.0005:
                    score = 0.35
                    summary = f"Negative funding ({funding_rate * 100:.3f}%) — bearish"
                elif funding_rate < 0:
                    score = 0.43
                    summary = f"Slight negative funding ({funding_rate * 100:.3f}%)"
                else:
                    score = 0.50
                    summary = f"Neutral funding rate ({funding_rate * 100:.4f}%)"

                return {"score": score, "summary": summary, "raw_rate": funding_rate}

        except Exception as e:
            logger.warning(f"[SentimentAgent] Failed to fetch funding rate for {symbol}: {e}")

        return {"score": 0.5, "summary": "Funding rate unavailable", "raw_rate": 0.0}

    def _analyze_price_momentum(self, state: dict) -> dict:
        """Analyze price momentum as sentiment proxy."""
        state.get("current_price", 50000)
        price_data = state.get("_price_data", [])

        if len(price_data) < 20:
            return {"score": 0.5, "summary": "insufficient momentum data"}

        closes = [d[0] for d in price_data]

        mom_7 = (closes[-1] - closes[-7]) / closes[-7] if len(closes) >= 7 else 0
        mom_14 = (closes[-1] - closes[-14]) / closes[-14] if len(closes) >= 14 else 0
        mom_30 = (closes[-1] - closes[-30]) / closes[-30] if len(closes) >= 30 else 0

        avg_momentum = (mom_7 + mom_14 + mom_30) / 3

        if avg_momentum > 0.05:
            score = 0.70
            summary = f"Strong positive momentum ({avg_momentum * 100:.1f}% avg)"
        elif avg_momentum > 0.02:
            score = 0.58
            summary = f"Mild positive momentum ({avg_momentum * 100:.1f}% avg)"
        elif avg_momentum < -0.05:
            score = 0.30
            summary = f"Strong negative momentum ({avg_momentum * 100:.1f}% avg)"
        elif avg_momentum < -0.02:
            score = 0.42
            summary = f"Mild negative momentum ({avg_momentum * 100:.1f}% avg)"
        else:
            score = 0.50
            summary = f"Neutral momentum ({avg_momentum * 100:.1f}% avg)"

        return {"score": score, "summary": summary, "momentum": avg_momentum}


async def run_sentiment_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = SentimentAgent()
    result = await agent.analyze(state)
    return {"sentiment_signal": result.to_dict()}

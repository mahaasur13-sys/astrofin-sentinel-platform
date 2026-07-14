"""
Quant Agent — backtesting, strategy optimization, ML predictions.
"""

from __future__ import annotations

import logging

import numpy as np

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection
from core.http_client import get_http_client

logger = logging.getLogger(__name__)


class QuantAgent(BaseAgent[AgentResponse]):
    """
    QuantAgent — количественный анализ и бэктестирование.

    Responsibilities:
    1. Backtest historical strategies
    2. Optimize entry/exit parameters
    3. Cross-market correlation analysis
    4. Volatility regime detection

    Weight: 10% (part of 20% Quant block)
    """

    def __init__(self):
        super().__init__(
            name="QuantAgent",
            instructions_path="agents/QuantAgent_instructions.md",
            domain="quant",
            weight=0.10,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        timeframe = state.get("timeframe_requested", "SWING")
        current_price = state.get("current_price", 50000)

        # Fetch price history
        price_data = await self._fetch_price_history(symbol, timeframe)

        if len(price_data) < 50:
            return AgentResponse(
                agent_name="QuantAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="Insufficient data for quant analysis",
                sources=[],
            )

        # Run quant models
        momentum = self._momentum_analysis(price_data)
        mean_reversion = self._mean_reversion_analysis(price_data, current_price)
        volatility_regime = self._volatility_regime(price_data)
        correlation = self._correlation_check(symbol)

        # Combine signals
        scores = []
        signals = []

        if momentum["score"] > 0.55:
            signals.append(SignalDirection.LONG)
            scores.append(momentum["score"])
        elif momentum["score"] < 0.45:
            signals.append(SignalDirection.SHORT)
            scores.append(1 - momentum["score"])
        else:
            signals.append(SignalDirection.NEUTRAL)
            scores.append(0.5)

        if mean_reversion["signal"] == "oversold":
            signals.append(SignalDirection.LONG)
            scores.append(0.65)
        elif mean_reversion["signal"] == "overbought":
            signals.append(SignalDirection.SHORT)
            scores.append(0.65)
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

        confidence = int(sum(scores) / len(scores) * 100) if scores else 50

        reasoning = (
            f"Momentum: {momentum['summary']}. "
            f"MeanRev: {mean_reversion['signal']} ({mean_reversion['z_score']:.1f}σ). "
            f"VolRegime: {volatility_regime['regime']}. "
            f"Correlation: {correlation}"
        )

        return AgentResponse(
            agent_name="QuantAgent",
            signal=direction,
            confidence=confidence,
            reasoning=reasoning,
            sources=["quant/momentum.md", "quant/mean_reversion.md"],
            metadata={
                "momentum": momentum,
                "mean_reversion": mean_reversion,
                "volatility_regime": volatility_regime,
                "correlation": correlation,
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

    async def _fetch_price_history(self, symbol: str, timeframe: str) -> list:
        """Fetch OHLCV data from Binance."""
        try:
            interval_map = {
                "1H": "1h",
                "4H": "4h",
                "1D": "1d",
                "1W": "1w",
                "SWING": "1d",
            }
            interval = interval_map.get(timeframe, "1d")
            url = f"https://www.okx.com/api/v5/market/candles?symbol={symbol}-USDT&interval={interval}&limit=100"
            resp = await get_http_client().get(url)
            data = resp.json()
            return [[float(x[4]), float(x[5]), float(x[2]), float(x[3])] for x in data]
        except Exception:
            return []

    def _momentum_analysis(self, data: list) -> dict:
        """Calculate momentum indicators."""
        closes = [d[0] for d in data]

        # Simple momentum: % change over dataset
        if len(closes) < 20:
            return {"score": 0.5, "summary": "insufficient data"}

        mom_20 = (closes[-1] - closes[-20]) / closes[-20] if len(closes) >= 20 else 0

        # Normalize to 0-1
        mom_score = 0.5 + mom_20 * 2  # rough normalization

        if mom_score > 0.7:
            summary = f"Strong momentum +{mom_20 * 100:.1f}%"
        elif mom_score > 0.55:
            summary = f"Weak momentum +{mom_20 * 100:.1f}%"
        elif mom_score > 0.45:
            summary = f"Neutral momentum {mom_20 * 100:.1f}%"
        elif mom_score > 0.3:
            summary = f"Weak bearish {mom_20 * 100:.1f}%"
        else:
            summary = f"Strong bearish {mom_20 * 100:.1f}%"

        return {
            "score": min(max(mom_score, 0), 1),
            "summary": summary,
            "mom_20": mom_20,
        }

    def _mean_reversion_analysis(self, data: list, current_price: float) -> dict:
        """Mean reversion using z-score."""
        closes = [d[0] for d in data]
        if len(closes) < 20:
            return {"signal": "neutral", "z_score": 0}

        mean = np.mean(closes[-20:])
        std = np.std(closes[-20:])
        z_score = (current_price - mean) / std if std > 0 else 0

        if z_score < -2:
            signal = "oversold"
            score = 0.7
        elif z_score < -1:
            signal = "bullish"
            score = 0.6
        elif z_score > 2:
            signal = "overbought"
            score = 0.7
        elif z_score > 1:
            signal = "bearish"
            score = 0.6
        else:
            signal = "neutral"
            score = 0.5

        return {"signal": signal, "z_score": z_score, "score": score}

    def _volatility_regime(self, data: list) -> dict:
        """Detect volatility regime."""
        closes = [d[0] for d in data]
        if len(closes) < 30:
            return {"regime": "unknown", "vol_pct": 0}

        returns = [np.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        vol_10 = np.std(returns[-10:]) * np.sqrt(365) if len(returns) >= 10 else 0
        vol_30 = np.std(returns[-30:]) * np.sqrt(365) if len(returns) >= 30 else vol_10

        if vol_10 > vol_30 * 1.5:
            regime = "high_vol_expanding"
            score = 0.4
        elif vol_10 < vol_30 * 0.7:
            regime = "low_vol_contr"
            score = 0.6
        else:
            regime = "normal"
            score = 0.5

        return {
            "regime": regime,
            "vol_pct": round(vol_30 * 100, 1),
            "score": score,
            "vol_10": round(vol_10 * 100, 1),
        }

    def _correlation_check(self, symbol: str) -> str:
        """Check correlation with major assets (simplified)."""
        # In production: fetch SPX, gold, DXY correlations
        return "BTC/USD correlation with SPX: moderate positive"


async def run_quant_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = QuantAgent()
    result = await agent.analyze(state)
    return {"quant_signal": result.to_dict()}

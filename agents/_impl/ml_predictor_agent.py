"""
ML Predictor Agent — ML-based price prediction and volatility forecasting.
"""

from __future__ import annotations

import logging

import numpy as np

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class MLPredictorAgent(BaseAgent[AgentResponse]):
    """
    MLPredictorAgent — ML-предсказания волатильности и направления.

    Responsibilities:
    1. Predict price direction using ML models
    2. Forecast volatility regimes
    3. Generate confidence intervals
    4. Optimize position sizing based on prediction confidence

    Weight: 10% (part of 20% Quant/AI block)
    """

    def __init__(self):
        super().__init__(
            name="MLPredictorAgent",
            instructions_path="agents/MLPredictorAgent_instructions.md",
            domain="quant",
            weight=0.10,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        timeframe = state.get("timeframe_requested", "SWING")
        current_price = state.get("current_price", 50000)

        # Fetch data
        price_data = await self._fetch_price_data(symbol, timeframe)

        if len(price_data) < 50:
            return AgentResponse(
                agent_name="MLPredictorAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="Insufficient data for ML prediction",
                sources=[],
            )

        # Run ML models
        direction_pred = self._predict_direction(price_data)
        volatility_pred = self._predict_volatility(price_data)
        confidence_interval = self._confidence_interval(price_data, current_price)

        # Combine predictions
        if direction_pred["direction"] == "up":
            direction = SignalDirection.LONG
            confidence = direction_pred["confidence"]
        elif direction_pred["direction"] == "down":
            direction = SignalDirection.SHORT
            confidence = direction_pred["confidence"]
        else:
            direction = SignalDirection.NEUTRAL
            confidence = 40

        reasoning = (
            f"ML Direction: {direction_pred['direction']} ({direction_pred['confidence']:.0%}). "
            f"Vol Prediction: {volatility_pred['regime']}. "
            f"95% CI: [{confidence_interval['lower']:.0f} - {confidence_interval['upper']:.0f}]"
        )

        return AgentResponse(
            agent_name="MLPredictorAgent",
            signal=direction,
            confidence=confidence,
            reasoning=reasoning,
            sources=["quant/ml_predictions.md"],
            metadata={
                "direction": direction_pred,
                "volatility": volatility_pred,
                "confidence_interval": confidence_interval,
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

    async def _fetch_price_data(self, symbol: str, timeframe: str) -> list:
        """Fetch price data for ML model."""
        try:
            interval_map = {
                "1H": "1h",
                "4H": "4h",
                "1D": "1d",
                "1W": "1w",
                "SWING": "1d",
            }
            interval = interval_map.get(timeframe, "1d")
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
            data = get_json(url) or []
            return [float(x[4]) for x in data]  # close prices
        except Exception:
            return []

    def _predict_direction(self, prices: list) -> dict:
        """
        Simple ML-like prediction using momentum and moving average crossover.
        In production: use sklearn, TensorFlow, or PyTorch models.
        """
        if len(prices) < 50:
            return {"direction": "neutral", "confidence": 0.4}

        # Features
        ma_short = np.mean(prices[-10:])
        ma_medium = np.mean(prices[-30:])
        ma_long = np.mean(prices[-50:])

        current = prices[-1]

        # Signals from MA crossover
        if ma_short > ma_medium > ma_long:
            direction = "up"
            confidence = 65
        elif ma_short < ma_medium < ma_long:
            direction = "down"
            confidence = 65
        elif ma_short > ma_medium:
            direction = "up"
            confidence = 55
        elif ma_short < ma_medium:
            direction = "down"
            confidence = 55
        else:
            direction = "neutral"
            confidence = 45

        # Distance from MAs (overbought/oversold)
        if current > ma_short * 1.05:
            confidence = min(confidence - 0.05, 0.6)  # slightly overextended
        elif current < ma_short * 0.95:
            confidence = min(confidence + 0.05, 0.7)  # oversold bounce

        return {"direction": direction, "confidence": confidence}

    def _predict_volatility(self, prices: list) -> dict:
        """Predict volatility regime."""
        if len(prices) < 30:
            return {"regime": "unknown", "forecast": 0}

        returns = np.diff(np.log(prices))
        vol_current = np.std(returns[-10:]) * np.sqrt(365)
        vol_historical = np.std(returns[-30:]) * np.sqrt(365)

        if vol_current > vol_historical * 1.5:
            regime = "expanding"
            forecast = vol_current
        elif vol_current < vol_historical * 0.7:
            regime = "contracting"
            forecast = vol_current
        else:
            regime = "stable"
            forecast = vol_current

        return {"regime": regime, "forecast_pct": round(forecast * 100, 1)}

    def _confidence_interval(self, prices: list, current_price: float) -> dict:
        """Calculate 95% confidence interval."""
        if len(prices) < 20:
            return {"lower": current_price * 0.95, "upper": current_price * 1.05}

        returns = np.diff(np.log(prices))
        std = np.std(returns[-30:])

        # 95% CI assuming normal distribution
        z = 1.96
        lower = current_price * np.exp(-z * std)
        upper = current_price * np.exp(z * std)

        return {
            "lower": lower,
            "upper": upper,
            "width_pct": round((upper - lower) / current_price * 100, 1),
        }


async def run_ml_predictor_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = MLPredictorAgent()
    result = await agent.analyze(state)
    return {"ml_predictor_signal": result.to_dict()}

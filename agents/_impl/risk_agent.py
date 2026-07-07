"""
Risk Agent — position sizing and risk management.
"""

from __future__ import annotations

import logging

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent[AgentResponse]):
    """
    RiskAgent — управление рисками и размером позиции.

    Responsibilities:
    1. Calculate optimal position size based on volatility
    2. Determine max drawdown tolerance
    3. Set stop-loss levels based on ATR
    4. Validate risk/reward ratio

    Weight: 5% (minor agent)
    """

    def __init__(self):
        super().__init__(
            name="RiskAgent",
            instructions_path=None,
            domain="trading",
            weight=0.05,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Calculate risk parameters and position sizing.
        """
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        price_data = await self._fetch_ohlcv(symbol, "1d", 30)
        if not price_data:
            return AgentResponse(
                agent_name="RiskAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=25,
                reasoning="No market data for risk calculation",
                sources=[],
            )

        # Calculate ATR for stop-loss
        atr = self._calculate_atr(price_data, period=14)
        volatility = atr / current_price

        # Position sizing (Kelly Criterion simplified)
        win_rate = state.get("win_rate_estimate", 0.55)
        avg_win = state.get("avg_win_pct", 0.03)
        avg_loss = state.get("avg_loss_pct", 0.015)

        position_size = self._calc_position_size(volatility=volatility, win_rate=win_rate, avg_win=avg_win, avg_loss=avg_loss)

        # Stop-loss calculation
        stop_distance = atr * 1.5
        stop_loss = current_price - stop_distance if stop_distance > 0 else current_price * 0.97

        # Risk assessment
        risk_score = self._assess_risk(
            volatility=volatility,
            position_size=position_size,
            atr=atr,
            current_price=current_price,
        )

        if risk_score > 0.7:
            signal = SignalDirection.AVOID
            confidence = 70
        elif risk_score > 0.5:
            signal = SignalDirection.NEUTRAL
            confidence = 50
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 60

        reasoning = (
            f"ATR(14): ${atr:,.2f} ({volatility * 100:.2f}% of price). "
            f"Volatility: {'high' if volatility > 0.03 else 'moderate' if volatility > 0.015 else 'low'}. "
            f"Recommended position: {position_size * 100:.1f}% of capital. "
            f"Stop-loss: ${stop_loss:,.2f} ({((current_price - stop_loss) / current_price) * 100:.1f}% below). "
            f"Risk score: {risk_score:.2f}"
        )

        return AgentResponse(
            agent_name="RiskAgent",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["trading/risk_management.md"],
            metadata={
                "atr": atr,
                "volatility": volatility,
                "position_size_recommended": position_size,
                "stop_loss": stop_loss,
                "risk_score": risk_score,
                "symbol": symbol,
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

    def _calculate_atr(self, data: list, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(data) < period + 1:
            return data[-1][2] * 0.02 if data else 100

        true_ranges = []
        for i in range(1, len(data)):
            high = data[i][0]
            low = data[i][1]
            prev_close = data[i - 1][2]

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)

        return sum(true_ranges[-period:]) / period

    def _calc_position_size(self, volatility: float, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate position size using simplified Kelly + volatility adjustment.
        """
        # Kelly fraction
        if avg_loss == 0 or win_rate == 0:
            kelly = 0.10
        else:
            win_loss_ratio = avg_win / avg_loss
            kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
            kelly = max(0.01, min(kelly, 0.20))  # Cap at 20%

        # Volatility adjustment
        if volatility > 0.05:
            kelly *= 0.5
        elif volatility > 0.03:
            kelly *= 0.75

        return kelly

    def _assess_risk(self, volatility: float, position_size: float, atr: float, current_price: float) -> float:
        """Assess overall risk score (0-1, higher = more risky)."""
        risk = 0.3

        # Volatility risk
        if volatility > 0.05:
            risk += 0.30
        elif volatility > 0.03:
            risk += 0.15

        # Position size risk
        if position_size > 0.15:
            risk += 0.25
        elif position_size > 0.10:
            risk += 0.10

        # ATR-based stop distance
        stop_pct = (atr * 1.5) / current_price
        if stop_pct > 0.05:
            risk += 0.15
        elif stop_pct > 0.03:
            risk += 0.08

        return min(risk, 1.0)


async def run_risk_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = RiskAgent()
    result = await agent.analyze(state)
    return {"risk_signal": result.to_dict()}


def create() -> RiskAgent:
    """Factory for 6-fn test contract."""
    return RiskAgent()

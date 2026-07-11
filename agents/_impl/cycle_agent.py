"""
Cycle Agent — market timing cycles analysis.
"""

from __future__ import annotations

import logging
from datetime import datetime

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


class CycleAgent(BaseAgent[AgentResponse]):
    """
    CycleAgent — анализ рыночных циклов.

    Responsibilities:
    1. Detect dominant cycle periods (20, 40, 80 days)
    2. Identify cycle phase (up/down/transition)
    3. Predict cycle turning points
    4. Align with astro cycles (Jupiter 12yr, Saturn 29yr)

    Weight: 5% (minor agent)
    """

    def __init__(self):
        super().__init__(
            name="CycleAgent",
            instructions_path=None,
            domain="technical",
            weight=0.05,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Analyze cycle position and predict next turning point.
        """
        symbol = state.get("symbol", "BTCUSDT")
        state.get("current_price", 50000)

        price_data = await self._fetch_ohlcv(symbol, "1d", 120)
        if not price_data:
            return AgentResponse(
                agent_name="CycleAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=25,
                reasoning="No market data for cycle analysis",
                sources=[],
            )

        # Detect dominant cycle
        dominant_cycle = self._find_dominant_cycle(price_data)
        cycle_phase = self._get_cycle_phase(price_data, dominant_cycle)
        next_turn = self._predict_turning_point(price_data, dominant_cycle, cycle_phase)
        astro_cycles = await self._check_astro_cycles(state)

        # Cycle alignment score
        cycle_score = cycle_phase["strength"] * 0.6 + astro_cycles["score"] * 0.4

        if cycle_phase["direction"] == "up" and cycle_score > 0.55:
            signal = SignalDirection.LONG
            confidence = min(int(cycle_score * 100 + 10), 75)
        elif cycle_phase["direction"] == "down" and cycle_score > 0.55:
            signal = SignalDirection.SHORT
            confidence = min(int(cycle_score * 100 + 10), 75)
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 40

        reasoning = (
            f"Dominant cycle: {dominant_cycle['period']} days "
            f"(strength: {cycle_phase['strength']:.0%}). "
            f"Phase: {cycle_phase['name']} ({cycle_phase['direction']}). "
            f"Next turn: {next_turn['direction']} in {next_turn['eta_days']:.0f} days. "
            f"Astro cycles: {astro_cycles['summary']}. "
            f"Cycle score: {cycle_score:.2f}"
        )

        return AgentResponse(
            agent_name="CycleAgent",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["technical/cycles.md", "astrology/planetary_cycles.md"],
            metadata={
                "dominant_cycle": dominant_cycle,
                "cycle_phase": cycle_phase,
                "next_turning_point": next_turn,
                "astro_cycles": astro_cycles,
                "cycle_score": cycle_score,
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

    def _find_dominant_cycle(self, data: list) -> dict:
        """Find dominant cycle period using autocorrelation."""
        if len(data) < 40:
            return {"period": 20, "strength": 0.4, "method": "insufficient_data"}

        closes = [d[0] for d in data]

        # Simplified cycle detection — find dominant periodicity
        # Check autocorrelation at different lags
        test_periods = [20, 30, 40, 60, 80]
        best_period = 20
        best_corr = -1

        mean = sum(closes) / len(closes)
        var = sum((c - mean) ** 2 for c in closes)

        for period in test_periods:
            if period >= len(closes) // 2:
                continue
            # Calculate autocorrelation at lag=period
            corr_sum = sum((closes[i] - mean) * (closes[i - period] - mean) for i in range(period, len(closes)))
            corr = corr_sum / var if var > 0 else 0

            if corr > best_corr:
                best_corr = corr
                best_period = period

        return {
            "period": best_period,
            "strength": min(abs(best_corr), 1.0),
            "method": "autocorrelation",
        }

    def _get_cycle_phase(self, data: list, dominant_cycle: dict) -> dict:
        """Determine current phase within the cycle."""
        if len(data) < dominant_cycle["period"]:
            return {"name": "unknown", "direction": "neutral", "strength": 0.4}

        period = dominant_cycle["period"]
        closes = [d[0] for d in data]

        # Find position in cycle (0 = start/bottom, 0.5 = top)
        recent = closes[-period:] if len(closes) >= period else closes
        oldest = recent[0]
        newest = recent[-1]

        # Simple phase detection
        mid_point = (max(recent) + min(recent)) / 2

        # Detect direction
        if newest > oldest:
            direction = "up"
            # Transition check
            if newest > mid_point:
                phase_name = "late_stage"
                strength = 0.7
            else:
                phase_name = "early_stage"
                strength = 0.6
        else:
            direction = "down"
            if newest < mid_point:
                phase_name = "late_stage"
                strength = 0.7
            else:
                phase_name = "early_stage"
                strength = 0.6

        return {"name": phase_name, "direction": direction, "strength": strength}

    def _predict_turning_point(self, data: list, dominant_cycle: dict, cycle_phase: dict) -> dict:
        """Predict next cycle turning point."""
        period = dominant_cycle["period"]

        # Rough estimate — next turning point is ~quarter cycle away
        if cycle_phase["direction"] == "up":
            next_direction = "down"
            eta_days = period // 4
        else:
            next_direction = "up"
            eta_days = period // 4

        return {
            "direction": next_direction,
            "eta_days": eta_days,
            "confidence": cycle_phase["strength"] * 0.8,
        }

    async def _check_astro_cycles(self, state: dict) -> dict:
        """Check planetary cycles alignment."""
        from core.ephemeris import HAS_SWISS_EPHEMERIS, _julian_day, calculate_planet

        if not HAS_SWISS_EPHEMERIS:
            return {"score": 0.5, "summary": "ephemeris unavailable"}

        now = datetime.utcnow()
        jd = _julian_day(now)

        # Jupiter cycle (12 years — check position in zodiac)
        jupiter = calculate_planet("jupiter", jd)
        int(jupiter.longitude / 30)

        # Saturn cycle (29 years)
        saturn = calculate_planet("saturn", jd)
        int(saturn.longitude / 30)

        # Cycle alignment scoring
        # Trine aspects (120°) are bullish for cycles
        angle = abs(jupiter.longitude - saturn.longitude) % 360
        is_trine = 115 <= angle <= 125
        is_opposition = 175 <= angle <= 185

        if is_trine:
            score = 0.70
            summary = "Jupiter-Saturn trine (120°)"
        elif is_opposition:
            score = 0.55
            summary = "Jupiter-Saturn opposition (180°)"
        else:
            score = 0.45
            summary = f"Jupiter-Saturn angle: {angle:.0f}°"

        return {"score": score, "summary": summary}


async def run_cycle_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = CycleAgent()
    result = await agent.analyze(state)
    return {"cycle_signal": result.to_dict()}


def create() -> CycleAgent:
    """Factory for 6-fn test contract."""
    return CycleAgent()

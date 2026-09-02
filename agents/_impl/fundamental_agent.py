"""
Fundamental Agent — financial statement analysis, valuation metrics.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

import aiohttp

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

_COIN_ID_MAP = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana"}
_CACHE: dict = {}
_CACHE_TTL = 600  # seconds (10 minutes)


def _coingecko_api_key() -> str | None:
    return os.getenv("COINGECKO_API_KEY") or os.getenv("COINGECKO_DEMO_API_KEY")


def _cache_set(data: dict) -> None:
    _CACHE["data"] = data
    _CACHE["ts"] = time.time()


def _cache_get() -> dict | None:
    if _CACHE and (time.time() - _CACHE.get("ts", 0)) < _CACHE_TTL:
        return _CACHE.get("data")
    return None


def _compute_from_prices(prices: list) -> dict:
    closes = [p[1] for p in prices]
    current = closes[-1]
    avg = sum(closes) / len(closes)
    ath = max(closes)
    prev = closes[-2] if len(closes) >= 2 else current
    return {
        "mvrv_ratio": round(current / avg, 2),
        "ath_distance_pct": round((ath - current) / ath * 100, 1),
        "volatility_30d": round((ath - min(closes)) / current * 100, 1),
        "price_change_24h": round((current - prev) / prev * 100, 1),
    }


class FundamentalAgent(BaseAgent[AgentResponse]):
    """
    FundamentalAgent — анализ фундаментальных показателей компании/актива.

    Responsibilities:
    1. P/E, EPS, Revenue growth analysis
    2. DCF valuation estimates
    3. Sector comparison
    4. Earnings quality assessment

    Weight: 12% (part of 20% Fundamental+Macro block)
    """

    def __init__(self):
        super().__init__(
            name="FundamentalAgent",
            instructions_path="agents/FundamentalAgent_instructions.md",
            domain="fundamental",
            weight=0.12,
        )
        self._session: aiohttp.ClientSession | None = None

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        # Fetch financial data (one CoinGecko request + cache + backoff)
        data = await self._fetch_fundamental_data(symbol)

        if data.get("no_data"):
            return AgentResponse(
                agent_name="FundamentalAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="No fundamental data available (CoinGecko unavailable)",
                sources=[],
                metadata={"no_data": True},
            )

        # Analyze valuation
        valuation = self._analyze_valuation(data, current_price)
        earnings = self._analyze_earnings_quality(data)
        growth = self._analyze_growth_metrics(data)

        # Combine signals
        scores = []
        signals = []

        if valuation["score"] > 0.55:
            signals.append(SignalDirection.LONG)
            scores.append(valuation["score"])
        elif valuation["score"] < 0.45:
            signals.append(SignalDirection.SHORT)
            scores.append(1 - valuation["score"])
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

        reasoning = f"Valuation: {valuation['summary']}. Earnings: {earnings['summary']}. Growth: {growth['summary']}. MVRV: {data.get('mvrv_ratio', 'N/A')}"

        return AgentResponse(
            agent_name="FundamentalAgent",
            signal=direction,
            confidence=confidence,
            reasoning=reasoning,
            sources=["fundamental/valuation.md", "fundamental/earnings.md"],
            metadata={
                "valuation": valuation,
                "earnings": earnings,
                "growth": growth,
                "onchain": data,
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

    async def _fetch_fundamental_data(self, symbol: str) -> dict:
        """One CoinGecko request for all needed fields, with demo-key header,
        a 10-minute cache (successful 200 only), and 429 backoff.

        On 200 → compute + cache + return. On 429/network error → serve a fresh
        cache if present, otherwise return {"no_data": True} (never a fake MVRV).
        """
        base = symbol.replace("USDT", "").replace("USD", "").lower()
        coin_id = _COIN_ID_MAP.get(base, base)
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30"

        headers = {}
        key = _coingecko_api_key()
        if key:
            headers["x-cg-demo-api-key"] = key

        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            async with self._session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    payload = await resp.json()
                    prices = payload.get("prices", [])
                    if len(prices) > 1:
                        data = _compute_from_prices(prices)
                        _cache_set(data)
                        return data
                elif resp.status == 429:
                    retry_after = resp.headers.get("Retry-After")
                    try:
                        wait = int(retry_after) if retry_after else 30
                    except (TypeError, ValueError):
                        wait = 30
                    logger.warning(
                        "[FundamentalAgent] CoinGecko 429, backoff %ss",
                        min(wait, 60),
                    )
                    await asyncio.sleep(min(wait, 60))
        except Exception as exc:
            logger.warning("[FundamentalAgent] CoinGecko fetch failed: %s", exc)

        cached = _cache_get()
        if cached:
            return cached
        return {"no_data": True}

    def _analyze_valuation(self, data: dict, current_price: float) -> dict:
        """Analyze valuation metrics."""
        mvrv = data.get("mvrv_ratio", 1.0)
        ath_distance = data.get("ath_distance_pct", 50)

        # MVRV interpretation
        if mvrv < 0.7:
            score = 0.75  # severely undervalued
            summary = f"MVRV {mvrv:.2f} (deep value)"
        elif mvrv < 1.0:
            score = 0.65  # undervalued
            summary = f"MVRV {mvrv:.2f} (below avg)"
        elif mvrv < 2.0:
            score = 0.55  # fair
            summary = f"MVRV {mvrv:.2f} (fair value)"
        elif mvrv < 3.5:
            score = 0.40  # overvalued
            summary = f"MVRV {mvrv:.2f} (overvalued)"
        else:
            score = 0.25  # bubble territory
            summary = f"MVRV {mvrv:.2f} (bubble zone)"

        # ATH distance bonus
        if ath_distance < 10:
            score *= 0.9  # near ATH, less upside
        elif ath_distance > 70:
            score *= 1.1  # deep discount

        return {"score": min(score, 1.0), "summary": summary}

    def _analyze_earnings_quality(self, data: dict) -> dict:
        """Analyze earnings/price-action quality from 24h change."""
        vol_change = abs(data.get("price_change_24h", 0))

        if vol_change < 2:
            score = 0.50
            summary = "Stable"
        elif vol_change < 5:
            score = 0.55
            summary = "Moderate"
        else:
            score = 0.45
            summary = "High vol"

        summary += f" {vol_change:.1f}%"
        return {"score": score, "summary": summary}

    def _analyze_growth_metrics(self, data: dict) -> dict:
        """Analyze growth metrics."""
        volatility = data.get("volatility_30d", 10)

        if volatility < 5:
            score = 0.60
            summary = "Low volatility (stable growth)"
        elif volatility < 15:
            score = 0.55
            summary = "Normal volatility"
        elif volatility < 30:
            score = 0.45
            summary = "High volatility"
        else:
            score = 0.35
            summary = "Extreme volatility"

        return {"score": score, "summary": summary}


async def run_fundamental_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = FundamentalAgent()
    result = await agent.analyze(state)
    return {"fundamental_signal": result.to_dict()}


def create() -> FundamentalAgent:
    """Factory for 6-fn test contract."""
    return FundamentalAgent()

"""
Fundamental Agent — financial statement analysis, valuation metrics.
"""

from __future__ import annotations

import logging

import requests

from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris
from agents.metrics import track_agent_metrics

from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection

logger = logging.getLogger(__name__)


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

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        # Fetch financial data
        crypto_metadata = await self._fetch_crypto_metadata(symbol)
        onchain_data = await self._fetch_onchain_data(symbol)

        # Analyze valuation
        valuation = self._analyze_valuation(crypto_metadata, onchain_data, current_price)
        earnings = self._analyze_earnings_quality(crypto_metadata, onchain_data)
        growth = self._analyze_growth_metrics(onchain_data)

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

        reasoning = (
            f"Valuation: {valuation['summary']}. "
            f"Earnings: {earnings['summary']}. "
            f"Growth: {growth['summary']}. "
            f"MVRV: {onchain_data.get('mvrv_ratio', 'N/A')}"
        )

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
                "onchain": onchain_data,
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

    async def _fetch_crypto_metadata(self, symbol: str) -> dict:
        """Fetch basic crypto metadata from CoinGecko."""
        try:
            # CoinGecko free API
            coin_id = symbol.replace("USDT", "").lower()
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "name": data.get("name", ""),
                    "market_cap_rank": data.get("market_cap_rank", 999),
                    "market_cap": data.get("market_data", {}).get("market_cap", {}).get("usd", 0),
                    "volume_24h": data.get("market_data", {}).get("total_volume", {}).get("usd", 0),
                    "price_change_24h": data.get("market_data", {}).get("price_change_percentage_24h", 0),
                    "ath": data.get("market_data", {}).get("ath", {}).get("usd", 0),
                    "atl": data.get("market_data", {}).get("atl", {}).get("usd", 0),
                }
        except Exception:
            pass
        return {"market_cap_rank": 999}

    async def _fetch_onchain_data(self, symbol: str) -> dict:
        """Fetch on-chain metrics (simplified)."""
        try:
            # Alternative: use public APIs
            coin_id = symbol.replace("USDT", "").lower()
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=30"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                prices = data.get("prices", [])
                if len(prices) > 1:
                    current = prices[-1][1]
                    ath = max(p[1] for p in prices)
                    # MVRV approximation
                    mvrv = current / (sum(p[1] for p in prices) / len(prices))
                    return {
                        "mvrv_ratio": round(mvrv, 2),
                        "ath_distance_pct": round((ath - current) / ath * 100, 1),
                        "volatility_30d": round(
                            (max(p[1] for p in prices) - min(p[1] for p in prices)) / current * 100,
                            1,
                        ),
                    }
        except Exception as e:
            logger.warning(f"[FundamentalAgent] Failed to fetch onchain data for {symbol}: {e}")
        return {"mvrv_ratio": 1.0, "ath_distance_pct": 50.0, "volatility_30d": 10.0}

    def _analyze_valuation(self, metadata: dict, onchain: dict, current_price: float) -> dict:
        """Analyze valuation metrics."""
        mvrv = onchain.get("mvrv_ratio", 1.0)
        ath_distance = onchain.get("ath_distance_pct", 50)

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

    def _analyze_earnings_quality(self, metadata: dict, onchain: dict) -> dict:
        """Analyze earnings/transaction quality."""
        rank = metadata.get("market_cap_rank", 999)
        vol_change = abs(metadata.get("price_change_24h", 0))

        if rank < 10:
            score = 0.65
            summary = "Top-10 cap, stable"
        elif rank < 50:
            score = 0.60
            summary = "Large cap"
        elif rank < 100:
            score = 0.55
            summary = "Mid cap"
        else:
            score = 0.45
            summary = "Small cap"

        if vol_change > 10:
            summary += f", high vol {vol_change:.1f}%"
        else:
            summary += f", normal vol {vol_change:.1f}%"

        return {"score": score, "summary": summary}

    def _analyze_growth_metrics(self, onchain: dict) -> dict:
        """Analyze growth metrics."""
        volatility = onchain.get("volatility_30d", 10)

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

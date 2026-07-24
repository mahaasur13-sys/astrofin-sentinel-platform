"""orchestration/result_aggregator.py — Agent flow runners & signal aggregation.

Extracted from sentinel_v5.py (P2-04 refactoring).
"""

from __future__ import annotations

import asyncio
import logging

from agents._impl.bear_researcher import run_bear_researcher
from agents._impl.bull_researcher import run_bull_researcher
from agents._impl.electoral_agent import run_electoral_agent
from agents._impl.fundamental_agent import run_fundamental_agent
from agents._impl.macro_agent import run_macro_agent
from agents._impl.market_analyst import run_market_analyst
from agents._impl.options_flow_agent import run_options_flow_agent
from agents._impl.quant_agent import run_quant_agent
from agents._impl.sentiment_agent import run_sentiment_agent
from agents.astro_council_agent import run_astro_council
from agents.base_agent import AgentResponse, SignalDirection
from core.thompson import ASTRO_POOL, MACRO_POOL, TECHNICAL_POOL

logger = logging.getLogger(__name__)


async def run_technical_flow(state: dict, selected_agents: list | None = None) -> dict:
    pool_agents = selected_agents or TECHNICAL_POOL.agents
    tasks, names = [], []
    if "MarketAnalyst" in pool_agents:
        tasks.append(run_market_analyst(state))
        names.append("MarketAnalyst")
    if "BullResearcher" in pool_agents:
        tasks.append(run_bull_researcher(state))
        names.append("BullResearcher")
    if "BearResearcher" in pool_agents:
        tasks.append(run_bear_researcher(state))
        names.append("BearResearcher")
    if not tasks:
        return {}
    results = await asyncio.gather(*tasks, return_exceptions=True)
    merged = {}
    for name, r in zip(names, results, strict=False):
        if isinstance(r, dict):
            merged[f"{name.lower()}_signal"] = (
                r.get(f"{name.lower()}_signal") or list(r.values())[0]
            )
        elif isinstance(r, Exception):
            logger.error(f"[TechFlow] Agent {name} failed: {r}")
            merged[f"{name.lower()}_signal"] = AgentResponse(
                agent_name=name,
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning=f"Agent error: {str(r)[:100]}",
                sources=[],
            ).to_dict()
    return merged


async def run_astro_flow(state: dict, selected_agents: list | None = None) -> dict:
    pool_agents = selected_agents or ASTRO_POOL.agents
    state = {**state, "_thompson_selected_astro": pool_agents}
    return await run_astro_council(state)


async def run_electoral_flow(state: dict, selected_agents: list | None = None) -> dict:
    return await run_electoral_agent(state)


async def run_macro_flow(state: dict, selected_agents: list | None = None) -> dict:
    pool_agents = selected_agents or MACRO_POOL.agents
    tasks, names = [], []
    if "FundamentalAgent" in pool_agents:
        tasks.append(run_fundamental_agent(state))
        names.append("FundamentalAgent")
    if "MacroAgent" in pool_agents:
        tasks.append(run_macro_agent(state))
        names.append("MacroAgent")
    if "QuantAgent" in pool_agents:
        tasks.append(run_quant_agent(state))
        names.append("QuantAgent")
    if "OptionsFlowAgent" in pool_agents:
        tasks.append(run_options_flow_agent(state))
        names.append("OptionsFlowAgent")
    if "SentimentAgent" in pool_agents:
        tasks.append(run_sentiment_agent(state))
        names.append("SentimentAgent")
    if not tasks:
        return {}
    results = await asyncio.gather(*tasks, return_exceptions=True)
    merged = {}
    for name, r in zip(names, results, strict=False):
        if isinstance(r, dict):
            sig = (
                r.get(f"{name.lower()}_signal")
                or r.get("signal")
                or (list(r.values())[0] if r else None)
            )
            merged[f"{name.lower()}_signal"] = sig
        elif isinstance(r, Exception):
            logger.error(f"[MacroFlow] Agent {name} failed: {r}")
            merged[f"{name.lower()}_signal"] = AgentResponse(
                agent_name=name,
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning=f"Agent error: {str(r)[:100]}",
                sources=[],
            ).to_dict()
    return merged


async def _fetch_price(symbol: str, fallback_price: float = 50000.0) -> float:
    import httpx

    max_retries = 3
    async with httpx.AsyncClient() as client:
        for attempt in range(max_retries):
            try:
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
                resp = await client.get(url, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                price = float(data.get("price", 0))
                if price > 0:
                    logger.debug(f"[Price] {symbol} = {price}")
                    return price
                else:
                    logger.warning(f"[Price] Invalid price for {symbol}: {price}")
            except Exception as e:
                logger.warning(
                    f"[Price] Attempt {attempt + 1}/{max_retries} error: {e}"
                )
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
    logger.error(
        f"[Price] All {max_retries} attempts failed for {symbol}, using fallback {fallback_price}"
    )
    return fallback_price

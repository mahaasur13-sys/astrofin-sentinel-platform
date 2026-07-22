#!/usr/bin/env python3
"""AstroFin Sentinel v5 — Multi-Agent Orchestrator (KARL + Standard)."""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

from agents._impl.bear_researcher import run_bear_researcher
from agents._impl.bull_researcher import run_bull_researcher
from agents._impl.electoral_agent import run_electoral_agent
from agents._impl.fundamental_agent import run_fundamental_agent
from agents._impl.macro_agent import run_macro_agent
from agents._impl.market_analyst import run_market_analyst
from agents._impl.options_flow_agent import run_options_flow_agent
from agents._impl.quant_agent import run_quant_agent
from agents._impl.sentiment_agent import run_sentiment_agent
from agents._impl.synthesis_agent import SynthesisAgent
from agents.astro_council_agent import run_astro_council
from agents.base_agent import AgentResponse, SignalDirection
from agents.karl_synthesis import KARLSynthesisAgent
from core.belief import update_beliefs_from_session
from core.history_db import save_session
from core.thompson import (
    ASTRO_POOL,
    ELECTORAL_POOL,
    MACRO_POOL,
    TECHNICAL_POOL,
    AgentPool,
    get_thompson_sampler,
)
from orchestration.router import route_query

try:
    from db.session import init_db_if_needed

    PG_AVAILABLE = True
except Exception:
    PG_AVAILABLE = False

from agents._impl.amre.oap_optimizer import get_oap_optimizer

OAP_WEIGHTING_ENABLED = True

logger = logging.getLogger(__name__)

KARL_ENABLED = os.getenv("KARL_ENABLED", "true").lower() == "true"


def _compute_oap_adjustments(oap_state, agents: list) -> dict:
    if not hasattr(oap_state, "agent_stats") or not oap_state.agent_stats:
        if not agents:
            return {}
        entropy = getattr(oap_state, "entropy_avg", 0.5) or 0.5
        sharpe = getattr(oap_state, "sharpe_ratio", 0.0) or 0.0
        oap_score = 0.5 * entropy + 0.5 * max(0.0, sharpe)
        adjustment = (oap_score - 0.5) * 0.4
        logger.debug(f"[OAP] no per-agent stats — uniform adj={adjustment:+.3f}")
        return dict.fromkeys(agents, adjustment)
    adjustments = {}
    for agent_name in agents:
        stats = oap_state.agent_stats.get(agent_name)
        if stats is None:
            adjustments[agent_name] = 0.0
            continue
        try:
            entropy = getattr(stats, "entropy_contribution", 0.5) or 0.5
            sharpe = max(0.0, getattr(stats, "sharpe_contribution", 0.0) or 0.0)
            recent_q = getattr(stats, "recent_decision_quality", 0.5) or 0.5
            agent_score = entropy * 0.4 + sharpe * 0.4 + recent_q * 0.2
            adjustment = max(-0.25, min(0.25, (agent_score - 0.5) * 0.5))
            adjustments[agent_name] = adjustment
        except Exception:
            adjustments[agent_name] = 0.0
    return adjustments


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


def _select_for_flow(
    pool: AgentPool,
    excluded: list | None = None,
    k: int | None = None,
    oap_adjustments: dict | None = None,
) -> list:
    adj = oap_adjustments if OAP_WEIGHTING_ENABLED else None
    sampler = get_thompson_sampler()
    if excluded:
        selected = sampler.select_with_exclusions(
            pool, excluded=excluded, k=k, oap_adjustments=adj
        )
    else:
        selected = sampler.select(pool, k=k, oap_adjustments=adj)
    return [name for name, _ in selected]


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


async def run_sentinel_v5(
    user_query: str = "",
    symbol: str = "BTCUSDT",
    timeframe: str = "SWING",
    current_price: float = 0,
    birth_data: dict | None = None,
    include_technical: bool = True,
    include_astro: bool = True,
    include_electional: bool = False,
    include_macro: bool = True,
    thompson_k: int | None = None,
    persist: bool = True,
    session_id: str | None = None,
) -> dict:
    session_id = session_id or str(uuid.uuid4())[:8]

    route_output = route_query(user_query)
    logger.info(f"[Router] Query type: {route_output.query_type.value}")
    logger.info(f"[Router] Symbols: {route_output.symbols}")

    symbols = route_output.symbols or [symbol]
    timeframe = route_output.timeframe or timeframe

    if current_price == 0 and symbols:
        current_price = await _fetch_price(symbols[0])
    current_price = current_price or 50000

    state = {
        "symbol": symbols[0],
        "timeframe_requested": timeframe,
        "current_price": current_price,
        "birth_data": birth_data,
        "user_query": user_query,
        "session_id": session_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "all_signals": [],
    }

    thompson_selections: dict = {}
    technical_selected: list = []

    if include_technical:
        technical_selected = _select_for_flow(TECHNICAL_POOL, k=thompson_k)
        thompson_selections["technical"] = technical_selected
    if include_macro:
        macro_selected = _select_for_flow(
            MACRO_POOL, excluded=technical_selected, k=thompson_k
        )
        thompson_selections["macro"] = macro_selected
    if include_astro:
        astro_selected = _select_for_flow(
            ASTRO_POOL, excluded=technical_selected, k=thompson_k
        )
        thompson_selections["astro"] = astro_selected
    if include_electional:
        electoral_selected = _select_for_flow(ELECTORAL_POOL, k=1)
        thompson_selections["electoral"] = electoral_selected

    logger.info(f"[Thompson] technical: {technical_selected}")

    flow_tasks = []
    if include_technical:
        flow_tasks.append(run_technical_flow(state, selected_agents=technical_selected))
    if include_macro:
        flow_tasks.append(
            run_macro_flow(state, selected_agents=thompson_selections.get("macro", []))
        )
    if include_astro:
        flow_tasks.append(run_astro_flow(state, selected_agents=astro_selected))
    if include_electional:
        flow_tasks.append(run_electoral_flow(state))
    if flow_tasks:
        flow_results = await asyncio.gather(*flow_tasks, return_exceptions=True)
        for result in flow_results:
            if isinstance(result, dict):
                for key, value in result.items():
                    if key.endswith("_signal") and value is not None:
                        state["all_signals"].append(value)
        if not state["all_signals"]:
            logger.warning("[Sentinel] All agents failed — using SystemFallback")
            fallback_response = AgentResponse(
                agent_name="SystemFallback",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="All agents failed to produce a signal.",
            )
            state["all_signals"].append(fallback_response)

    synthesis_agent = SynthesisAgent()
    try:
        synthesis_result = await synthesis_agent.run(state)
    except Exception as e:
        logger.error(f"[SynthesisAgent] Skipped — agent unavailable: {e}")
        synthesis_result = None

    final_output = {
        "session_id": session_id,
        "symbol": symbols[0],
        "timeframe": timeframe,
        "current_price": current_price,
        "query_type": route_output.query_type.value,
        "flows_run": {
            "technical": include_technical,
            "astro": include_astro,
            "electional": include_electional,
            "macro": include_macro,
        },
        "thompson_selections": thompson_selections,
        "agent_count": len(state["all_signals"]),
        "final_recommendation": (
            synthesis_result.to_dict() if synthesis_result else None
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if persist:
        save_session(final_output)
        update_beliefs_from_session(final_output)

    logger.info(
        f"[Sentinel] Session {session_id} completed: {len(state['all_signals'])} signals"
    )
    return final_output


async def run_karl_sentinel_v5(
    user_query: str = "",
    symbol: str = "BTCUSDT",
    timeframe: str = "SWING",
    current_price: float = 0,
    birth_data: dict | None = None,
    include_technical: bool = True,
    include_astro: bool = True,
    include_electional: bool = False,
    include_macro: bool = True,
    thompson_k: int | None = None,
    persist: bool = True,
    sync_interval: int = 60,
    enable_self_question: bool = True,
    enable_backtest: bool = True,
    session_id: str | None = None,
) -> dict:
    session_id = session_id or str(uuid.uuid4())[:8]

    if PG_AVAILABLE:
        try:
            db_init = init_db_if_needed()
            if db_init.get("tables_created"):
                logger.info("[DB] PostgreSQL tables initialized")
            elif db_init.get("postgres_available"):
                logger.info("[DB] PostgreSQL connected")
            else:
                logger.info("[DB] PostgreSQL not available, using SQLite")
        except Exception as e:
            logger.warning(f"[DB] Init failed: {e}, using SQLite")
    else:
        logger.info("[DB] PostgreSQL not configured, using SQLite")

    route_output = route_query(user_query)
    logger.info(f"[Router] Query type: {route_output.query_type.value}")
    logger.info(f"[Router] Symbols: {route_output.symbols}")

    symbols = route_output.symbols or [symbol]
    timeframe = route_output.timeframe or timeframe

    if current_price == 0 and symbols:
        current_price = await _fetch_price(symbols[0])
    current_price = current_price or 50000

    state = {
        "symbol": symbols[0],
        "timeframe_requested": timeframe,
        "current_price": current_price,
        "birth_data": birth_data,
        "user_query": user_query,
        "session_id": session_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "all_signals": [],
    }

    thompson_selections: dict = {}
    technical_selected: list = []

    oap_adjustments: dict | None = None
    if OAP_WEIGHTING_ENABLED:
        try:
            oap_state = get_oap_optimizer().kpi_state
            all_agents = (
                list(TECHNICAL_POOL.agents)
                + list(MACRO_POOL.agents)
                + list(ASTRO_POOL.agents)
            )
            oap_adjustments = _compute_oap_adjustments(oap_state, all_agents)
        except Exception as e:
            logger.warning(f"[OAP] disabled due to error: {e}")
            oap_adjustments = None

    if include_technical:
        technical_selected = _select_for_flow(
            TECHNICAL_POOL, k=thompson_k, oap_adjustments=oap_adjustments
        )
        thompson_selections["technical"] = technical_selected
    if include_macro:
        macro_selected = _select_for_flow(
            MACRO_POOL,
            excluded=technical_selected,
            k=thompson_k,
            oap_adjustments=oap_adjustments,
        )
        thompson_selections["macro"] = macro_selected
    if include_astro:
        astro_selected = _select_for_flow(
            ASTRO_POOL,
            excluded=technical_selected,
            k=thompson_k,
            oap_adjustments=oap_adjustments,
        )
        thompson_selections["astro"] = astro_selected
    if include_electional:
        electoral_selected = _select_for_flow(ELECTORAL_POOL, k=1)
        thompson_selections["electoral"] = electoral_selected

    logger.info(f"[Thompson] technical: {technical_selected}")

    flow_tasks = []
    if include_technical:
        flow_tasks.append(run_technical_flow(state, selected_agents=technical_selected))
    if include_macro:
        flow_tasks.append(
            run_macro_flow(state, selected_agents=thompson_selections.get("macro", []))
        )
    if include_astro:
        flow_tasks.append(run_astro_flow(state, selected_agents=astro_selected))
    if include_electional:
        flow_tasks.append(run_electoral_flow(state))
    if flow_tasks:
        flow_results = await asyncio.gather(*flow_tasks, return_exceptions=True)
        for result in flow_results:
            if isinstance(result, dict):
                for key, value in result.items():
                    if key.endswith("_signal") and value is not None:
                        state["all_signals"].append(value)
        if not state["all_signals"]:
            logger.warning("[KARL] All agents failed — using SystemFallback")
            fallback_response = AgentResponse(
                agent_name="SystemFallback",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="All agents failed to produce a signal.",
            )
            state["all_signals"].append(fallback_response)

    karl_agent = KARLSynthesisAgent(
        sync_interval=sync_interval,
        enable_self_question=enable_self_question,
        enable_backtest=enable_backtest,
    )
    try:
        karl_result = await karl_agent.run(state)
        synthesis_result = karl_result.get("synthesis_result")
        amre_output = karl_result.get("amre_output")
        decision_record = karl_result.get("decision_record")
        karl_diagnostics_result = karl_result.get("karl_diagnostics")
    except Exception as e:
        logger.error(f"[KARLSynthesisAgent] Fell back to base synthesis: {e}")
        synthesis_agent = SynthesisAgent()
        synthesis_result = await synthesis_agent.run(state)
        synthesis_result = (
            synthesis_result.to_dict()
            if hasattr(synthesis_result, "to_dict")
            else synthesis_result
        )
        amre_output = None
        decision_record = None
        karl_diagnostics_result = None

    final_output = {
        "session_id": session_id,
        "symbol": symbols[0],
        "timeframe": timeframe,
        "current_price": current_price,
        "query_type": route_output.query_type.value,
        "flows_run": {
            "technical": include_technical,
            "astro": include_astro,
            "electional": include_electional,
            "macro": include_macro,
        },
        "thompson_selections": thompson_selections,
        "agent_count": len(state["all_signals"]),
        "final_recommendation": synthesis_result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "karl_enabled": True,
        "decision_record": decision_record,
        "amre_output": amre_output,
        "karl_diagnostics": karl_diagnostics_result,
    }

    if persist:
        save_session(final_output)
        update_beliefs_from_session(final_output)

    logger.info(
        f"[KARL] Session {session_id} completed: {len(state['all_signals'])} signals"
    )
    return final_output


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AstroFin Sentinel v5 Orchestrator")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--timeframe", default="SWING")
    parser.add_argument(
        "--mode", default="paper", choices=["historical", "paper", "live"]
    )
    parser.add_argument("--karl", action="store_true", default=True)
    parser.add_argument("--query", default="", help="User query")
    args = parser.parse_args()

    if args.karl:
        result = asyncio.run(
            run_karl_sentinel_v5(
                user_query=args.query, symbol=args.symbol, timeframe=args.timeframe
            )
        )
    else:
        result = asyncio.run(
            run_sentinel_v5(
                user_query=args.query, symbol=args.symbol, timeframe=args.timeframe
            )
        )

    log.info("\nFinal recommendation:", result.get("final_recommendation"))


if __name__ == "__main__":
    main()

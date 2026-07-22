"""
AstroFin Sentinel v5 — LangGraph Schema (Belief-Guided)

BeliefTracker + Thompson Sampling встроены в граф:
  - Каждый узел принимает решение "вызываться или пропуститься"
    через ThompsonSampler на основе Beta-распределения из belief.db
  - Пропущенный узел сразу передаёт state следующему узлу
  - Thompson sampling для параллельного пула (technical) отбирает
    подмножество агентов внутри узла

Flow (conditional, не sequential):
    START → technical → astro_council → electoral → synthesis → END
"""

import asyncio
from operator import add
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph

from core.belief import get_belief_tracker
from core.thompson import (

import logging
log = logging.getLogger(__name__)

    ASTRO_POOL,
    ELECTORAL_POOL,
    TECHNICAL_POOL,
    AgentPool,
    ThompsonSampler,
    get_thompson_sampler,
)

# ─── State ─────────────────────────────────────────────────────────────────────


class AgentState(TypedDict, total=False):
    symbol: str
    query: str
    timeframe: str
    current_price: float
    birth_data: dict | None
    include_technical: bool
    include_astro: bool
    include_electoral: bool
    query_type: str | None  # ELECTIONAL_ONLY, TECHNICAL_ONLY, etc.
    include_electoral_only: bool  # True when router requests election-only flow

    # Thompson selection results per flow
    thompson_selections: dict

    # Agent results (None if flow skipped)
    technical_result: dict | None
    astro_council_result: dict | None
    electoral_result: dict | None

    # Final synthesis
    synthesis_result: dict
    final_recommendation: dict | None

    errors: Annotated[list[str], add]
    session_id: str
    started_at: str


# ─── Thompson + Belief helpers ─────────────────────────────────────────────────

_sampler: ThompsonSampler | None = None


def _sampler() -> ThompsonSampler:
    global _sampler
    if _sampler is None:
        _sampler = get_thompson_sampler()
    return _sampler


def _pool_decide(pool: AgentPool, k_override: int = None) -> tuple[bool, list[str]]:
    """
    Decide whether a pool should run and which agents to select.

    Uses Thompson sampling:
      1. Get Beta(α, β) for each agent from belief tracker
      2. Skip agents with mean_accuracy < pool.min_usefulness
         (unseen agents get Beta(1+bonus, 1) based on sampler's exploration_bonus)
      3. Sample θ_i ~ Beta(α_i, β_i) for eligible agents
      4. Sort descending, take top-K (resolved: k_override > pool.k > default_k)

    Returns:
        (should_run: bool, selected_agents: list[str])
    """
    sampler = _sampler()
    bt = get_belief_tracker()
    pool_agents = pool.agents

    # Resolve K: explicit arg > pool.k > default_k from sampler
    k_resolved = (
        k_override
        if k_override is not None
        else (pool.k if pool.k is not None else sampler.default_k)
    )
    k = max(k_resolved, pool.min_select)
    k = min(k, len(pool_agents))

    # Step 1: filter by usefulness threshold
    eligible: list[tuple[str, float]] = []  # (name, sampled_theta)
    below: list[str] = []

    for name in pool_agents:
        belief = bt.get(name)
        if belief is not None and belief.mean < pool.min_usefulness:
            below.append(name)
            continue
        if belief is not None:
            alpha, beta = belief.alpha, belief.beta
        else:
            # Unseen: apply exploration_bonus to alpha
            alpha = sampler.DEFAULT_PRIOR_ALPHA + sampler.exploration_bonus
            beta = sampler.DEFAULT_PRIOR_BETA
        theta = sampler._sample_beta(alpha, beta)
        eligible.append((name, theta))

    # Fallback: if ALL below threshold, use all (need at least some agents)
    if not eligible:
        eligible = []
        for name in pool_agents:
            belief = bt.get(name)
            if belief is not None:
                alpha, beta = belief.alpha, belief.beta
            else:
                alpha = sampler.DEFAULT_PRIOR_ALPHA + sampler.exploration_bonus
                beta = sampler.DEFAULT_PRIOR_BETA
            theta = sampler._sample_beta(alpha, beta)
            eligible.append((name, theta))
        below = []

    # Step 2: sort by sampled theta, take top-K
    eligible.sort(key=lambda x: x[1], reverse=True)
    selected = [name for name, _ in eligible[:k]]

    if below:
        log.info(
            f"[BeliefGuard] '{pool.name}' — filtered (low utility): {below} | selected: {selected}"
        )

    should_run = len(selected) >= pool.min_select
    return should_run, selected


# ─── Graph Nodes ───────────────────────────────────────────────────────────────


def _run_technical_agents(state: AgentState, selected: list[str]) -> dict:
    """Run Thompson-selected technical agents in parallel."""
    from agents._impl.bear_researcher import run_bear_researcher
    from agents._impl.bull_researcher import run_bull_researcher
    from agents._impl.market_analyst import run_market_analyst

    tasks, names = [], []

    if "MarketAnalyst" in selected:
        tasks.append(run_market_analyst(state))
        names.append("MarketAnalyst")
    if "BullResearcher" in selected:
        tasks.append(run_bull_researcher(state))
        names.append("BullResearcher")
    if "BearResearcher" in selected:
        tasks.append(run_bear_researcher(state))
        names.append("BearResearcher")

    if not tasks:
        return {}

    results = asyncio.run(asyncio.gather(*tasks, return_exceptions=True))

    merged = {}
    for name, r in zip(names, results, strict=False):
        if isinstance(r, Exception):
            from agents.base_agent import AgentResponse, SignalDirection

            merged[f"{name.lower()}_signal"] = AgentResponse(
                agent_name=name,
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning=f"Agent error: {str(r)[:100]}",
                sources=[],
            ).model_dump()
        elif hasattr(r, "model_dump"):  # AgentResponse Pydantic model
            merged[f"{name.lower()}_signal"] = r.model_dump()
        elif isinstance(r, dict):
            merged[f"{name.lower()}_signal"] = r.get(f"{name.lower()}_signal") or (
                list(r.values())[0] if r else {}
            )
        else:
            merged[f"{name.lower()}_signal"] = {"signal": "NEUTRAL", "confidence": 0}
    return merged


def technical_node(state: AgentState) -> AgentState:
    """
    Thompson-sampled technical team node.

    Decision: should_run, selected = _pool_decide(TECHNICAL_POOL)
    If should_run=False → skip, go directly to astro_council (or synthesis).
    """
    should_run, selected = _pool_decide(TECHNICAL_POOL)

    if not should_run:
        log.info("[Graph] technical — SKIPPED (BeliefGuard)")
        return {**state, "technical_result": None}

    log.info(f"[Graph] technical — selected: {selected}")
    selections = dict(state.get("thompson_selections", {}))
    selections["technical"] = selected

    try:
        result = _run_technical_agents(state, selected)
    except Exception as e:  # noqa: BLE001 — graph node must never crash the pipeline
        result = {}
        errors = list(state.get("errors", []))
        errors.append(f"technical_node: {e}")
        state = {**state, "errors": errors}

    return {
        **state,
        "technical_result": result or {},
        "thompson_selections": selections,
    }


def astro_council_node(state: AgentState) -> AgentState:
    """
    AstroCouncil node with Thompson-sampled sub-agents.

    Decision: should_run, selected = _pool_decide(ASTRO_POOL)
    Excludes agents already selected in technical (BullResearcher, BearResearcher).
    If should_run=False → skip directly to electoral (or synthesis).
    """
    tech_selected = state.get("thompson_selections", {}).get("technical", [])
    excluded = [a for a in tech_selected if a in ASTRO_POOL.agents]
    candidates = [a for a in ASTRO_POOL.agents if a not in excluded]

    if not candidates:
        log.info("[Graph] astro_council — SKIPPED (no candidates after exclusion)")
        return {**state, "astro_council_result": None}

    tmp_pool = AgentPool(
        name="astro",
        agents=candidates,
        min_select=ASTRO_POOL.min_select,
        max_select=ASTRO_POOL.max_select,
        min_usefulness=ASTRO_POOL.min_usefulness,
        k=ASTRO_POOL.k,
    )
    should_run, selected = _pool_decide(tmp_pool)

    if not should_run:
        log.info("[Graph] astro_council — SKIPPED (BeliefGuard)")
        return {**state, "astro_council_result": None}

    log.info(f"[Graph] astro_council — selected: {selected}")
    selections = dict(state.get("thompson_selections", {}))
    selections["astro"] = selected

    try:
        from agents.astro_council_agent import run_astro_council

        enriched = {**state, "_thompson_selected_astro": selected}
        result = asyncio.run(run_astro_council(enriched))
    except Exception as e:  # noqa: BLE001 — graph node must never crash the pipeline
        result = {}
        errors = list(state.get("errors", []))
        errors.append(f"astro_council_node: {e}")

    return {
        **state,
        "astro_council_result": result or {},
        "thompson_selections": selections,
    }


def electoral_node(state: AgentState) -> AgentState:
    """
    ElectoralAgent node (always single agent, Thompson just for consistency).

    Decision: should_run, selected = _pool_decide(ELECTORAL_POOL)
    If should_run=False → skip directly to synthesis.
    """
    should_run, selected = _pool_decide(ELECTORAL_POOL)

    if not should_run:
        log.info("[Graph] electoral — SKIPPED (BeliefGuard)")
        return {**state, "electoral_result": None}

    log.info(f"[Graph] electoral — selected: {selected}")
    selections = dict(state.get("thompson_selections", {}))
    selections["electoral"] = selected

    try:
        from agents._impl.electoral_agent import run_electoral_agent

        result = asyncio.run(run_electoral_agent(state))
    except Exception as e:  # noqa: BLE001 — graph node must never crash the pipeline
        result = {}
        errors = list(state.get("errors", []))
        errors.append(f"electoral_node: {e}")

    return {
        **state,
        "electoral_result": result or {},
        "thompson_selections": selections,
    }


def synthesis_node(state: AgentState) -> AgentState:
    """
    Synthesis node — always runs last, regardless of which flows were active.
    Collects all produced signals into all_signals for SynthesisAgent.
    """
    from agents._impl.synthesis_agent import SynthesisAgent

    all_signals: list = []

    # Collect from technical
    tech = state.get("technical_result")
    if tech:
        for v in tech.values():
            if isinstance(v, dict):
                all_signals.append(v)

    # Collect from astro_council
    astro = state.get("astro_council_result")
    if astro:
        for v in astro.values():
            if isinstance(v, dict):
                all_signals.append(v)

    # Collect from electoral
    elec = state.get("electoral_result")
    if elec:
        for v in elec.values():
            if isinstance(v, dict):
                all_signals.append(v)

    synth_state = {
        **state,
        "all_signals": all_signals,
        "thompson_selections": state.get("thompson_selections", {}),
    }

    try:
        agent = SynthesisAgent()
        result = asyncio.run(agent.run(synth_state))
        rec = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    except Exception as e:  # noqa: BLE001 — graph node must never crash the pipeline
        rec = {
            "agent_name": "SynthesisAgent",
            "error": str(e),
            "signal": "NEUTRAL",
            "confidence": 0,
            "reasoning": "Synthesis failed",
            "sources": [],
            "metadata": {},
        }

    return {**state, "synthesis_result": rec, "final_recommendation": rec}


# ─── Conditional Edge Routing ─────────────────────────────────────────────────


def route_after_start(
    state: AgentState,
) -> Literal["technical", "astro_council", "electoral", "synthesis"]:
    """
    Маршрутизация с полным уважением к флагам из router.py.
    Priority order: ELECTORAL_ONLY > astro-only (no tech) > technical > astro > electional > synthesis.
    """
    # Priority 1: ELECTORAL_ONLY from router
    query_type = state.get("query_type", "")
    if query_type == "ELECTORAL_ONLY" or state.get("include_electoral_only", False):
        return "electoral"

    # Priority 2: Astro only (technical explicitly disabled)
    include_tech = state.get("include_technical", True)
    include_astro = state.get("include_astro", True)
    if include_astro and not include_tech:
        return "astro_council"

    # Priority 3: Technical (default when enabled)
    if include_tech:
        return "technical"

    # Priority 4: Astro (tech disabled, astro enabled)
    if include_astro:
        return "astro_council"

    # Priority 5: Electional timing (flag-based)
    if state.get("include_electoral", False):
        return "electoral"

    # Fallback: synthesis
    return "synthesis"


def route_from_technical(
    state: AgentState,
) -> Literal["astro_council", "electoral", "synthesis", "__end__"]:
    """After technical: skip to next active node (or synthesis/END)."""
    if state.get("include_astro", True):
        return "astro_council"
    if state.get("include_electoral", False):
        return "electoral"
    return "synthesis"


def route_from_astro(state: AgentState) -> Literal["electoral", "synthesis", "__end__"]:
    """After astro_council: skip to next active node (or synthesis/END)."""
    if state.get("include_electoral", False):
        return "electoral"
    return "synthesis"


# ─── Graph Builder ─────────────────────────────────────────────────────────────


def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("technical", technical_node)
    g.add_node("astro_council", astro_council_node)
    g.add_node("electoral", electoral_node)
    g.add_node("synthesis", synthesis_node)

    # Start → first active agent
    g.add_conditional_edges(
        "__start__",
        route_after_start,
        {
            "technical": "technical",
            "astro_council": "astro_council",
            "electoral": "electoral",
            "synthesis": "synthesis",
        },
    )

    # Each agent routes to next active node (BeliefGuard handles skip internally)
    g.add_conditional_edges(
        "technical",
        route_from_technical,
        {
            "astro_council": "astro_council",
            "electoral": "electoral",
            "synthesis": "synthesis",
            "__end__": END,
        },
    )

    g.add_conditional_edges(
        "astro_council",
        route_from_astro,
        {
            "electoral": "electoral",
            "synthesis": "synthesis",
            "__end__": END,
        },
    )

    g.add_edge("electoral", "synthesis")
    g.add_edge("synthesis", END)

    return g.compile()


graph = build_graph()

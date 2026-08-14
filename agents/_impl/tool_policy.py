"""AgentToolPolicy — Allow-listing tool calls per agent.

GitHub Agentic Workflows v0.86.1 pattern applied to AstroFin Sentinel V5.
Each agent maps to an allowed set of tools. BaseAgent enforces the policy
before any tool call via can_use_tool().
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentToolPolicy:
    """Mapping: agent → allowed tools (allow-list)."""

    agent_name: str
    allowed_tools: list[str] = field(default_factory=list)
    description: str = ""


# ── Global Policies (allow-list registry) ──────────────────────────────

TOOL_POLICIES: dict[str, AgentToolPolicy] = {
    "FundamentalAgent": AgentToolPolicy(
        "FundamentalAgent",
        allowed_tools=["sec_edgar", "coingecko", "coinglass", "data_room.*"],
        description="SEC filings, market data, on-chain metrics",
    ),
    "MacroAgent": AgentToolPolicy(
        "MacroAgent",
        allowed_tools=["feargreed", "yahoo", "data_room.*", "news_sentiment"],
        description="VIX, DXY, macro indicators, sentiment feed",
    ),
    "QuantAgent": AgentToolPolicy(
        "QuantAgent",
        allowed_tools=["data_room.*", "backtest", "risk_engine"],
        description="Backtesting, risk models, statistical analysis",
    ),
    "OptionsFlowAgent": AgentToolPolicy(
        "OptionsFlowAgent",
        allowed_tools=["data_room.*", "polygon_options", "gamma_exposure"],
        description="Options flow data, gamma exposure calculations",
    ),
    "SentimentAgent": AgentToolPolicy(
        "SentimentAgent",
        allowed_tools=["news_sentiment", "social_scraper", "data_room.*"],
        description="News, Reddit, X, social media sentiment",
    ),
    "TechnicalAgent": AgentToolPolicy(
        "TechnicalAgent",
        allowed_tools=["data_room.*", "indicator_calc"],
        description="Technical indicators (RSI, MACD, Bollinger)",
    ),
    "BullResearcher": AgentToolPolicy(
        "BullResearcher",
        allowed_tools=["data_room.*", "feargreed", "news_sentiment"],
        description="Bullish research: data, sentiment, fundamentals",
    ),
    "BearResearcher": AgentToolPolicy(
        "BearResearcher",
        allowed_tools=["data_room.*", "feargreed", "news_sentiment"],
        description="Bearish research: risk signals, downside catalysts",
    ),
    "ElectoralAgent": AgentToolPolicy(
        "ElectoralAgent",
        allowed_tools=["ephemeris", "muhurtha"],
        description="Swiss Ephemeris, Muhurta electional timing",
    ),
    "BradleyAgent": AgentToolPolicy(
        "BradleyAgent",
        allowed_tools=["ephemeris", "aspect_engine", "data_room.*"],
        description="Planetary aspects, Bradley model, seasonality",
    ),
    "TimeWindowAgent": AgentToolPolicy(
        "TimeWindowAgent",
        allowed_tools=["ephemeris", "data_room.*"],
        description="Multi-TF windows, astro timing",
    ),
    "GannAgent": AgentToolPolicy(
        "GannAgent",
        allowed_tools=["ephemeris", "data_room.*", "indicator_calc"],
        description="Gann angles, time/price squares, astro clusters",
    ),
    "CycleAgent": AgentToolPolicy(
        "CycleAgent",
        allowed_tools=["ephemeris", "data_room.*", "cycle_detector"],
        description="Market cycles, planetary cycles, phase detection",
    ),
    "KARLSynthesisAgent": AgentToolPolicy(
        "KARLSynthesisAgent",
        allowed_tools=["*"],
        description="Arbiter — unrestricted access to all tools",
    ),
    "AstroCouncilAgent": AgentToolPolicy(
        "AstroCouncilAgent",
        allowed_tools=["ephemeris", "muhurtha", "aspect_engine"],
        description="Astro coordinator — ephemeris + timing",
    ),
}


def get_policy(agent_name: str) -> AgentToolPolicy | None:
    """Return the tool policy for a given agent, or None."""
    return TOOL_POLICIES.get(agent_name)


def can_use_tool(agent_name: str, tool_name: str) -> bool:
    """Check if an agent is allowed to use a specific tool."""
    policy = TOOL_POLICIES.get(agent_name)
    if policy is None:
        # No policy = allow all (backward compatible)
        return True
    for allowed in policy.allowed_tools:
        if allowed == "*" or allowed == tool_name:
            return True
        if allowed.endswith(".*") and tool_name.startswith(allowed[:-2]):
            return True
    return False

"""mas_factory/registry.py - Agent Registry with capabilities"""

from __future__ import annotations

from typing import Any

from mas_factory.topology import Role

# Agent registry - maps agent_type → Role definition
# This replaces hard-coded pools in sentinel_v5.py

AGENT_DEFINITIONS = {
    # === FUNDAMENTAL CATEGORY ===
    "FundamentalAgent": Role(
        name="fundamental",
        agent_type="FundamentalAgent",
        weight=0.20,
        capabilities=[
            "fundamental_analysis",
            "valuation",
            "financial_metrics",
            "pe_ratio",
            "mvrv",
        ],
        inputs=["symbol", "price"],
        outputs=["signal", "confidence", "reasoning", "fundamental_score"],
        constraints={"timeout_ms": 30000},
    ),
    "InsiderAgent": Role(
        name="insider",
        agent_type="InsiderAgent",
        weight=0.10,
        capabilities=["insider_tracking", "sec_filings", "whale_activity"],
        inputs=["symbol"],
        outputs=["signal", "confidence"],
    ),
    # === MACRO CATEGORY ===
    "MacroAgent": Role(
        name="macro",
        agent_type="MacroAgent",
        weight=0.15,
        capabilities=[
            "macro_analysis",
            "economic_indicators",
            "fed_policy",
            "geopolitics",
            "dxy",
            "vix",
        ],
        inputs=["symbol"],
        outputs=["signal", "confidence", "macro_score"],
        constraints={"timeout_ms": 20000},
    ),
    # === QUANT CATEGORY ===
    "QuantAgent": Role(
        name="quant",
        agent_type="QuantAgent",
        weight=0.20,
        capabilities=[
            "ml_predictions",
            "backtesting",
            "volatility_model",
            "pattern_recognition",
        ],
        inputs=["symbol", "price", "ohlcv"],
        outputs=["signal", "confidence", "predicted_volatility"],
        constraints={"timeout_ms": 45000},
    ),
    "MLPredictorAgent": Role(
        name="ml_predictor",
        agent_type="MLPredictorAgent",
        weight=0.15,
        capabilities=["ml_predictions", "price_forecasting", "time_series"],
        inputs=["symbol", "price_history"],
        outputs=["signal", "confidence", "price_target"],
    ),
    # === OPTIONS CATEGORY ===
    "OptionsFlowAgent": Role(
        name="options",
        agent_type="OptionsFlowAgent",
        weight=0.15,
        capabilities=["options_flow", "gamma_exposure", "unusual_activity", "iv_rank"],
        inputs=["symbol"],
        outputs=["signal", "confidence", "gamma_exposure", "iv_rank"],
        constraints={"timeout_ms": 20000},
    ),
    # === SENTIMENT CATEGORY ===
    "SentimentAgent": Role(
        name="sentiment",
        agent_type="SentimentAgent",
        weight=0.10,
        capabilities=[
            "social_sentiment",
            "news_analysis",
            "fear_greed",
            "reddit",
            "twitter",
        ],
        inputs=["symbol"],
        outputs=["signal", "confidence", "sentiment_score"],
        constraints={"timeout_ms": 15000},
    ),
    "BullResearcher": Role(
        name="bull",
        agent_type="BullResearcher",
        weight=0.05,
        capabilities=["bullish_narrative", "strength_factors", "catalyst_research"],
        inputs=["symbol"],
        outputs=["signal", "confidence", "bullish_factors"],
    ),
    "BearResearcher": Role(
        name="bear",
        agent_type="BearResearcher",
        weight=0.05,
        capabilities=["bearish_narrative", "risk_factors", "downside_scenarios"],
        inputs=["symbol"],
        outputs=["signal", "confidence", "bearish_factors"],
    ),
    # === TECHNICAL CATEGORY ===
    "TechnicalAgent": Role(
        name="technical",
        agent_type="TechnicalAgent",
        weight=0.10,
        capabilities=[
            "technical_analysis",
            "price_action",
            "indicators",
            "rsi",
            "macd",
            "bollinger",
        ],
        inputs=["symbol", "price", "ohlcv"],
        outputs=["signal", "confidence", "support_resistance"],
    ),
    "MarketAnalyst": Role(
        name="market_analyst",
        agent_type="MarketAnalyst",
        weight=0.10,
        capabilities=["market_structure", "trend_analysis", "volume_profile"],
        inputs=["symbol", "price"],
        outputs=["signal", "confidence", "market_structure"],
    ),
    "ElliotWaveAgent": Role(
        name="elliot",
        agent_type="ElliotWaveAgent",
        weight=0.05,
        capabilities=["elliot_wave", "wave_counting", "pattern_analysis"],
        inputs=["symbol", "price_history"],
        outputs=["signal", "confidence", "wave_label"],
    ),
    # === ASTRO CATEGORY ===
    "AstroCouncil": Role(
        name="astro_council",
        agent_type="AstroCouncil",
        weight=0.16,
        capabilities=["planetary_positions", "aspects", "natal_chart", "retrograde"],
        inputs=["symbol", "birth_data"],
        outputs=["signal", "confidence", "astro_factors"],
        constraints={"timeout_ms": 5000},  # Fast ephemeris
    ),
    "BradleyAgent": Role(
        name="bradley",
        agent_type="BradleyAgent",
        weight=0.03,
        capabilities=["bradley_model", "seasonality", "planetary_aspects"],
        inputs=["symbol", "date"],
        outputs=["signal", "confidence"],
    ),
    "GannAgent": Role(
        name="gann",
        agent_type="GannAgent",
        weight=0.03,
        capabilities=["gann_angles", "square_of_nine", "time_price_analysis"],
        inputs=["symbol", "price", "date"],
        outputs=["signal", "confidence", "gann_levels"],
    ),
    "CycleAgent": Role(
        name="cycle",
        agent_type="CycleAgent",
        weight=0.05,
        capabilities=["cycle_analysis", "dominant_cycles", "turning_points"],
        inputs=["symbol", "price_history"],
        outputs=["signal", "confidence", "cycle_phase"],
    ),
    "ElectoralAgent": Role(
        name="electoral",
        agent_type="ElectoralAgent",
        weight=0.03,
        capabilities=[
            "muhurta_timing",
            "electional_astrology",
            "choghadiya",
            "nakshatra",
        ],
        inputs=["symbol", "timeframe"],
        outputs=["signal", "confidence", "timing_score"],
        constraints={"timeout_ms": 5000},
    ),
    "TimeWindowAgent": Role(
        name="time_window",
        agent_type="TimeWindowAgent",
        weight=0.02,
        capabilities=["entry_windows", "multi_timeframe", "4h_1d_1w"],
        inputs=["symbol"],
        outputs=["signal", "confidence", "best_windows"],
    ),
    # === COORDINATOR ===
    "SynthesisAgent": Role(
        name="synthesis",
        agent_type="SynthesisAgent",
        weight=0.0,  # Coordinator - no vote
        capabilities=[
            "synthesis",
            "final_recommendation",
            "weighting",
            "conflict_resolution",
        ],
        inputs=["signals"],
        outputs=["final_signal", "confidence", "breakdown"],
        constraints={"timeout_ms": 5000},
    ),
}


class AgentRegistry:
    """Registry of available agents with capabilities and constraints"""

    def __init__(self):
        self._roles: dict[str, Role] = {}
        for agent_type, role in AGENT_DEFINITIONS.items():
            self._roles[agent_type] = role

    def get_role(self, agent_type: str) -> Role | None:
        return self._roles.get(agent_type)

    def get_all_roles(self) -> list[Role]:
        return list(self._roles.values())

    def get_by_capability(self, capability: str) -> list[Role]:
        return [r for r in self._roles.values() if capability in r.capabilities]

    def get_pool(self, pool_name: str) -> list[Role]:
        """Get roles by pool category"""
        pools = {
            "fundamental": ["FundamentalAgent", "InsiderAgent"],
            "macro": ["MacroAgent"],
            "quant": ["QuantAgent", "MLPredictorAgent"],
            "options": ["OptionsFlowAgent"],
            "sentiment": ["SentimentAgent", "BullResearcher", "BearResearcher"],
            "technical": ["TechnicalAgent", "MarketAnalyst", "ElliotWaveAgent"],
            "astro": ["AstroCouncil", "BradleyAgent", "GannAgent", "CycleAgent"],
            "electoral": ["ElectoralAgent", "TimeWindowAgent"],
        }
        types = pools.get(pool_name, [])
        return [self._roles[t] for t in types if t in self._roles]

    def register(self, agent_type: str, role: Role):
        """Register a new agent dynamically"""
        self._roles[agent_type] = role

    def list_capabilities(self) -> list[str]:
        """List all unique capabilities"""
        caps = set()
        for role in self._roles.values():
            caps.update(role.capabilities)
        return sorted(caps)


# Singleton
_REGISTRY: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = AgentRegistry()
    return _REGISTRY


# Agent runner wrapper for MAS Factory compatibility
class BasicAgentRunner:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        return {"signal": "NEUTRAL", "confidence": 50, "agent": self.agent_type}


def get_agent_runner(agent_type: str) -> BasicAgentRunner:
    return BasicAgentRunner(agent_type)

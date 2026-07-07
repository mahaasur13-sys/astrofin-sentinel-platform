
"""
agents._impl — All analytical agents for AstroFin Sentinel v5.

Architecture (2026 Hybrid Signal):
  - AstroSignal: 25% (astrology)
  - Fundamental + Macro: 20%
  - Quant/AI: 20%
  - Options Flow: 15%
  - Sentiment: 10%
  - Technical: 10% (filter only)
"""

from __future__ import annotations

# Core Astro Agents
from agents._impl.bear_researcher import BearResearcherAgent, run_bear_researcher
from agents._impl.bradley_agent import BradleyAgent, run_bradley_agent
from agents._impl.bull_researcher import BullResearcherAgent, run_bull_researcher
from agents._impl.compromise_agent import CompromiseAgent, run_compromise_agent
from agents._impl.cycle_agent import CycleAgent, run_cycle_agent
from agents._impl.electoral_agent import ElectoralAgent, run_electoral_agent
from agents._impl.elliot_agent import ElliotAgent, run_elliot_agent

# Ephemeris decorator
from agents._impl.ephemeris_decorator import HAS_SWISS_EPHEMERIS, require_ephemeris

# NEW: Hybrid Platform Agents (2026)
from agents._impl.fundamental_agent import FundamentalAgent, run_fundamental_agent
from agents._impl.gann_agent import GannAgent, run_gann_agent
from agents._impl.insider_agent import InsiderAgent, run_insider_agent
from agents._impl.macro_agent import MacroAgent, run_macro_agent
from agents._impl.market_analyst import MarketAnalystAgent, run_market_analyst
from agents._impl.ml_predictor_agent import MLPredictorAgent, run_ml_predictor_agent
from agents._impl.options_flow_agent import OptionsFlowAgent, run_options_flow_agent
from agents._impl.quant_agent import QuantAgent, run_quant_agent
from agents._impl.risk_agent import RiskAgent, run_risk_agent
from agents._impl.sentiment_agent import SentimentAgent, run_sentiment_agent
from agents._impl.synthesis_agent import SynthesisAgent
from agents._impl.technical_agent import TechnicalAgent, run_technical_agent
from agents._impl.time_window_agent import TimeWindowAgent, run_time_window_agent

# Ensure @require_ephemeris symbol is imported for R2 detection
from agents._impl.ephemeris_decorator import require_ephemeris  # noqa: F401

__all__ = [
    # Astro Agents
    "BullResearcherAgent",
    "run_bull_researcher",
    "BearResearcherAgent",
    "run_bear_researcher",
    "CycleAgent",
    "run_cycle_agent",
    "CompromiseAgent",
    "run_compromise_agent",
    "RiskAgent",
    "run_risk_agent",
    "GannAgent",
    "run_gann_agent",
    "ElliotAgent",
    "run_elliot_agent",
    "BradleyAgent",
    "run_bradley_agent",
    "SentimentAgent",
    "run_sentiment_agent",
    "TimeWindowAgent",
    "run_time_window_agent",
    # Hybrid Agents
    "FundamentalAgent",
    "run_fundamental_agent",
    "InsiderAgent",
    "run_insider_agent",
    "MacroAgent",
    "run_macro_agent",
    "QuantAgent",
    "run_quant_agent",
    "OptionsFlowAgent",
    "run_options_flow_agent",
    "MLPredictorAgent",
    "run_ml_predictor_agent",
    "TechnicalAgent",
    "run_technical_agent",
    "ElectoralAgent",
    "run_electoral_agent",
    "MarketAnalystAgent",
    "run_market_analyst",
    "SynthesisAgent",
    # Utils
    "require_ephemeris",
    "HAS_SWISS_EPHEMERIS",
]

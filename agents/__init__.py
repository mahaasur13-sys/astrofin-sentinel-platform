"""agents — AstroFin Sentinel V5 Agent Layer

Re-exports all canonical agents from _impl/ for clean public API.

Architecture (DEDUP-001):
    agents/             ← public API (re-exports from _impl/)
    agents/_impl/       ← canonical implementations
    agents/_archived/   ← deprecated duplicates
"""

from __future__ import annotations

from agents._impl.bear_researcher import BearResearcherAgent, run_bear_researcher
from agents._impl.bradley_agent import BradleyAgent, run_bradley_agent
from agents._impl.bull_researcher import BullResearcherAgent, run_bull_researcher
from agents._impl.compromise_agent import CompromiseAgent, run_compromise_agent
from agents._impl.cycle_agent import CycleAgent, run_cycle_agent
from agents._impl.electoral_agent import ElectoralAgent, run_electoral_agent
from agents._impl.elliot_agent import ElliotAgent, run_elliot_agent
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
from agents.astro_council_agent import AstroCouncilAgent
from agents.base_agent import AgentResponse, BaseAgent, SignalDirection
from agents.karl_synthesis import KARLSynthesisAgent

__all__ = [
    "FundamentalAgent",
    "run_fundamental_agent",
    "MacroAgent",
    "run_macro_agent",
    "QuantAgent",
    "run_quant_agent",
    "OptionsFlowAgent",
    "run_options_flow_agent",
    "SentimentAgent",
    "run_sentiment_agent",
    "BullResearcherAgent",
    "run_bull_researcher",
    "BearResearcherAgent",
    "run_bear_researcher",
    "SynthesisAgent",
    "CompromiseAgent",
    "run_compromise_agent",
    "MarketAnalystAgent",
    "run_market_analyst",
    "ElectoralAgent",
    "run_electoral_agent",
    "TechnicalAgent",
    "run_technical_agent",
    "BradleyAgent",
    "run_bradley_agent",
    "GannAgent",
    "run_gann_agent",
    "CycleAgent",
    "run_cycle_agent",
    "TimeWindowAgent",
    "run_time_window_agent",
    "MLPredictorAgent",
    "run_ml_predictor_agent",
    "InsiderAgent",
    "run_insider_agent",
    "ElliotAgent",
    "run_elliot_agent",
    "RiskAgent",
    "run_risk_agent",
    "AstroCouncilAgent",
    "BaseAgent",
    "AgentResponse",
    "SignalDirection",
    "KARLSynthesisAgent",
]

#!/usr/bin/env python3
"""
ACOS × AstroFin — 14 Agent Registry
Each agent = ACOS job type with constraint profile.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentSpec:
    name: str
    acos_job_type: str
    acos_layer: str          # L0-L10 layer that governs this agent
    constraint_block: str    # from AstroFinConstraintCompiler
    compute_profile: str      # cpu | gpu | edge
    timeout_sec: int = 300
    requires_governance: bool = True
    risk_weight: float = 1.0
    description: str = ""


AGENTS = {
    # ── Fundamental Analysis ──
    "fundamental": AgentSpec(
        name="FundamentalAgent",
        acos_job_type="astrofin_fundamental",
        acos_layer="L5",
        constraint_block="astrofin_risk_default",
        compute_profile="cpu",
        timeout_sec=300,
        risk_weight=0.8,
        description="DCF, earnings, balance sheet scoring",
    ),

    # ── Quantitative ──
    "quant": AgentSpec(
        name="QuantAgent",
        acos_job_type="astrofin_quant",
        acos_layer="L6",
        constraint_block="astrofin_risk_default",
        compute_profile="gpu",
        timeout_sec=600,
        risk_weight=1.0,
        description="Statistical arbitrage, factor models",
    ),

    # ── Macro ──
    "macro": AgentSpec(
        name="MacroAgent",
        acos_job_type="astrofin_macro",
        acos_layer="L5",
        constraint_block="astrofin_risk_default",
        compute_profile="cpu",
        timeout_sec=180,
        risk_weight=0.7,
        description="Fed policy, CPI, GDP, geopolitical",
    ),

    # ── Options Flow ──
    "options_flow": AgentSpec(
        name="OptionsFlowAgent",
        acos_job_type="astrofin_options_flow",
        acos_layer="L6",
        constraint_block="astrofin_risk_default",
        compute_profile="gpu",
        timeout_sec=300,
        risk_weight=1.2,
        description="Unusual options activity, dark pool flow",
    ),

    # ── Sentiment ──
    "sentiment": AgentSpec(
        name="SentimentAgent",
        acos_job_type="astrofin_sentiment",
        acos_layer="L5",
        constraint_block="astrofin_risk_default",
        compute_profile="cpu",
        timeout_sec=120,
        risk_weight=0.6,
        description="News, social, analyst ratings",
    ),

    # ── Technical ──
    "technical": AgentSpec(
        name="TechnicalAgent",
        acos_job_type="astrofin_technical",
        acos_layer="L6",
        constraint_block="astrofin_risk_default",
        compute_profile="gpu",
        timeout_sec=180,
        risk_weight=0.9,
        description="Patterns, indicators, volume analysis",
    ),

    # ── Bull / Bear Research ──
    "bull": AgentSpec(
        name="BullResearcher",
        acos_job_type="astrofin_bull",
        acos_layer="L5",
        constraint_block="astrofin_risk_default",
        compute_profile="cpu",
        timeout_sec=240,
        risk_weight=0.5,
        description="Bull case scenario construction",
    ),
    "bear": AgentSpec(
        name="BearResearcher",
        acos_job_type="astrofin_bear",
        acos_layer="L5",
        constraint_block="astrofin_risk_default",
        compute_profile="cpu",
        timeout_sec=240,
        risk_weight=0.5,
        description="Bear case scenario construction",
    ),

    # ── Cycle Analysis ──
    "cycle": AgentSpec(
        name="CycleAgent",
        acos_job_type="astrofin_cycle",
        acos_layer="L6",
        constraint_block="astrofin_risk_default",
        compute_profile="gpu",
        timeout_sec=600,
        risk_weight=1.0,
        description="Kondratieff, Juglar, Kuznets cycles",
    ),
    "bradley": AgentSpec(
        name="BradleyAgent",
        acos_job_type="astrofin_bradley",
        acos_layer="L6",
        constraint_block="astrofin_risk_default",
        compute_profile="gpu",
        timeout_sec=900,
        risk_weight=1.1,
        description="Bradley Money Roshambo timing model",
    ),

    # ── Astrological ──
    "electoral": AgentSpec(
        name="ElectoralAgent",
        acos_job_type="astrofin_electoral",
        acos_layer="L5",
        constraint_block="astrofin_risk_default",
        compute_profile="cpu",
        timeout_sec=300,
        risk_weight=0.7,
        description="Electoral cycles, political timing",
    ),
    "gann": AgentSpec(
        name="GannAgent",
        acos_job_type="astrofin_gann",
        acos_layer="L6",
        constraint_block="astrofin_risk_default",
        compute_profile="gpu",
        timeout_sec=900,
        risk_weight=1.1,
        description="Gann angles, square of 9, time cycles",
    ),

    # ── Time Windows ──
    "timewindow": AgentSpec(
        name="TimeWindowAgent",
        acos_job_type="astrofin_timewindow",
        acos_layer="L5",
        constraint_block="astrofin_risk_default",
        compute_profile="cpu",
        timeout_sec=60,
        risk_weight=0.4,
        description="Astro timing windows,Muhurta selection",
    ),

    # ── Risk (HARD GOVERNANCE GATED) ──
    "risk": AgentSpec(
        name="RiskAgent",
        acos_job_type="astrofin_risk",
        acos_layer="L8",           # L8: HARD GOVERNANCE GATED
        constraint_block="astrofin_risk_default",
        compute_profile="cpu",
        timeout_sec=120,
        requires_governance=True,  # MANDATORY L8 + L9 approval
        risk_weight=2.0,
        description="Portfolio risk, VaR, drawdown enforcement",
    ),
}


def get_agent(name: str) -> Optional[AgentSpec]:
    return AGENTS.get(name)


def list_agents() -> dict[str, AgentSpec]:
    return AGENTS.copy()


def get_governance_gated_agents() -> list[str]:
    """Agents that MUST pass L8+L9 before execution."""
    return [a.name for a in AGENTS.values() if a.requires_governance]


def get_gpu_agents() -> list[str]:
    return [a.name for a in AGENTS.values() if a.compute_profile == "gpu"]


def get_cpu_agents() -> list[str]:
    return [a.name for a in AGENTS.values() if a.compute_profile == "cpu"]



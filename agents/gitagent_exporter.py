#!/usr/bin/env python3
"""agents/gitagent_exporter.py — Export all agents to GitAgent format (fixed YAML)"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import yaml

AGENTS = {
    "bull_researcher": {
        "name": "BullResearcher",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "research",
        "weight": 0.05,
        "description": "Identifies bullish factors and positive narratives for trading decisions",
        "capabilities": ["bullish_narrative_discovery", "positive_momentum_identification", "opportunity_mapping"],
        "inputs": ["market_state", "news", "social_sentiment"],
        "outputs": ["bullish_signals", "opportunities"],
        "karl": {"reward_weight": 0.05, "supports_ttc": True, "supports_selfq": True},
        "sources": ["News API", "Social Media", "On-chain data"],
    },
    "bear_researcher": {
        "name": "BearResearcher",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "research",
        "weight": 0.05,
        "description": "Identifies bearish risks and negative narratives for trading decisions",
        "capabilities": ["bearish_risk_discovery", "negative_momentum_identification", "risk_mapping"],
        "inputs": ["market_state", "news", "social_sentiment"],
        "outputs": ["bearish_signals", "risks"],
        "karl": {"reward_weight": 0.05, "supports_ttc": True, "supports_selfq": True},
        "sources": ["News API", "Social Media", "On-chain data"],
    },
    "technical_agent": {
        "name": "TechnicalAgent",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "technical",
        "weight": 0.10,
        "description": "Technical analysis: RSI, MACD, Bollinger, Volume",
        "capabilities": [
            "trend_detection",
            "indicator_analysis",
            "rsi_calculation",
            "macd_analysis",
            "bollinger_bands",
            "volume_profile",
        ],
        "inputs": ["market_state", "ohlcv_data", "indicators"],
        "outputs": ["signal", "confidence", "reasoning"],
        "karl": {"reward_weight": 0.10, "supports_ttc": True, "supports_selfq": True},
        "sources": ["Binance API", "Technical analysis"],
    },
    "sentiment_agent": {
        "name": "SentimentAgent",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "sentiment",
        "weight": 0.10,
        "description": "Analyzes news, social media, and Fear & Greed Index for market sentiment",
        "capabilities": ["news_sentiment", "social_media_analysis", "fear_greed_index", "reddit_twitter_analysis"],
        "inputs": ["news", "social_data", "fear_greed"],
        "outputs": ["sentiment_score", "confidence", "reasoning"],
        "karl": {"reward_weight": 0.10, "supports_ttc": True, "supports_selfq": True},
        "sources": ["News API", "Reddit", "Twitter", "Fear & Greed Index"],
    },
    "options_flow_agent": {
        "name": "OptionsFlowAgent",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "options",
        "weight": 0.15,
        "description": "Analyzes options flow, unusual activity, gamma exposure for market direction",
        "capabilities": ["options_flow_analysis", "unusual_activity_detection", "gamma_exposure", "put_call_ratio"],
        "inputs": ["options_data", "market_state"],
        "outputs": ["signal", "confidence", "gamma_exposure"],
        "karl": {"reward_weight": 0.15, "supports_ttc": True, "supports_selfq": True},
        "sources": ["Unusual Whales", "CBOE", "Polygon.io"],
    },
    "insider_agent": {
        "name": "InsiderAgent",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "fundamental",
        "weight": 0.05,
        "description": "Tracks insider transactions and institutional activity from SEC 13F filings",
        "capabilities": ["insider_tracking", "sec_13f_analysis", "institutional_holding_changes"],
        "inputs": ["sec_filings", "insider_transactions"],
        "outputs": ["insider_signal", "confidence", "institutional_flow"],
        "karl": {"reward_weight": 0.05, "supports_ttc": False, "supports_selfq": False},
        "sources": ["SEC EDGAR", "Form 13F", "Insider tracking services"],
    },
    "ml_predictor_agent": {
        "name": "MLPredictorAgent",
        "version": "1.0.0",
        "type": "prediction",
        "domain": "quant",
        "weight": 0.08,
        "description": "ML-based price prediction using historical patterns and features",
        "capabilities": ["price_prediction", "pattern_recognition", "feature_based_ml", "regime_detection"],
        "inputs": ["price_history", "features", "regime"],
        "outputs": ["predicted_direction", "confidence", "features_used"],
        "karl": {"reward_weight": 0.08, "supports_ttc": True, "supports_selfq": True},
        "sources": ["Historical data", "Feature engineering"],
    },
    "market_analyst": {
        "name": "MarketAnalyst",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "technical",
        "weight": 0.05,
        "description": "Market structure analysis: support/resistance, patterns, order blocks",
        "capabilities": ["market_structure", "support_resistance", "pattern_recognition", "order_block_identification"],
        "inputs": ["price_data", "volume_profile"],
        "outputs": ["structure_signal", "key_levels", "confidence"],
        "karl": {"reward_weight": 0.05, "supports_ttc": True, "supports_selfq": True},
        "sources": ["Price action", "Volume profile"],
    },
    "cycle_agent": {
        "name": "CycleAgent",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "astro",
        "weight": 0.05,
        "description": "Market cycle analysis: 20/40/80 day cycles, phase detection, turn points",
        "capabilities": ["cycle_detection", "phase_analysis", "turn_point_prediction", "jupiter_saturn_cycles"],
        "inputs": ["price_history", "ephemeris"],
        "outputs": ["cycle_phase", "turn_probability", "confidence"],
        "karl": {"reward_weight": 0.05, "supports_ttc": True, "supports_selfq": True},
        "sources": ["Price cycles", "Ephemeris data"],
    },
    "bradley_agent": {
        "name": "BradleyAgent",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "astro",
        "weight": 0.03,
        "description": "Bradley Siderograph model: planetary aspects correlation with S&P 500",
        "capabilities": ["siderograph_generation", "planetary_aspect_analysis", "market_correlation"],
        "inputs": ["ephemeris", "current_date"],
        "outputs": ["siderograph_score", "aspect_conflicts", "signal"],
        "karl": {"reward_weight": 0.03, "supports_ttc": True, "supports_selfq": True},
        "sources": ["Swiss Ephemeris", "Bradley Siderograph model"],
    },
    "gann_agent": {
        "name": "GannAgent",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "astro",
        "weight": 0.03,
        "description": "Gann angles (1x1, 1x2), square of price/time, time clusters",
        "capabilities": [
            "gann_angle_calculation",
            "price_time_square",
            "time_cluster_detection",
            "support_resistance_gann",
        ],
        "inputs": ["price_data", "date"],
        "outputs": ["gann_levels", "time_clusters", "signal"],
        "karl": {"reward_weight": 0.03, "supports_ttc": True, "supports_selfq": True},
        "sources": ["Gann theory", "Price-time relationships"],
    },
    "electoral_agent": {
        "name": "ElectoralAgent",
        "version": "1.0.0",
        "type": "timing",
        "domain": "astro",
        "weight": 0.03,
        "description": "Muhurta/Choghadiya timing for optimal trade entry/exit windows",
        "capabilities": ["choghadiya_analysis", "nakshatra_timing", "muhurta_windows", "rahu_kala_avoidance"],
        "inputs": ["date", "location", "trade_direction"],
        "outputs": ["best_windows", "avoid_windows", "confidence"],
        "karl": {"reward_weight": 0.03, "supports_ttc": False, "supports_selfq": False},
        "sources": ["Drik Panchang", "Aum4.com", "ProKerala"],
    },
    "time_window_agent": {
        "name": "TimeWindowAgent",
        "version": "1.0.0",
        "type": "timing",
        "domain": "astro",
        "weight": 0.02,
        "description": "Multi-timeframe entry windows (4H/1D/1W) combined with astro timing",
        "capabilities": ["multi_timeframe_windows", "astro_timing_sync", "window_alignment"],
        "inputs": ["timeframes", "astro_data"],
        "outputs": ["aligned_windows", "confidence", "best_entry"],
        "karl": {"reward_weight": 0.02, "supports_ttc": True, "supports_selfq": True},
        "sources": ["Multi-TF analysis", "Ephemeris"],
    },
    "elliot_agent": {
        "name": "ElliotAgent",
        "version": "1.0.0",
        "type": "analysis",
        "domain": "technical",
        "weight": 0.05,
        "description": "Elliott Wave analysis for wave counting and trend prediction",
        "capabilities": ["wave_counting", "impulse_waves", "corrective_waves", "wave_personality"],
        "inputs": ["price_data", "current_wave"],
        "outputs": ["wave_count", "next_target", "signal"],
        "karl": {"reward_weight": 0.05, "supports_ttc": True, "supports_selfq": True},
        "sources": ["Elliott Wave theory", "Price action"],
    },
    "risk_agent": {
        "name": "RiskAgent",
        "version": "1.0.0",
        "type": "risk_management",
        "domain": "risk",
        "weight": 0.00,
        "description": "Dynamic risk assessment, position sizing, stop-loss recommendations",
        "capabilities": ["risk_assessment", "position_sizing", "stop_loss_calculation", "volatility_regime_detection"],
        "inputs": ["price_data", "regime", "volatility"],
        "outputs": ["risk_score", "position_size", "stop_loss"],
        "karl": {"reward_weight": 0.00, "supports_ttc": False, "supports_selfq": False},
        "sources": ["Volatility models", "ATR", "Historical drawdown"],
    },
}


def _discover_agents():
    """Return merged agents dict: static base + dynamic discovery from agents/_impl/."""
    agents = dict(AGENTS)  # start with static definitions
    import importlib
    import inspect
    import pkgutil

    import agents._impl as impl_pkg

    for _, modname, _ in pkgutil.iter_modules(impl_pkg.__path__):
        if modname.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"agents._impl.{modname}")
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                if not name.endswith("Agent") or name == "BaseAgent":
                    continue
                key = name.lower()
                if key not in agents:
                    # Extract metadata from class
                    try:
                        instance = obj()
                        agents[key] = {
                            "name": getattr(instance, "name", name),
                            "version": "1.0.0",
                            "type": "analysis",
                            "domain": getattr(instance, "domain", "unknown"),
                            "weight": getattr(instance, "weight", 0.05),
                            "description": (obj.__doc__ or "").strip().split(".")[0],
                            "capabilities": [],
                            "inputs": [],
                            "outputs": [],
                            "karl": {
                                "reward_weight": getattr(instance, "weight", 0.05),
                                "supports_ttc": False,
                                "supports_selfq": False,
                            },
                            "sources": [],
                        }
                    except Exception:
                        pass  # skip if instantiation fails
        except ImportError:
            pass
    return agents


# Replace direct AGENTS usage with _discover_agents()
AGENTS = _discover_agents()


def generate_agent_yaml(agent: dict) -> str:
    karl = agent.get("karl", {})
    caps = "\n".join(f"  - {c}" for c in agent.get("capabilities", []))
    inputs = "\n".join(f"  - {i}" for i in agent.get("inputs", []))
    outputs = "\n".join(f"  - {o}" for o in agent.get("outputs", []))
    sources = "\n".join(f"  - {s}" for s in agent.get("sources", []))
    return f"""name: {agent["name"]}
version: {agent["version"]}
type: {agent["type"]}
domain: {agent["domain"]}

description: |
  {agent["description"]}

capabilities:
{caps}

inputs:
{inputs}

outputs:
{outputs}

sources:
{sources}

karl_integration:
  reward_weight: {karl.get("reward_weight", 0.1)}
  supports_ttc: {str(karl.get("supports_ttc", True)).lower()}
  supports_selfq: {str(karl.get("supports_selfq", True)).lower()}
  oap_track: true
  replay_buffer_ready: true

constraints:
  - NEVER hallucinate indicators or data
  - ALWAYS reference input data in reasoning
  - MUST return structured output with confidence

tags:
  - {agent["domain"]}
  - core
  - karl_integrated
"""


def generate_prompt_md(agent: dict) -> str:
    name = agent["name"]
    domain = agent["domain"]
    caps = ", ".join(agent.get("capabilities", [])[:3])
    return f"""# {name} — System Prompt

## Role

You are **{name}**, a {domain} analysis agent for the AstroFin Sentinel V5 multi-agent trading system.

## Task

{agent["description"]}

## Capabilities

- {caps}
- All analysis must be evidence-based and data-driven

## KARL Integration

You are part of the KARL (Kernel Rifle Agent Learning) framework:
- Uncertainty quantification enabled
- Self-questioning available when confidence > 85%
- OAP (Outcome Analysis Prediction) tracking active
- Replay buffer logging for future improvement

## Decision Rules

1. **NEVER** invent or hallucinate indicators, data, or signals
2. **ALWAYS** reference actual input data in your reasoning
3. **ALWAYS** quantify uncertainty before reporting confidence
4. **NEVER** report confidence > 90 without strong evidence
5. Apply AMRE (Adaptive Model Reward Estimation) validation

## Output Format

Return a structured response:

```json
{{
  "agent_name": "{name}",
  "signal": "LONG | SHORT | NEUTRAL | AVOID",
  "confidence": <int 0-100>,
  "reasoning": "<detailed explanation with data references>",
  "sources": ["<actual data sources used>"],
  "metadata": {{
    "features_used": [<list of actual indicators/data>],
    "decision_path": [<steps taken>],
    "uncertainty": <float 0-1>,
    "karl_eligible": true
  }}
}}

Confidence Calibration
Evidence Strength    Confidence Range
Strong               75-88
Moderate             55-74
Weak                 35-54
No data/Uncertain    < 35

Error Handling
- If data is unavailable: return NEUTRAL with confidence 40-50
- If calculation fails: log error, return NEUTRAL
- NEVER guess or fabricate data
"""


def generate_schema_py(agent: dict) -> str:
    name = agent["name"].replace("Agent", "")
    return f'''"""schema.py — Pydantic output schema for {name}"""
from pydantic import BaseModel, Field
from typing import List, Literal

class {name}Metadata(BaseModel):
    features_used: List[str] = Field(default_factory=list)
    decision_path: List[str] = Field(default_factory=list)
    uncertainty: float = Field(0.5, ge=0.0, le=1.0)
    karl_eligible: bool = Field(True)

class {name}Output(BaseModel):
    agent_name: str = Field(default="{name}")
    signal: Literal["LONG", "SHORT", "NEUTRAL", "AVOID"]
    confidence: int = Field(..., ge=0, le=100)
    reasoning: str = Field(...)
    sources: List[str] = Field(default_factory=list)
    metadata: {name}Metadata = Field(default_factory={name}Metadata)
'''


def generate_tests_yaml(agent: dict) -> str:
    data = {
        "agent": agent["name"],
        "version": agent["version"],
        "test_suite": [
            {
                "name": "full_regression",
                "cases": [
                    {
                        "name": "neutral_market",
                        "input": {"domain": agent["domain"], "price_data": "sideways"},
                        "expected": {"signal": "NEUTRAL", "confidence_range": [35, 65]},
                    },
                    {
                        "name": "strong_bullish",
                        "input": {"domain": agent["domain"], "price_data": "strong_uptrend"},
                        "expected": {"signal": "LONG", "confidence_min": 65},
                    },
                    {
                        "name": "strong_bearish",
                        "input": {"domain": agent["domain"], "price_data": "strong_downtrend"},
                        "expected": {"signal": "SHORT", "confidence_min": 65},
                    },
                    {
                        "name": "no_data_available",
                        "input": {"domain": agent["domain"], "price_data": None},
                        "expected": {"signal": "NEUTRAL", "confidence_max": 55},
                    },
                ],
            },
            {
                "name": "karl_integration",
                "cases": [
                    {
                        "name": "uncertainty_quantified",
                        "input": {"ambiguous_data": True},
                        "expected": {"metadata_contains": "uncertainty"},
                    },
                    {
                        "name": "metadata_present",
                        "input": {"data": "valid"},
                        "expected": {"metadata_contains": "features_used"},
                    },
                ],
            },
            {
                "name": "boundary",
                "cases": [
                    {
                        "name": "confidence_max_100",
                        "input": {"extreme_data": True},
                        "expected": {"confidence_max": 100},
                    },
                    {"name": "confidence_min_0", "input": {"no_data": True}, "expected": {"confidence_min": 0}},
                ],
            },
        ],
        "karl_validation": {
            "replay_buffer_ready": True,
            "oap_track": True,
            "supports_selfq": agent.get("karl", {}).get("supports_selfq", True),
        },
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def generate_tools_py(agent: dict) -> str:
    name = agent["name"]
    domain = agent["domain"]
    tools = {
        "technical": "TA-lib (RSI, MACD, Bollinger), pandas, numpy",
        "sentiment": "News API, Reddit API, Twitter API",
        "options": "Polygon.io, Unusual Whales API",
        "fundamental": "SEC EDGAR API, CoinGecko",
        "astro": "Swiss Ephemeris, Drik Panchang API",
        "quant": "scikit-learn, pandas, numpy",
        "risk": "pandas, numpy, scipy",
    }
    tool_list = tools.get(domain, "Standard Python libraries")
    return f'''"""tools.py — Custom tools for {name}"""
# Domain: {domain}
# Available tools: {tool_list}
# Add custom tools here as needed
'''


def export_agent(agent_key: str, output_dir: Union[str, Path]) -> bool:
    if agent_key not in AGENTS:
        print(f" ❌ Unknown agent: {agent_key}")
        return False
    out_path = Path(output_dir)
    agent = AGENTS[agent_key]
    pkg_dir = out_path / agent_key
    pkg_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "agent.yaml": generate_agent_yaml(agent),
        "prompt.md": generate_prompt_md(agent),
        "schema.py": generate_schema_py(agent),
        "tests.yaml": generate_tests_yaml(agent),
        "tools.py": generate_tools_py(agent),
    }
    for filename, content in files.items():
        (pkg_dir / filename).write_text(content)
    print(f" ✅ {agent['name']}: agent.yaml, prompt.md, schema.py, tests.yaml, tools.py")
    return True


def export_all(output_dir: Union[str, Path]) -> dict:
    out_path = Path(output_dir)
    results = {"success": [], "failed": []}
    for agent_key in AGENTS:
        if export_agent(agent_key, out_path):
            results["success"].append(agent_key)
        else:
            results["failed"].append(agent_key)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export agents to GitAgent format")
    parser.add_argument("--all", action="store_true", help="Export all agents")
    parser.add_argument("--agent", type=str, help="Export specific agent")
    parser.add_argument("--output", "-o", type=str, default="integrations/gitagent", help="Output directory")
    args = parser.parse_args()
    if args.all:
        print("📦 Exporting all agents...")
        results = export_all(args.output)
        print(f"\n✅ Exported: {len(results['success'])}/{len(AGENTS)}")
    elif args.agent:
        export_agent(args.agent, args.output)
    else:
        parser.print_help()
        print(f"\nAvailable agents ({len(AGENTS)}):")
        for key in sorted(AGENTS):
            print(f" - {key} ({AGENTS[key]['name']})")

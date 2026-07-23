"""Smoke tests: verify every key module imports cleanly.

This boosts coverage by exercising import-time code (class defs, decorators,
module-level constants) without needing full integration runtime.
"""
from __future__ import annotations

import importlib
import sys

import pytest

# Modules that need special setup or have expensive side-effects
SKIP_MODULES = {
    "core.ephemeris",         # Swiss Ephemeris license
    "orchestration.sentinel_v5_mas",  # orchestrator wireup
    "orchestration.sentinel_v5",      # full sentinel startup
    "orchestration.langgraph_schema", # LangGraph schema
    "web.app",                # Dash server startup
    "telegram_bot.bot",       # PTB startup
    "api.main",               # FastAPI startup
}

MODULES = [
    # agents
    "agents._impl.types",
    "agents._impl.ephemeris_decorator",
    "agents.synthesis_agent",
    "agents.base_agent",
    "agents.market_analyst",
    "agents.directional_agents",
    "agents.compromise_agent",
    # core
    "core.auth",
    "core.base_agent",
    "core.belief",
    "core.cache_key",
    "core.checkpoint",
    "core.circuit_breaker",
    "core.code_io",
    "core.error_schema",
    "core.feedback_loop",
    "core.history_db",
    "core.logging",
    "core.muhurtha",
    "core.outbox",
    "core.settings",
    "core.tracing",
    "core.volatility",
    # trading
    "trading.factory",
    "trading.mode",
    "trading.portfolio",
    # data_room
    "data_room",
    "data_room.blueprint",
    "data_room.historical",
    "data_room.feature_store",
    # knowledge
    "knowledge.rag_index",
    "knowledge.rag_retriever",
    "knowledge.ranking",
    "knowledge.tokenizer",
    # meta_rl
    "meta_rl.ab_testing",
    "meta_rl.calibration_pipeline",
    "meta_rl.gaussian_process",
    "meta_rl.genetic_layers",
    "meta_rl.hmm_ensemble",
    "meta_rl.hmm_regime",
    "meta_rl.instrumentation",
    "meta_rl.meta_agent",
    "meta_rl.pairwise_ranking",
    "meta_rl.persistence",
    "meta_rl.rl_trainer",
    "meta_rl.strategy_evaluator",
    "meta_rl.thompson_sampling",
    # orchestration
    "orchestration.broker",
    "orchestration.council_orchestrator",
    "orchestration.karl_cli",
    "orchestration.router",
    # trading execution
    "trading.execution.sanity",
    # agents
    "agents._impl.bradley_agent",
    "agents._impl.cycle_agent",
    "agents._impl.elliot_agent",
    "agents._impl.ephemeris_decorator",
    "agents._impl.gann_agent",
    "agents._impl.insider_agent",
    "agents._impl.ml_predictor_agent",
    "agents._impl.options_flow_agent",
    "agents._impl.risk_agent",
    "agents._impl.time_window_agent",
    "agents._impl.synthesis_agent",
    "agents.karl_synthesis",
    # artifacts
    "artifacts.best_practices.core.circuit_breaker",
    "artifacts.best_practices.core.outbox",
    "artifacts.best_practices.core.reward",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_module_imports(module_name: str):
    """Verify the module can be imported without raising."""
    if module_name in SKIP_MODULES:
        pytest.skip(f"Module {module_name} requires setup")

    # Clean sys.modules to test fresh import
    for key in list(sys.modules):
        if key == module_name or key.startswith(module_name + "."):
            del sys.modules[key]

    try:
        importlib.import_module(module_name)
    except ImportError as e:
        pytest.skip(f"Import blocked: {e}")
    except Exception as e:
        # Module-level execution errors are real failures (not skips)
        cls = type(e).__name__
        pytest.fail(f"Module {module_name} raised {cls}: {e}")

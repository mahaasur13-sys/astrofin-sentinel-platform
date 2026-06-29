"""
import pytest
PR1 verification — runs in isolation by stubbing the pre-existing
broken `meta_rl` import chain (caused by missing `integrations.gitagent`).

This is a runtime harness, not a normal pytest test: we need to stub
`meta_rl.__init__` (and its broken transitive import) before any
project code is loaded. Once a proper conftest at tests/conftest.py
stubs the chain, this file can be reduced to a normal test module.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import types
from pathlib import Path

WS = Path("/home/workspace")

# ── 1. Stub the broken chain BEFORE any user code imports it ─────────────
# (Pre-existing project issue: integrations.gitagent is mostly empty.)
for stub_name in [
    "integrations",
    "integrations.gitagent",
    "integrations.gitagent.validators",
    "integrations.gitagent.validators.agent_validator",
]:
    if stub_name not in sys.modules:
        m = types.ModuleType(stub_name)
        if stub_name.endswith("agent_validator"):
            class _Stub:
                def __init__(self, *a, **k): pass
            m.AgentYamlValidator = _Stub
        sys.modules[stub_name] = m

# ── 2. Stub tools.metrics_server which pulls in meta_rl.metrics ────────
class _StubModule(types.ModuleType):
    def __getattr__(self, name):
        return _StubModule(name)

sys.modules.setdefault("tools", _StubModule("tools"))
sys.modules["tools.metrics_server"] = _StubModule("tools.metrics_server")

# ── 3. Now import in dependency order ────────────────────────────────────
sys.path.insert(0, str(WS))

from core.base_agent import AgentResponse, SignalDirection  # noqa: E402
from agents._impl.compromise_agent import (  # noqa: E402
    CompromiseAgent,
    run_compromise_agent,
)

logging.basicConfig(level=logging.WARNING)


# ── Helpers ─────────────────────────────────────────────────────────────
def mk(agent_name, signal, conf, *, reasoning="", meta=None):
    """Build a minimal agent signal (dict or AgentResponse)."""
    if isinstance(signal, str):
        signal = SignalDirection(signal)
    return AgentResponse(
        agent_name=agent_name,
        signal=signal,
        confidence=conf,
        reasoning=reasoning,
        sources=[],
        metadata=meta or {},
    )


# ── Tests ───────────────────────────────────────────────────────────────
async def main():
    agent = CompromiseAgent()
    print(f"OK | instantiated {agent.name} domain={agent.domain} weight={agent.weight}")

    # T1 — empty signals → no compromise
    r = await agent.run({"symbol": "BTCUSDT", "current_price": 50000, "all_signals": []})
    assert r.signal == SignalDirection.NEUTRAL
    assert r.metadata.get("compromise_active") is False
    assert r.metadata.get("reason_code") == "INSUFFICIENT_SIGNALS"
    print("T1 OK | empty signals → NEUTRAL, no compromise")

    # T2: all agree → no compromise, but report dominant signal
    agree = [
        {"agent_name": "BradleyAgent", "signal": "LONG", "confidence": 80},
        {"agent_name": "GannAgent", "signal": "LONG", "confidence": 70},
    ]
    r = await agent.run({"symbol": "BTCUSDT", "current_price": 50000, "all_signals": agree})
    assert r.signal == SignalDirection.NEUTRAL, f"T2: expected NEUTRAL (abstain), got {r.signal}"
    assert r.metadata.get("compromise_active") is False
    assert r.metadata.get("reason_code") == "CONSENSUS"
    assert r.metadata.get("dominant", {}).get("agent") == "BradleyAgent"
    assert r.metadata.get("dominant", {}).get("signal") == "LONG"
    print("T2 OK | consensus LONG → abstains, reports dominant=BradleyAgent LONG@80")

    # T3 — Astro LONG@85 vs Quant SHORT@70 → compromise should be NEUTRAL@mid
    conflict = [
        mk("AstroCouncil", "LONG", 85),
        mk("QuantAgent", "SHORT", 70),
        mk("MacroAgent", "LONG", 55),
    ]
    r = await agent.run({"symbol": "BTCUSDT", "current_price": 50000, "all_signals": conflict})
    assert r.signal == SignalDirection.NEUTRAL, f"expected NEUTRAL, got {r.signal}"
    assert r.metadata.get("compromise_active") is True
    assert r.metadata.get("reason_code") == "MULTI_CATEGORY_CONFLICT"
    assert 30 <= r.confidence <= 80, f"expected mid-conf ≤ 80, got {r.confidence}"
    assert "LONG" in r.reasoning and "SHORT" in r.reasoning
    print(f"T3 OK | Astro LONG@85 vs Quant SHORT@70 → NEUTRAL@{r.confidence}, compromise active")
    print(f"     reasoning: {r.reasoning[:120]}…")

    # T4 — strong consensus, no compromise
    same_dir = [mk("AstroCouncil", "LONG", 85), mk("QuantAgent", "LONG", 85), mk("MacroAgent", "LONG", 85)]
    r = await agent.run({"symbol": "BTCUSDT", "current_price": 50000, "all_signals": same_dir})
    assert r.signal == SignalDirection.NEUTRAL, f"expected NEUTRAL (abstain), got {r.signal}"
    assert r.metadata.get("compromise_active") is False
    assert r.metadata.get("reason_code") == "CONSENSUS"
    assert r.metadata.get("dominant", {}).get("confidence") == 85
    print("T4 OK | consensus LONG → abstains, reports dominant=AstroCouncil LONG@85")

    # T5 — degraded: analyze raises non-ephemeris exception
    class Boom(CompromiseAgent):
        async def analyze(self, state):
            raise RuntimeError("simulated upstream failure")
    r = await Boom().run({"symbol": "BTCUSDT", "current_price": 50000, "all_signals": conflict})
    assert r.signal == SignalDirection.NEUTRAL
    assert r.metadata.get("degraded") is True
    assert r.metadata.get("degradation_reason") == "UNKNOWN"
    print("T5 OK | raised exception → degraded UNKNOWN, NEUTRAL")

    # T6 — runtime: only 1 signal — no compromise
    r = await agent.run({"symbol": "BTCUSDT", "current_price": 50000, "all_signals": [mk("AstroCouncil", "LONG", 80)]})
    assert r.metadata.get("compromise_active") is False
    assert r.metadata.get("reason_code") == "SINGLE_SIGNAL"
    print("T6 OK | single signal → no compromise (single_signal)")

    # T7 — runner entry-point
    out = await run_compromise_agent({"symbol": "BTCUSDT", "current_price": 50000, "all_signals": conflict})
    assert "compromise_signal" in out
    print("T7 OK | run_compromise_agent returns compromise_signal dict")

    print("\n=== PR1: ALL 7 CASES PASS ===")


asyncio.run(main())


# ─── BlackRock Six Tests (mixin) ─────────────────────────────────────────────
# Imported at the bottom so it doesn't interfere with the PR1 stubs above.

if True:  # keep block scoped
    from tests.agent_test_base import AgentTestContract, DegradedContract  # noqa: E402
    from agents._impl.compromise_agent import CompromiseAgent  # noqa: E402

    class TestCompromiseAgentBlackRock(AgentTestContract, DegradedContract):
        agent_class = CompromiseAgent

        async def test_happy_path(self, agent, happy_state): return await super().test_happy_path(agent, happy_state)
        async def test_empty_state(self, agent): return await super().test_empty_state(agent)
        async def test_malformed_state(self, agent): return await super().test_malformed_state(agent)
        async def test_data_source_unavailable(self, agent, happy_state): return await super().test_data_source_unavailable(agent, happy_state)
        async def test_missing_ephemeris(self, agent, happy_state): return await super().test_missing_ephemeris(agent, happy_state)
        async def test_large_input(self, agent): return await super().test_large_input(agent)

"""Main AstroCouncil (agents/astro_council_agent.py), variant A: astro council of
ASTRO_POOL members; weights ONLY from synthesis/weights.get_agent_weight,
normalised over the five members. Network mocked; no real I/O."""
from __future__ import annotations

import ast
import asyncio
import logging
from pathlib import Path
from unittest import mock

import httpx
import pytest

import agents.astro_council_agent as aca
from agents._impl.synthesis import weights as W
from agents.astro_council_agent import ASTRO_MEMBERS, AstroCouncilAgent
from core.base_agent import AgentResponse, SignalDirection
from core.thompson import ASTRO_POOL


def _resp(name, sig, conf=100, **meta):
    return AgentResponse(agent_name=name, signal=sig, confidence=conf, reasoning="t", sources=[], metadata=meta)


def test_members_equal_astro_pool_and_registry():
    c = AstroCouncilAgent()
    c._register_sub_agents()
    assert set(ASTRO_MEMBERS) == set(ASTRO_POOL.agents) == set(c._sub_agents)


def test_member_weights_from_single_source_normalised():
    c = AstroCouncilAgent()
    total = sum(W.get_agent_weight(n) for n in ASTRO_MEMBERS)
    got = {n: c._weight_for(n) for n in ASTRO_MEMBERS}
    assert sum(got.values()) == pytest.approx(1.0)
    for n in ASTRO_MEMBERS:
        assert got[n] == pytest.approx(W.AGENT_WEIGHTS[n] / total)


def test_get_agent_weight_short_full_and_sentiment():
    assert W.get_agent_weight("Fundamental") == W.get_agent_weight("FundamentalAgent") == 0.20
    assert W.get_agent_weight("SentimentAgent") == pytest.approx(0.10)
    assert W.get_agent_weight("MarketAnalyst") == W.CATEGORY_WEIGHTS["technical"]


def test_unknown_agent_zero_and_logged(caplog):
    with caplog.at_level(logging.ERROR):
        assert W.get_agent_weight("GhostAgent") == 0.0
        assert AstroCouncilAgent()._weight_for("FundamentalAgent") == 0.0  # not a council member
    assert sum("unknown_agent_weight" in r.getMessage() for r in caplog.records) >= 2


def test_council_defines_no_weight_numbers():
    assert not hasattr(aca, "HYBRID_WEIGHTS") and not hasattr(aca, "_AGENT_CATEGORY_MAP")
    tree = ast.parse(Path(aca.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "agents._impl.synthesis.weights":
            assert {a.name for a in node.names} == {"get_agent_weight"}
        if isinstance(node, ast.Dict) and node.values and all(
                isinstance(v, ast.Constant) and isinstance(v.value, float) for v in node.values) and any(
                v.value != 0.0 for v in node.values):
            pytest.fail(f"weight-like dict literal at line {node.lineno}")


@pytest.mark.parametrize("raw,exp", [("BUY", SignalDirection.LONG), ("STRONG_BUY", SignalDirection.LONG),
                                     ("SELL", SignalDirection.SHORT), ("STRONG_SELL", SignalDirection.SHORT)])
def test_buy_sell_mapping(raw, exp):
    out = AstroCouncilAgent()._weighted_vote([_resp(n, raw, 90) for n in ASTRO_MEMBERS])
    assert out.signal == exp


def test_no_data_members_abstain_and_quorum():
    L, N = SignalDirection.LONG, SignalDirection.NEUTRAL
    c = AstroCouncilAgent()
    # 1 member with data (LONG) + 4 no_data -> quorum not met -> NEUTRAL
    rs = [_resp("TimeWindowAgent", L, 80)] + [_resp(n, N, 20, no_data=True) for n in ASTRO_MEMBERS[:4]]
    assert c._weighted_vote(rs).signal == N
    # all no_data -> NEUTRAL, flagged no_data so synthesis abstains
    out = c._weighted_vote([_resp(n, N, 20, no_data=True) for n in ASTRO_MEMBERS])
    assert out.signal == N and out.metadata.get("no_data") is True
    # 3 with data agree LONG -> LONG
    rs = [_resp(n, L, 80) for n in ASTRO_MEMBERS[:3]] + [_resp(n, N, 20, no_data=True) for n in ASTRO_MEMBERS[3:]]
    assert c._weighted_vote(rs).signal == L


def _fake(mode):
    async def fake(self, url, *a, **k):
        req = httpx.Request("GET", str(url))
        if mode == "dns":
            raise httpx.ConnectError("dns timeout", request=req)
        if mode == "empty":
            return httpx.Response(200, json={"code": "0", "data": []}, request=req)
        if mode == "code_err":
            return httpx.Response(200, json={"code": "50011", "data": []}, request=req)
        return httpx.Response(500, text="cf", request=req)
    return fake


@pytest.mark.parametrize("mode", ["dns", "empty", "code_err", "http500"])
@pytest.mark.parametrize("chog", ["Amrita", "Marana", "Kaala"])
def test_all_okx_down_council_is_neutral(mode, chog):
    st = {"symbol": "BTCUSDT", "current_price": 50000}
    with mock.patch.object(httpx.AsyncClient, "get", _fake(mode)), \
         mock.patch.object(httpx.AsyncClient, "post", _fake(mode)), \
         mock.patch("astrology.vedic.get_choghadiya", return_value={"name": chog, "quality": "x", "score": 5.0}):
        r = asyncio.run(AstroCouncilAgent().run(dict(st)))
    assert str(getattr(r.signal, "value", r.signal)) == "NEUTRAL", r.reasoning


def test_run_astro_flow_selects_real_members():
    """run_astro_flow passes ASTRO_POOL names; the council must actually run them (not empty)."""
    from orchestration.result_aggregator import run_astro_flow

    called = []

    async def fake_run(self, state):
        called.append(type(self).__name__)
        return _resp(type(self).__name__, SignalDirection.LONG, 80)

    import agents._impl.bradley_agent as b, agents._impl.cycle_agent as cy, agents._impl.elliot_agent as e
    import agents._impl.gann_agent as g, agents._impl.time_window_agent as tw
    with mock.patch.object(b.BradleyAgent, "run", fake_run), mock.patch.object(cy.CycleAgent, "run", fake_run), \
         mock.patch.object(e.ElliotAgent, "run", fake_run), mock.patch.object(g.GannAgent, "run", fake_run), \
         mock.patch.object(tw.TimeWindowAgent, "run", fake_run):
        out = asyncio.run(run_astro_flow({"symbol": "BTCUSDT"}, selected_agents=list(ASTRO_POOL.agents)))
    sig = out["astro_council_signal"]
    assert sorted(called) == sorted(ASTRO_MEMBERS)
    assert sig["signal"] == "LONG" and sig["metadata"]["total_agents"] == 5


def test_live_path_run_karl_sentinel_v5_astro_council_not_empty():
    """Live entry (sentinel_v5.run_karl_sentinel_v5) with mocked network + stubbed DB:
    AstroCouncil now runs its 5 members instead of returning an empty NEUTRAL 50."""
    import random

    import orchestration.sentinel_v5 as sv

    rnd = random.Random(1)

    def candles(n=400):
        p, rows = 50000.0, []
        for i in range(n):
            p *= 1 + rnd.uniform(-0.02, 0.021)
            rows.append([str(1700000000000 + i * 86400000), str(p), str(p * 1.01), str(p * 0.99), str(p), "100"])
        return list(reversed(rows))

    async def fake(self, url, *a, **k):
        req = httpx.Request("GET", str(url))
        u = str(url)
        if "candles" in u:
            return httpx.Response(200, json={"code": "0", "data": candles()}, request=req)
        if "binance" in u:
            return httpx.Response(200, json={"price": "50000"}, request=req)
        return httpx.Response(200, json={}, request=req)

    seen = {}
    orig = sv.KARLSynthesisAgent.run

    async def karl_run(self, state):
        for s in state.get("all_signals", []):
            name = s.get("agent_name") if isinstance(s, dict) else getattr(s, "agent_name", None)
            if name == "AstroCouncil":
                seen["astro"] = s if isinstance(s, dict) else s.to_dict()
        return await orig(self, state)

    patches = [mock.patch.object(httpx.AsyncClient, "get", fake), mock.patch.object(httpx.AsyncClient, "post", fake),
               mock.patch.object(sv.KARLSynthesisAgent, "run", karl_run),
               mock.patch.object(sv, "save_session", mock.MagicMock()),
               mock.patch.object(sv, "update_beliefs_from_session", mock.MagicMock()),
               # candles() are dated from 1700000000000 (daily, 400 bars): freeze the freshness clock after the newest
               mock.patch("core.market_freshness._now", return_value=1700000000 + 399 * 86400 + 3600)]
    if hasattr(sv, "init_db_if_needed"):
        patches.append(mock.patch.object(sv, "init_db_if_needed", mock.MagicMock()))
    for p in patches:
        p.start()
    try:
        asyncio.run(sv.run_karl_sentinel_v5(user_query="", symbol="BTCUSDT", timeframe="SWING"))
    finally:
        for p in patches:
            p.stop()
    astro = seen["astro"]
    assert astro["metadata"]["total_agents"] >= 4  # Thompson min_select=4 of ASTRO_POOL
    assert "All astro agents failed" not in (astro.get("reasoning") or "")

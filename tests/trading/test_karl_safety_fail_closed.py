"""Fail-closed regressions: KARL synthesis error, SafetyGate exception, kill-switch error.

KARL: an exception in KARLSynthesisAgent must not yield a tradable signal
(previously fell back to the base SynthesisAgent = fail-open).
SafetyGate / kill switch: already fail-closed on 7dc1f7a3; these tests pin it.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from trading.safety_gate import SafetyGate, SafetyStatus


def _boom(*a, **k):
    raise RuntimeError("backend down")


async def _run_karl_with_failing_agent():
    from orchestration import sentinel_v5 as _sv

    route = MagicMock()
    route.query_type.value = "single_symbol"
    route.symbols = ["BTCUSDT"]
    route.timeframe = "SWING"
    karl = MagicMock()
    karl.run = AsyncMock(side_effect=RuntimeError("karl exploded"))
    fallback = MagicMock()
    fallback.run = AsyncMock(return_value={"signal": "LONG", "confidence": 95})
    beliefs = MagicMock()
    with (
        patch.object(_sv, "route_query", return_value=route),
        patch.object(_sv, "_fetch_price", AsyncMock(return_value=50000)),
        patch.object(_sv, "get_oap_optimizer", MagicMock()),
        patch.object(_sv, "_compute_oap_adjustments", MagicMock(return_value=None)),
        patch.object(_sv, "KARLSynthesisAgent", return_value=karl),
        patch.object(_sv, "SynthesisAgent", return_value=fallback),
        patch.object(_sv, "save_session", MagicMock(return_value="s")),
        patch.object(_sv, "update_beliefs_from_session", beliefs),
    ):
        out = await _sv.run_karl_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
            current_price=50000,
            include_technical=False,
            include_astro=False,
            include_macro=False,
            persist=True,
            session_id="sess-karl-fail",
        )
    return out, beliefs


@pytest.mark.asyncio
async def test_karl_error_is_fail_closed_no_trade_signal():
    out, beliefs = await _run_karl_with_failing_agent()
    rec = out["final_recommendation"]
    assert rec["signal"] == "NEUTRAL", rec
    assert rec["confidence"] == 0
    assert rec.get("blocked") is True and rec.get("blocked_reason") == "karl_error"
    assert out.get("karl_failed") is True
    beliefs.assert_not_called()  # no learning from a synthetic fail-closed decision


def test_safety_gate_internal_exception_blocks(monkeypatch):
    gate = SafetyGate(portfolio=SimpleNamespace(total_value=100_000.0, positions={}))
    monkeypatch.setattr(SafetyGate, "_check_impl", _boom)
    d = gate.check({"signal": "LONG", "confidence": 90}, {}, current_price=50_000.0)
    assert d.status is SafetyStatus.BLOCKED, d
    assert d.blocked_reason == "safety_gate_error"


def test_kill_switch_check_error_blocks(monkeypatch):
    from trading.risk_v2 import RiskEngineV2

    gate = SafetyGate(portfolio=SimpleNamespace(total_value=100_000.0, positions={}))
    monkeypatch.setattr(RiskEngineV2, "check_kill_switch", _boom)
    d = gate._check_risk("BTCUSDT", "LONG", 90, 0.1, 50_000.0)
    assert d.status is SafetyStatus.BLOCKED, d
    assert d.blocked_reason == "kill_switch_error"

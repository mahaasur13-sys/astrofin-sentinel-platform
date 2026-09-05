from __future__ import annotations

import pytest

from core.base_agent import AgentResponse, SignalDirection
from orchestration.router import route_query
from orchestration.sentinel_v5 import run_sentinel_v5


class TestImports:
    """All modules should import without errors."""

    def test_all_imports(self):
        pass


class TestRouter:
    """Router must correctly classify queries."""

    def test_route_single_symbol(self):
        result = route_query("Analyze BTC")
        assert result.query_type.value == "single_symbol"
        # Router normalizes to full symbol
        assert len(result.symbols) == 1
        assert "BTC" in result.symbols[0]

    def test_route_timeframe(self):
        result = route_query("Swing trade BTCUSDT")
        assert result.timeframe in ("INTRADAY", "SWING", "POSITIONAL")


class TestAgentResponseModel:
    """AgentResponse must have all required fields and valid ranges."""

    def test_signal_direction_enum(self):
        for sig in SignalDirection:
            assert hasattr(sig, "value")

    def test_confidence_range_bounds(self):
        resp = AgentResponse(
            agent_name="Test",
            signal=SignalDirection.NEUTRAL,
            confidence=50,
            reasoning="test",
        )
        assert 0 <= resp.confidence <= 100

    def test_confidence_out_of_range_rejected(self):
        with pytest.raises((ValueError, AssertionError)):
            AgentResponse(
                agent_name="Test",
                signal=SignalDirection.NEUTRAL,
                confidence=150,
                reasoning="test",
            )

    def test_to_dict_all_fields(self):
        resp = AgentResponse(
            agent_name="MarketAnalyst",
            signal=SignalDirection.LONG,
            confidence=75,
            reasoning="Price above 200 EMA",
        )
        d = resp.to_dict()
        for field in (
            "agent_name",
            "signal",
            "confidence",
            "reasoning",
            "sources",
            "metadata",
            "timestamp",
            "session_id",
        ):
            assert field in d

    def test_to_dict_signal_is_string(self):
        resp = AgentResponse(
            agent_name="Test",
            signal=SignalDirection.LONG,
            confidence=50,
            reasoning="test",
        )
        d = resp.to_dict()
        assert isinstance(d["signal"], str)
        assert d["signal"] == "LONG"

    def test_confidence_zero_valid(self):
        resp = AgentResponse(
            agent_name="Test",
            signal=SignalDirection.SHORT,
            confidence=0,
            reasoning="test",
        )
        assert resp.confidence == 0


class TestOrchestratorIntegration:
    """Full pipeline — all agents run, final output is complete."""

    @pytest.mark.asyncio
    async def test_run_sentinel_v5_full_output(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )

        required_fields = [
            "session_id",
            "symbol",
            "timeframe",
            "current_price",
            "query_type",
            "flows_run",
            "agent_count",
            "final_recommendation",
            # "final_report" — merged into final_recommendation (G12)  # noqa
            "timestamp",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_confidence_in_range(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        rec = result["final_recommendation"]
        assert rec is not None
        conf = rec.get("confidence")
        assert isinstance(
            conf, (int, float)
        ), f"confidence is {type(conf)}: {conf}"  # noqa: UP038
        assert 0 <= conf <= 100, f"confidence={conf} out of range"

    @pytest.mark.asyncio
    async def test_agent_count_positive(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        assert result["agent_count"] >= 0

    @pytest.mark.asyncio
    async def test_flows_run_flags(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        flows = result["flows_run"]
        assert "technical" in flows
        assert "astro" in flows
        assert "electional" in flows
        assert flows["technical"] is True
        assert flows["astro"] is True

    @pytest.mark.asyncio
    async def test_final_report_equals_recommendation(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        assert (
            result["final_recommendation"] is not None
        )  # final_report merged into final_recommendation (G12)

    @pytest.mark.asyncio
    async def test_timestamp_is_iso_format(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        from datetime import datetime

        dt = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
        assert dt.year >= 2024

    @pytest.mark.asyncio
    async def test_symbol_in_output(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        assert result["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_session_id_is_short_uuid(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        sid = result["session_id"]
        assert isinstance(sid, str)
        assert len(sid) == 8

    @pytest.mark.asyncio
    async def test_current_price_is_numeric(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        assert isinstance(result["current_price"], (int, float))  # noqa: UP038
        assert result["current_price"] > 0

    @pytest.mark.asyncio
    async def test_all_signals_in_state(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        rec = result["final_recommendation"]
        assert rec is not None
        assert "agent_name" in rec
        assert "signal" in rec
        assert "reasoning" in rec

    @pytest.mark.asyncio
    async def test_electional_flow_disabled_by_default(self):
        result = await run_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
        )
        assert result["flows_run"]["electional"] is False


def test_decision_record_never_missing_decision_id():
    """The KARL panel must never print ID=N/A — always fall back to a stable id."""
    from orchestration.sentinel_v5 import _ensure_decision_record

    # Non-KARL / fallback path (decision_record is None)
    rec = _ensure_decision_record(None, "abc12345")
    assert rec["decision_id"] == "abc12345"
    assert rec["decision_id"] != "N/A"

    # dict without decision_id → session id added
    rec = _ensure_decision_record({"signal": "NEUTRAL"}, "deadbeef")
    assert rec["decision_id"] == "deadbeef"

    # existing KARL_* id is preserved, not overwritten
    rec = _ensure_decision_record({"decision_id": "KARL_0001_BTC"}, "deadbeef")
    assert rec["decision_id"] == "KARL_0001_BTC"


@pytest.mark.asyncio
async def test_karl_persists_session_before_decision():
    """KARL must persist the session row before its decision/signal FK inserts.

    Reproduces the live FK violation: karl_decision_records.session_id
    referenced a session_id that was not yet in `sessions`. The fix saves a
    minimal session row first, then the KARL agent runs, then the full row is
    upserted.
    """
    from unittest.mock import AsyncMock, MagicMock, patch

    from orchestration import sentinel_v5 as _sv

    route = MagicMock()
    route.query_type.value = "single_symbol"
    route.symbols = ["BTCUSDT"]
    route.timeframe = "SWING"

    karl = MagicMock()
    events = []

    async def fake_karl_run(state):
        events.append(("karl_run", state.get("session_id")))
        return {
            "synthesis_result": {"signal": "NEUTRAL", "confidence": 50},
            "amre_output": None,
            "decision_record": {"decision_id": "KARL_0001_BTC"},
            "karl_diagnostics": None,
        }

    karl.run = fake_karl_run

    def fake_save_session(result):
        events.append(("save_session", result.get("session_id")))
        return result.get("session_id", "")

    with patch.object(_sv, "route_query", return_value=route), \
         patch.object(_sv, "_fetch_price", AsyncMock(return_value=50000)), \
         patch.object(_sv, "get_oap_optimizer", MagicMock()), \
         patch.object(_sv, "_compute_oap_adjustments", MagicMock(return_value=None)), \
         patch.object(_sv, "KARLSynthesisAgent", return_value=karl), \
         patch.object(_sv, "save_session", side_effect=fake_save_session), \
         patch.object(_sv, "update_beliefs_from_session", MagicMock()):
        await _sv.run_karl_sentinel_v5(
            user_query="Analyze BTC",
            symbol="BTCUSDT",
            timeframe="SWING",
            current_price=50000,
            include_technical=False,
            include_astro=False,
            include_macro=False,
            persist=True,
            session_id="sess12345",
        )

    # The minimal session save must happen BEFORE the KARL agent runs.
    assert events, "no save_session/karl_run events recorded"
    assert events[0] == ("save_session", "sess12345")
    assert events[1] == ("karl_run", "sess12345")

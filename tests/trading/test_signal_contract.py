"""Unified Signal contract (trading/contracts): schema, Decimal boundary, refusals, adapter."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trading.contracts import (
    SCHEMA_VERSION,
    Evidence,
    HypothesisStatus,
    Side,
    Signal,
    SignalRefused,
    Verdict,
    build_signal,
    from_signal_dict,
)

UTC = timezone.utc
T_AS_OF = datetime(2026, 10, 28, 0, 0, tzinfo=UTC)
T_CREATED = datetime(2026, 10, 28, 0, 5, tzinfo=UTC)


def _ev():
    return [Evidence(source="QuantAgent", kind="reasoning", detail="EMA cross")]


def _fields(**over):
    f = dict(
        symbol="BTCUSDT",
        side="LONG",
        verdict="ENTER",
        strategy_id="ema_cross",
        strategy_version="1.2.0",
        created_at=T_CREATED,
        as_of=T_AS_OF,
        confidence="0.7",
        evidence=_ev(),
        hypothesis_status="CONFIRMED",
        hypothesis_check="wf-oos:ema_cross:1.2.0",
    )
    f.update(over)
    return {k: v for k, v in f.items() if v is not None}


# ── happy path ───────────────────────────────────────────────────────────────


def test_build_valid_signal_types():
    s = build_signal(**_fields(entry_price="50000.10", stop_price=49000, target_price=52000.5, quantity="0.02"))
    assert isinstance(s, Signal)
    assert s.side is Side.LONG and s.verdict is Verdict.ENTER and s.is_actionable
    assert s.confidence == Decimal("0.7")
    assert s.entry_price == Decimal("50000.10") and isinstance(s.stop_price, Decimal)
    assert s.target_price == Decimal("52000.5")  # float via str(): no binary noise
    assert s.quantity == Decimal("0.02")
    assert s.created_at.tzinfo == UTC and s.as_of.tzinfo == UTC
    assert s.schema_version == "1.1" == SCHEMA_VERSION


def test_signal_is_immutable():
    s = build_signal(**_fields())
    with pytest.raises(Exception):
        s.symbol = "ETHUSDT"  # type: ignore[misc]


def test_timestamps_normalised_to_utc():
    msk = timezone(timedelta(hours=3))
    s = build_signal(**_fields(as_of=datetime(2026, 10, 28, 3, 0, tzinfo=msk), created_at="2026-10-28T00:05:00Z"))
    assert s.as_of == T_AS_OF and s.as_of.utcoffset() == timedelta(0)
    assert s.created_at == T_CREATED


def test_signal_id_deterministic_and_identity_based():
    a = build_signal(**_fields())
    b = build_signal(**_fields(confidence="0.9", created_at=T_CREATED + timedelta(seconds=30)))
    c = build_signal(**_fields(strategy_version="1.3.0"))
    assert a.signal_id == b.signal_id  # same decision on same bar
    assert a.signal_id != c.signal_id
    assert len(a.signal_id) == 64


def test_to_dict_serialises_decimals_as_str():
    d = build_signal(**_fields(entry_price="50000.10")).to_dict()
    assert d["confidence"] == "0.7" and d["entry_price"] == "50000.10"
    assert d["evidence"][0]["source"] == "QuantAgent"
    assert d["signal_id"] and d["schema_version"] == "1.1"
    assert d["hypothesis_status"] == "CONFIRMED" and d["hypothesis_check"] == "wf-oos:ema_cross:1.2.0"


@pytest.mark.parametrize("side,verdict", [("FLAT", "HOLD"), ("FLAT", "AVOID"), ("SHORT", "ENTER")])
def test_valid_side_verdict_combinations(side, verdict):  # status CONFIRMED
    assert build_signal(**_fields(side=side, verdict=verdict)).verdict.value == verdict


# ── refusals: missing ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "field",
    [
        "symbol", "side", "verdict", "strategy_id", "strategy_version", "created_at", "as_of", "confidence",
        "evidence", "hypothesis_status", "hypothesis_check",
    ],
)
def test_missing_required_field_refused(field):
    f = _fields()
    f.pop(field)
    with pytest.raises(SignalRefused) as ei:
        build_signal(**f)
    assert ei.value.missing == (field,)
    assert field in str(ei.value)


def test_all_missing_listed_at_once():
    with pytest.raises(SignalRefused) as ei:
        build_signal()
    assert set(ei.value.missing) == {
        "symbol", "side", "verdict", "strategy_id", "strategy_version", "created_at", "as_of", "confidence", "evidence",
        "hypothesis_status",
    }


# ── refusals: invalid ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "over,field",
    [
        ({"symbol": "  "}, "symbol"),
        ({"strategy_version": 3}, "strategy_version"),
        ({"side": "UP"}, "side"),
        ({"verdict": "MAYBE"}, "verdict"),
        ({"confidence": "1.5"}, "confidence"),
        ({"confidence": -0.1}, "confidence"),
        ({"confidence": float("nan")}, "confidence"),
        ({"confidence": True}, "confidence"),
        ({"confidence": "abc"}, "confidence"),
        ({"created_at": datetime(2026, 10, 28, 0, 5)}, "created_at"),  # naive
        ({"as_of": "yesterday"}, "as_of"),
        ({"as_of": T_CREATED + timedelta(minutes=1)}, "as_of"),  # look-ahead
        ({"evidence": []}, "evidence"),
        ({"evidence": ["text"]}, "evidence"),
        ({"evidence": [Evidence(source="", kind="x")]}, "evidence"),
        ({"side": "FLAT", "verdict": "ENTER"}, "side"),
        ({"side": "LONG", "verdict": "HOLD"}, "side"),
        ({"entry_price": 0}, "entry_price"),
        ({"quantity": "-1"}, "quantity"),
        ({"quantity": float("inf")}, "quantity"),
        ({"entry_price": 50_000, "stop_price": 51_000}, "stop_price"),  # LONG stop above entry
        ({"entry_price": 50_000, "target_price": 49_000}, "target_price"),
        ({"side": "SHORT", "entry_price": 50_000, "stop_price": 49_000}, "stop_price"),
        ({"side": "SHORT", "entry_price": 50_000, "target_price": 51_000}, "target_price"),
        ({"leverage": 10}, "leverage"),  # unknown field
        ({"hypothesis_status": "PROBABLY"}, "hypothesis_status"),
        ({"hypothesis_status": "REFUTED"}, "hypothesis_status"),  # ENTER needs CONFIRMED
        ({"hypothesis_status": "INSUFFICIENT_DATA"}, "hypothesis_status"),  # ENTER needs CONFIRMED
        ({"hypothesis_check": "   "}, "hypothesis_check"),
        ({"hypothesis_check": 7}, "hypothesis_check"),
    ],
)
def test_invalid_field_refused(over, field):
    with pytest.raises(SignalRefused) as ei:
        build_signal(**_fields(**over))
    assert field in ei.value.invalid, ei.value
    assert ei.value.missing == ()


def test_short_with_consistent_levels_ok():
    s = build_signal(**_fields(side="SHORT", entry_price=50_000, stop_price=51_000, target_price=48_000))
    assert s.stop_price > s.entry_price > s.target_price


# ── adapter: legacy dicts ───────────────────────────────────────────────────


def _agent_dict(**over):
    d = {
        "agent_name": "QuantAgent",
        "signal": "LONG",
        "confidence": 72,
        "reasoning": "EMA cross up",
        "sources": ["binance:BTCUSDT:1d"],
        "metadata": {},
        "timestamp": "2026-10-28T00:05:00+00:00",
        "session_id": "abcd1234",
    }
    d.update(over)
    return d


def _ctx(**over):
    c = dict(symbol="BTCUSDT", strategy_id="council", strategy_version="5.0.0", as_of=T_AS_OF,
             hypothesis_status="CONFIRMED", hypothesis_check="wf-oos:council:5.0.0")
    c.update(over)
    return c


def test_adapter_agent_response_dict():
    s = from_signal_dict(_agent_dict(), confidence_scale="percent", **_ctx())
    assert s.side is Side.LONG and s.verdict is Verdict.ENTER
    assert s.confidence == Decimal("0.72")
    assert s.created_at == T_CREATED
    assert [(e.source, e.kind) for e in s.evidence] == [("QuantAgent", "reasoning"), ("binance:BTCUSDT:1d", "source")]


def test_adapter_real_agent_response_object():
    from core.base_agent import AgentResponse, SignalDirection

    r = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.SHORT, confidence=61, reasoning="consensus")
    s = from_signal_dict(r.to_dict(), confidence_scale="percent", **_ctx())
    assert s.side is Side.SHORT and s.confidence == Decimal("0.61")


@pytest.mark.parametrize(
    "raw,side,verdict",
    [
        ("STRONG_BUY", Side.LONG, Verdict.ENTER),
        ("BUY", Side.LONG, Verdict.ENTER),
        ("SELL", Side.SHORT, Verdict.ENTER),
        ("STRONG_SELL", Side.SHORT, Verdict.ENTER),
        ("NEUTRAL", Side.FLAT, Verdict.HOLD),
        ("HOLD", Side.FLAT, Verdict.HOLD),
        ("AVOID", Side.FLAT, Verdict.AVOID),
    ],
)
def test_adapter_direction_mapping(raw, side, verdict):
    s = from_signal_dict(_agent_dict(signal=raw), confidence_scale="percent", **_ctx())
    assert (s.side, s.verdict) == (side, verdict)


def test_adapter_enum_direction():
    from core.base_agent import SignalDirection

    s = from_signal_dict(_agent_dict(signal=SignalDirection.AVOID), confidence_scale="percent", **_ctx())
    assert s.verdict is Verdict.AVOID


def test_adapter_fraction_scale_and_context_from_dict():
    d = _agent_dict(confidence=0.55, symbol="ETHUSDT", strategy_id="s", strategy_version="2", as_of="2026-10-28T00:00:00Z")
    s = from_signal_dict(d, confidence_scale="fraction", hypothesis_status="CONFIRMED", hypothesis_check="c")
    assert s.confidence == Decimal("0.55") and s.symbol == "ETHUSDT" and s.as_of == T_AS_OF


def test_adapter_context_from_metadata_and_levels():
    d = _agent_dict(
        metadata={"strategy_id": "m", "strategy_version": "9", "as_of": "2026-10-28T00:00:00Z", "stop_loss": 49_000.0},
        entry_price=50_000,
        take_profit="52000",
    )
    s = from_signal_dict(d, confidence_scale="percent", symbol="BTCUSDT", hypothesis_status="CONFIRMED",
                         hypothesis_check="c")
    assert s.strategy_id == "m" and s.stop_price == Decimal("49000.0") and s.target_price == Decimal("52000")


def test_adapter_percent_out_of_range_refused():
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(_agent_dict(confidence=150), confidence_scale="percent", **_ctx())
    assert "confidence" in ei.value.invalid


def test_adapter_wrong_scale_detected():
    # 72 interpreted as fraction → out of [0,1] → refused (no auto-guessing of scale)
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(_agent_dict(), confidence_scale="fraction", **_ctx())
    assert "confidence" in ei.value.invalid


def test_adapter_requires_explicit_scale():
    with pytest.raises(TypeError):
        from_signal_dict(_agent_dict(), **_ctx())  # type: ignore[call-arg]


def test_adapter_missing_context_listed():
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(_agent_dict(), confidence_scale="percent")
    assert set(ei.value.missing) == {"symbol", "strategy_id", "strategy_version", "as_of", "hypothesis_status"}


def test_adapter_missing_signal_and_confidence():
    d = _agent_dict()
    d.pop("signal")
    d.pop("confidence")
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(d, confidence_scale="percent", **_ctx())
    assert set(ei.value.missing) == {"signal", "confidence"}
    assert "side" not in ei.value.missing and "verdict" not in ei.value.missing


def test_adapter_unknown_direction_refused():
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(_agent_dict(signal="MOON"), confidence_scale="percent", **_ctx())
    assert "signal" in ei.value.invalid


def test_adapter_trading_signal_naive_timestamp_refused():
    """agents/_impl/types.TradingSignal uses naive datetime.now() → refused, not assumed UTC."""
    from dataclasses import asdict

    from agents._impl.types import TradingSignal

    ts = asdict(TradingSignal(signal="BUY", confidence=0.8, symbol="BTCUSDT"))
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(ts, confidence_scale="fraction", strategy_id="x", strategy_version="1", as_of=T_AS_OF,
                         hypothesis_status="CONFIRMED", hypothesis_check="c")
    assert "created_at" in ei.value.invalid
    assert "evidence" in ei.value.missing  # no reasoning/sources in TradingSignal


def test_adapter_explicit_created_at_overrides_timestamp():
    d = _agent_dict(timestamp="2026-10-28T00:05:00")  # naive
    s = from_signal_dict(d, confidence_scale="percent", created_at=T_CREATED, **_ctx())
    assert s.created_at == T_CREATED


def test_adapter_reasoning_without_agent_refused():
    d = _agent_dict(agent_name=None, sources=[])
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(d, confidence_scale="percent", **_ctx())
    assert "agent_name" in ei.value.invalid


def test_adapter_no_evidence_refused():
    d = _agent_dict(reasoning="", sources=[])
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(d, confidence_scale="percent", **_ctx())
    assert "evidence" in ei.value.missing


def test_adapter_non_mapping_refused():
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(["LONG"], confidence_scale="percent", **_ctx())  # type: ignore[arg-type]
    assert "signal_dict" in ei.value.invalid


def test_contract_not_wired_into_live_paths():
    """PR 2 scope guard: nothing outside trading/contracts imports the contract yet."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    hits = []
    for p in root.rglob("*.py"):
        rel = p.relative_to(root).as_posix()
        if rel.startswith(("trading/contracts/", "tests/", ".venv/")) or "/.venv/" in rel:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "trading.contracts" in txt:
            hits.append(rel)
    assert hits == []


# ── hypothesis status (schema 1.1) ───────────────────────────────────────────


@pytest.mark.parametrize(
    "side,verdict,status,check",
    [
        ("LONG", "ENTER", "CONFIRMED", "chk"),
        ("FLAT", "HOLD", "CONFIRMED", "chk"),
        ("FLAT", "HOLD", "REFUTED", "chk"),
        ("FLAT", "AVOID", "REFUTED", "chk"),
        ("FLAT", "HOLD", "INSUFFICIENT_DATA", None),
        ("FLAT", "AVOID", "INSUFFICIENT_DATA", None),
        ("FLAT", "AVOID", "INSUFFICIENT_DATA", "chk"),  # check name allowed but optional
    ],
)
def test_hypothesis_valid_combinations(side, verdict, status, check):
    s = build_signal(**_fields(side=side, verdict=verdict, hypothesis_status=status, hypothesis_check=check))
    assert s.hypothesis_status is HypothesisStatus(status) and s.hypothesis_check == check


@pytest.mark.parametrize("status", ["REFUTED", "INSUFFICIENT_DATA"])
@pytest.mark.parametrize("side", ["LONG", "SHORT"])
def test_enter_without_confirmed_refused(status, side):
    with pytest.raises(SignalRefused) as ei:
        build_signal(**_fields(side=side, verdict="ENTER", hypothesis_status=status))
    assert "ENTER requires CONFIRMED" in ei.value.invalid["hypothesis_status"]


@pytest.mark.parametrize("status", ["CONFIRMED", "REFUTED"])
def test_check_required_unless_insufficient(status):
    with pytest.raises(SignalRefused) as ei:
        build_signal(**_fields(side="FLAT", verdict="HOLD", hypothesis_status=status, hypothesis_check=None))
    assert ei.value.missing == ("hypothesis_check",)


def test_status_enum_and_lowercase_accepted():
    s = build_signal(**_fields(hypothesis_status=HypothesisStatus.CONFIRMED))
    assert build_signal(**_fields(hypothesis_status="confirmed")).hypothesis_status is s.hypothesis_status


def test_status_independent_of_confidence():
    """High confidence never upgrades status; low confidence never downgrades it."""
    with pytest.raises(SignalRefused):
        build_signal(**_fields(confidence="1", hypothesis_status="REFUTED"))
    s = build_signal(**_fields(confidence="0", hypothesis_status="CONFIRMED"))
    assert s.hypothesis_status is HypothesisStatus.CONFIRMED and s.confidence == 0


def test_signal_id_includes_hypothesis_fields():
    base = dict(side="FLAT", verdict="HOLD")
    a = build_signal(**_fields(**base, hypothesis_status="CONFIRMED"))
    b = build_signal(**_fields(**base, hypothesis_status="REFUTED"))
    c = build_signal(**_fields(**base, hypothesis_status="CONFIRMED", hypothesis_check="other-check"))
    d = build_signal(**_fields(**base, hypothesis_status="INSUFFICIENT_DATA", hypothesis_check=None))
    assert len({a.signal_id, b.signal_id, c.signal_id, d.signal_id}) == 4
    assert a.signal_id == build_signal(**_fields(**base, hypothesis_status="CONFIRMED")).signal_id


def test_to_dict_insufficient_data_check_none():
    d = build_signal(**_fields(side="FLAT", verdict="AVOID", hypothesis_status="INSUFFICIENT_DATA",
                               hypothesis_check=None)).to_dict()
    assert d["hypothesis_status"] == "INSUFFICIENT_DATA" and d["hypothesis_check"] is None


def test_adapter_requires_explicit_hypothesis_status():
    c = _ctx()
    c.pop("hypothesis_status")
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(_agent_dict(confidence=99), confidence_scale="percent", **c)
    assert "hypothesis_status" in ei.value.missing


def test_adapter_ignores_status_in_legacy_dict():
    """Status in the legacy dict/metadata is not trusted; caller must pass it."""
    c = _ctx()
    c.pop("hypothesis_status")
    d = _agent_dict(hypothesis_status="CONFIRMED", metadata={"hypothesis_status": "CONFIRMED"})
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(d, confidence_scale="percent", **c)
    assert "hypothesis_status" in ei.value.missing


def test_adapter_never_infers_status_from_confidence():
    for conf in (100, 0):
        with pytest.raises(SignalRefused) as ei:
            from_signal_dict(_agent_dict(confidence=conf), confidence_scale="percent",
                             **_ctx(hypothesis_status="REFUTED"))
        assert "hypothesis_status" in ei.value.invalid


@pytest.mark.parametrize("raw", ["NEUTRAL", "AVOID"])
def test_adapter_insufficient_data_hold_avoid(raw):
    s = from_signal_dict(_agent_dict(signal=raw), confidence_scale="percent",
                         **_ctx(hypothesis_status="INSUFFICIENT_DATA", hypothesis_check=None))
    assert s.hypothesis_status is HypothesisStatus.INSUFFICIENT_DATA and not s.is_actionable


def test_adapter_insufficient_data_enter_refused():
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(_agent_dict(signal="LONG"), confidence_scale="percent",
                         **_ctx(hypothesis_status="INSUFFICIENT_DATA", hypothesis_check=None))
    assert "hypothesis_status" in ei.value.invalid


def test_adapter_confirmed_needs_check_name():
    with pytest.raises(SignalRefused) as ei:
        from_signal_dict(_agent_dict(), confidence_scale="percent", **_ctx(hypothesis_check=None))
    assert "hypothesis_check" in ei.value.missing


def test_layers_documented_separately():
    import trading.contracts.signal as m

    doc = m.__doc__
    assert "Data validity" in doc and "Hypothesis status" in doc and "Execution permission" in doc
    assert "SafetyGate" in doc and "NEVER inferred from ``confidence``" in doc

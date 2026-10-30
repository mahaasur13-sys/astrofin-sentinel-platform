"""PR fix/trading-safety: SafetyGate before broker, fail-closed gate, live gate, qty in asset units.

No network: socket connect/DNS entry points are patched to raise in every test of this module.
(socket.socket construction itself stays intact: asyncio's event loop needs a local socketpair,
and aiohttp/typing use socket.socket as a type at import time.)
"""

from __future__ import annotations

import socket
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import orchestration.council_orchestrator  # noqa: F401  (import before network patch)
import trading.factory  # noqa: F401
from core.base_agent import AgentResponse, SignalDirection


class _NetworkBlocked(RuntimeError):
    pass


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def _blocked(*_a, **_kw):
        raise _NetworkBlocked("network access is forbidden in trading safety tests")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)
    yield


def _resp(name: str, direction: SignalDirection, confidence: int = 80) -> AgentResponse:
    return AgentResponse(agent_name=name, signal=direction, confidence=confidence, reasoning="test")


class _FakeRisk:
    def __init__(self, size: float = 0.1, reason: str = "ok"):
        self.size, self.reason = size, reason

    def adjust_position_size(self, base_size, agent_responses):
        return self.size, self.reason


def _mock_broker():
    broker = MagicMock()
    broker.name = "MockBroker"
    broker.place_order.return_value = SimpleNamespace(
        order_id="mock-1",
        status=SimpleNamespace(name="FILLED"),
        avg_fill_price=50_000.0,
        commission=0.0,
    )
    return broker


def test_socket_is_blocked():
    with pytest.raises(_NetworkBlocked):
        socket.create_connection(("api.binance.com", 443))
    with pytest.raises(_NetworkBlocked):
        socket.getaddrinfo("api.binance.com", 443)
    s = socket.socket()
    try:
        with pytest.raises(_NetworkBlocked):
            s.connect(("127.0.0.1", 9))
    finally:
        s.close()


# ── 1. SafetyGate refusal → place_order NOT called ─────────────────────────


@pytest.mark.asyncio
async def test_safety_gate_refusal_blocks_order(monkeypatch):
    import orchestration.council_orchestrator as orch_mod
    from trading.safety_gate import SafetyDecision, SafetyStatus

    broker = _mock_broker()
    monkeypatch.setattr(orch_mod, "get_broker", lambda *a, **k: broker)

    gate = MagicMock()
    gate.check.return_value = SafetyDecision(
        status=SafetyStatus.REJECTED,
        reason="RiskEngineV2: drawdown limit",
        blocked_reason="kill_switch:drawdown",
    )
    orch = orch_mod.CouncilOrchestrator(
        _FakeRisk(0.1),
        config={"symbol": "BTCUSDT", "equity": 10_000.0, "current_price": 50_000.0},
        safety_gate=gate,
    )
    final = _resp("AstroCouncil", SignalDirection.LONG)

    result = await orch.execute_trading_cycle([final], final)

    gate.check.assert_called_once()
    broker.place_order.assert_not_called()
    assert result["action"] == "DENIED"
    assert result["status"] == "REJECTED"
    assert result["blocked"] is True
    assert result["blocked_reason"] == "kill_switch:drawdown"
    assert "drawdown" in result["safety_reason"]


@pytest.mark.asyncio
async def test_safety_gate_approval_places_order_in_asset_units(monkeypatch):
    import orchestration.council_orchestrator as orch_mod
    from trading.safety_gate import SafetyDecision, SafetyStatus

    broker = _mock_broker()
    monkeypatch.setattr(orch_mod, "get_broker", lambda *a, **k: broker)
    gate = MagicMock()
    gate.check.return_value = SafetyDecision(status=SafetyStatus.APPROVED, reason="ok", reduced_position_pct=0.1)

    orch = orch_mod.CouncilOrchestrator(
        _FakeRisk(0.1),
        config={"symbol": "BTCUSDT", "equity": 10_000.0, "current_price": 50_000.0},
        safety_gate=gate,
    )
    final = _resp("AstroCouncil", SignalDirection.LONG)
    result = await orch.execute_trading_cycle([final], final)

    # qty = 10_000 * 0.1 / 50_000 = 0.02 BTC (not the 0.1 coefficient)
    broker.place_order.assert_called_once()
    assert broker.place_order.call_args.args[3] == pytest.approx(0.02)
    assert result["action"] == "EXECUTED"
    assert result["qty"] == pytest.approx(0.02)


# ── 2. Exception in kill switch check → DENY (fail-closed) ─────────────────


def test_kill_switch_exception_denies(monkeypatch):
    from trading import risk_v2
    from trading.safety_gate import SafetyGate

    def _boom(self):
        raise RuntimeError("kill switch backend down")

    monkeypatch.setattr(risk_v2.RiskEngineV2, "check_kill_switch", _boom)
    gate = SafetyGate(portfolio=SimpleNamespace(total_value=10_000.0, positions={}))

    decision = gate.check(
        {"signal": "LONG", "confidence": 90},
        {"trading_mode": "BACKTEST"},
        current_price=50_000.0,
        suggested_position_pct=0.1,
    )

    assert decision.is_blocked
    assert decision.is_denied
    assert decision.blocked_reason == "kill_switch_error"


def test_any_check_exception_denies(monkeypatch):
    from trading.safety_gate import SafetyGate

    gate = SafetyGate()

    def _boom(*_a, **_k):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(gate, "_normalize_signal", _boom)
    decision = gate.check({"signal": "LONG"}, {}, current_price=50_000.0)

    assert decision.is_blocked
    assert decision.blocked_reason == "safety_gate_error"


# ── 3. LIVE without flag → error at get_broker(), BinanceBroker not created ─


@pytest.mark.parametrize("mode_name", ["LIVE_LIMITED", "LIVE_FULL"])
@pytest.mark.parametrize("flag", [None, "", "yes", "i_understand", "I_UNDERSTAND "])
def test_live_mode_without_flag_raises(monkeypatch, mode_name, flag):
    from trading import factory
    from trading.mode import TradingMode

    if flag is None:
        monkeypatch.delenv("ASTROFIN_ALLOW_LIVE_TRADING", raising=False)
    else:
        monkeypatch.setenv("ASTROFIN_ALLOW_LIVE_TRADING", flag)

    sentinel = MagicMock(name="BinanceBroker")
    fake_mod = SimpleNamespace(BinanceBroker=sentinel)
    monkeypatch.setitem(sys.modules, "trading.broker.binance", fake_mod)

    with pytest.raises(factory.LiveTradingNotAllowedError, match="ASTROFIN_ALLOW_LIVE_TRADING"):
        factory.get_broker(TradingMode[mode_name])
    sentinel.assert_not_called()

    monkeypatch.setenv("TRADING_MODE", mode_name)
    with pytest.raises(factory.LiveTradingNotAllowedError):
        factory.get_broker()
    sentinel.assert_not_called()


def test_live_mode_with_exact_flag_creates_broker(monkeypatch):
    from trading import factory
    from trading.mode import TradingMode

    monkeypatch.setenv("ASTROFIN_ALLOW_LIVE_TRADING", "I_UNDERSTAND")
    instance = MagicMock()
    sentinel = MagicMock(name="BinanceBroker", return_value=instance)
    monkeypatch.setitem(sys.modules, "trading.broker.binance", SimpleNamespace(BinanceBroker=sentinel))

    assert factory.get_broker(TradingMode.LIVE_LIMITED) is instance
    sentinel.assert_called_once_with(paper=False)


def test_default_mode_is_paper(monkeypatch):
    from trading import factory
    from trading.mode import TradingMode

    monkeypatch.delenv("TRADING_MODE", raising=False)
    assert factory._resolve_mode() is TradingMode.PAPER


# ── 4. qty in asset units ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "equity,fraction,price,expected",
    [
        (10_000.0, 0.10, 50_000.0, 0.02),
        (25_000.0, 0.02, 2_500.0, 0.2),
        (1_000.0, 0.5, 0.25, 2000.0),
    ],
)
def test_compute_order_quantity(equity, fraction, price, expected):
    from orchestration.council_orchestrator import compute_order_quantity

    assert compute_order_quantity(equity, fraction, price) == pytest.approx(expected)


@pytest.mark.parametrize(
    "equity,fraction,price",
    [(0, 0.1, 50_000.0), (10_000.0, 0.1, 0), (10_000.0, -0.1, 1.0), (float("nan"), 0.1, 1.0), (10_000.0, 0.1, None)],
)
def test_compute_order_quantity_rejects_invalid(equity, fraction, price):
    from orchestration.council_orchestrator import compute_order_quantity

    with pytest.raises(ValueError):
        compute_order_quantity(equity, fraction, price)


# ── 5. Sanity via ExecutionSanityChecker.validate() ────────────────────────

_PORTFOLIO = SimpleNamespace(total_value=100_000.0, positions={})


def _market(**over):
    m = {
        "last_price": 50_000.0,
        "spread_bps": 2.0,
        "adv_24h_quote": 1_000_000_000.0,
        "current_vol_regime": "NORMAL",
    }
    m.update(over)
    return {k: v for k, v in m.items() if v is not None}


def _gate_check(market, pct=0.05, order_qty=None, portfolio=_PORTFOLIO):
    from trading.safety_gate import SafetyGate

    return SafetyGate(portfolio=portfolio).check(
        {"signal": "LONG", "confidence": 90},
        {"trading_mode": "BACKTEST", "market": market},
        current_price=0.0,
        symbol="BTCUSDT",
        suggested_position_pct=pct,
        order_qty=order_qty,
    )


def test_sanity_full_data_approved():
    d = _gate_check(_market())
    assert d.is_approved, d.reason


@pytest.mark.parametrize(
    "drop,expected",
    [
        ({"spread_bps": None}, "spread_bps"),
        ({"adv_24h_quote": None}, "adv_24h"),
        ({"current_vol_regime": None}, "current_vol_regime"),
        ({"last_price": None}, "last_price"),
        ({"spread_bps": None, "adv_24h_quote": None}, "spread_bps,adv_24h"),
    ],
)
def test_sanity_missing_data_blocked_with_fields(drop, expected):
    d = _gate_check(_market(**drop))
    assert d.is_blocked
    assert d.blocked_reason == f"sanity_missing_data:{expected}"


def test_sanity_missing_qty_blocked():
    # No portfolio: RiskEngineV2 is skipped (a portfolio without equity is now
    # BLOCKED no_equity before sanity); sanity cannot size the order → BLOCKED
    d = _gate_check(_market(), portfolio=None, pct=0.05)
    assert d.is_blocked
    assert d.blocked_reason.startswith("sanity_missing_data:") and "order_qty" in d.blocked_reason


def test_sanity_no_synthetic_spread_default():
    """bid/ask absent and spread absent → BLOCKED (never a default spread)."""
    d = _gate_check(_market(spread_bps=None))
    assert d.is_blocked and "spread_bps" in d.blocked_reason


def test_sanity_spread_from_real_bid_ask():
    d = _gate_check(_market(spread_bps=None, bid_price=49_995.0, ask_price=50_005.0))
    assert d.is_approved, d.reason


def test_sanity_base_volume_converted_to_quote():
    # 20_000 BTC * 50_000 = 1e9 USDT; order 5_000 USDT → 0.0005% participation → OK
    d = _gate_check(_market(adv_24h_quote=None, volume_24h_base=20_000.0))
    assert d.is_approved, d.reason
    # 1 BTC * 50_000 = 50_000 USDT ADV; order 5_000 USDT = 10% > 5% → SCALED
    d2 = _gate_check(_market(adv_24h_quote=None, volume_24h_base=1.0))
    assert d2.is_reduced
    assert d2.adjusted_qty == pytest.approx(50_000.0 * 0.05 / 50_000.0)


@pytest.mark.parametrize(
    "over,code",
    [
        ({"spread_bps": 150.0}, "sanity_failed:SPREAD_FILTER"),
        ({"current_vol_regime": "EXTREME"}, "sanity_failed:VOL_REGIME"),
        ({"slippage_bp_estimate": 80.0}, "sanity_failed:SLIPPAGE"),
    ],
)
def test_sanity_validate_rejected_is_rejected(over, code):
    d = _gate_check(_market(**over))
    assert d.is_rejected
    assert d.blocked_reason == code


def test_sanity_scaled_returns_adjusted_qty():
    # ADV 100_000 USDT, order 0.1 BTC * 50_000 = 5_000 USDT = 5% → exactly limit; use 0.2 BTC = 10%
    d = _gate_check(_market(adv_24h_quote=100_000.0), order_qty=0.2)
    assert d.is_reduced
    assert d.blocked_reason == "sanity_scaled"
    assert d.adjusted_qty == pytest.approx(100_000.0 * 0.05 / 50_000.0)


def test_sanity_exception_blocked(monkeypatch):
    from trading.execution import sanity

    def _boom(self, order, market):
        raise RuntimeError("validator crashed")

    monkeypatch.setattr(sanity.ExecutionSanityChecker, "validate", _boom)
    d = _gate_check(_market())
    assert d.is_blocked
    assert d.blocked_reason == "sanity_check_error"


# ── 6. Orchestrator never calls place_order on BLOCKED / REJECTED ──────────


def _orch(monkeypatch, gate=None, **cfg):
    import orchestration.council_orchestrator as orch_mod

    broker = _mock_broker()
    monkeypatch.setattr(orch_mod, "get_broker", lambda *a, **k: broker)
    base = {"symbol": "BTCUSDT", "equity": 100_000.0, "current_price": 50_000.0, "trading_mode": "BACKTEST"}
    base.update(cfg)
    from trading.safety_gate import SafetyGate

    orch = orch_mod.CouncilOrchestrator(
        _FakeRisk(0.05), config=base, safety_gate=gate or SafetyGate(portfolio=_PORTFOLIO)
    )
    return orch, broker


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "market,status,code_prefix",
    [
        (None, "BLOCKED", "sanity_missing_data:"),
        (_market(spread_bps=None), "BLOCKED", "sanity_missing_data:spread_bps"),
        (_market(spread_bps=500.0), "REJECTED", "sanity_failed:SPREAD_FILTER"),
        (_market(current_vol_regime="EXTREME"), "REJECTED", "sanity_failed:VOL_REGIME"),
    ],
)
async def test_orchestrator_no_order_on_blocked_or_rejected(monkeypatch, market, status, code_prefix):
    cfg = {"market": market} if market is not None else {}
    orch, broker = _orch(monkeypatch, **cfg)
    final = _resp("AstroCouncil", SignalDirection.LONG, confidence=90)

    result = await orch.execute_trading_cycle([final], final)

    broker.place_order.assert_not_called()
    assert result["action"] == "DENIED"
    assert result["status"] == status
    assert result["blocked_reason"].startswith(code_prefix)


@pytest.mark.asyncio
async def test_orchestrator_invalid_quantity_blocked(monkeypatch):
    orch, broker = _orch(monkeypatch, market=_market(), current_price=0.0)
    final = _resp("AstroCouncil", SignalDirection.LONG, confidence=90)
    result = await orch.execute_trading_cycle([final], final)
    broker.place_order.assert_not_called()
    assert result["status"] == "BLOCKED" and result["blocked_reason"] == "invalid_quantity"


@pytest.mark.asyncio
async def test_orchestrator_market_data_error_blocked(monkeypatch):
    import orchestration.council_orchestrator as orch_mod

    broker = _mock_broker()
    broker.get_market_price.side_effect = RuntimeError("feed down")
    monkeypatch.setattr(orch_mod, "get_broker", lambda *a, **k: broker)
    orch = orch_mod.CouncilOrchestrator(_FakeRisk(0.05), config={"equity": 100_000.0}, safety_gate=MagicMock())
    final = _resp("AstroCouncil", SignalDirection.LONG, confidence=90)
    result = await orch.execute_trading_cycle([final], final)
    broker.place_order.assert_not_called()
    assert result["status"] == "BLOCKED" and result["blocked_reason"] == "market_data_error"


@pytest.mark.asyncio
async def test_orchestrator_full_data_executes(monkeypatch):
    orch, broker = _orch(monkeypatch, market=_market())
    final = _resp("AstroCouncil", SignalDirection.LONG, confidence=90)
    result = await orch.execute_trading_cycle([final], final)
    # qty = 100_000 * 0.05 / 50_000 = 0.1 BTC
    broker.place_order.assert_called_once()
    assert broker.place_order.call_args.args[3] == pytest.approx(0.1)
    assert result["status"] == "APPROVED" and result["qty_scaled_from"] is None


@pytest.mark.asyncio
async def test_orchestrator_scaled_uses_adjusted_qty(monkeypatch):
    # ADV 100_000 USDT; order 0.1 BTC = 5_000 USDT = 5% → not above limit; use ADV 50_000 → 10%
    orch, broker = _orch(monkeypatch, market=_market(adv_24h_quote=50_000.0))
    final = _resp("AstroCouncil", SignalDirection.LONG, confidence=90)
    result = await orch.execute_trading_cycle([final], final)
    expected = 50_000.0 * 0.05 / 50_000.0  # 0.05 BTC
    broker.place_order.assert_called_once()
    assert broker.place_order.call_args.args[3] == pytest.approx(expected)
    assert result["status"] == "REDUCED"
    assert result["qty"] == pytest.approx(expected)
    assert result["qty_scaled_from"] == pytest.approx(0.1)


# ── 7. Slippage source: market | model ─────────────────────────────────────


def test_slippage_from_market():
    d = _gate_check(_market(slippage_bp_estimate=7.5))
    assert d.is_approved, d.reason
    assert d.slippage_source == "market" and d.slippage_bps == pytest.approx(7.5)


def test_slippage_from_model_when_absent():
    from trading.execution.slippage import SlippageModel

    d = _gate_check(_market(spread_bps=2.0))
    assert d.is_approved, d.reason
    assert d.slippage_source == "model"
    # SlippageModel: configured slippage_bps + real market spread_bps
    assert d.slippage_bps == pytest.approx(SlippageModel().slippage_bps + 2.0)


def test_slippage_model_high_estimate_rejects():
    """Model estimate above SanityConfig.max_slippage_bps (50) → REJECTED SLIPPAGE (spread 49 ≤ 100)."""
    d = _gate_check(_market(spread_bps=49.0))
    assert d.slippage_source == "model" and d.slippage_bps == pytest.approx(54.0)
    assert d.is_rejected and d.blocked_reason == "sanity_failed:SLIPPAGE"


@pytest.mark.parametrize("bad", [float("nan"), -1.0, None])
def test_slippage_model_unavailable_blocked(bad):
    from trading.safety_gate import SafetyGate

    class _BadModel:
        def calculate(self, side, qty, price):
            if bad is None:
                raise RuntimeError("model down")
            return SimpleNamespace(slippage_bps=bad)

    d = SafetyGate(portfolio=_PORTFOLIO, slippage_model=_BadModel()).check(
        {"signal": "LONG", "confidence": 90},
        {"trading_mode": "BACKTEST", "market": _market()},
        symbol="BTCUSDT",
        suggested_position_pct=0.05,
    )
    assert d.is_blocked
    assert d.blocked_reason == "sanity_missing_data:slippage"


def test_slippage_invalid_market_value_blocked():
    d = _gate_check(_market(slippage_bp_estimate=float("nan")))
    assert d.is_blocked and d.blocked_reason == "sanity_missing_data:slippage"


@pytest.mark.asyncio
async def test_orchestrator_reports_slippage_source(monkeypatch):
    orch, broker = _orch(monkeypatch, market=_market())
    final = _resp("AstroCouncil", SignalDirection.LONG, confidence=90)
    result = await orch.execute_trading_cycle([final], final)
    assert result["slippage_source"] == "model" and result["slippage_bps"] == pytest.approx(7.0)

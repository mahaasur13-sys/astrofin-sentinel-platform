"""Deterministic ledger-backed paper broker (trading/ledger/paper_broker.py). No network."""

from __future__ import annotations

import pathlib
import socket
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from trading.ledger import (
    ChainBroken,
    EventType,
    IdempotencyConflict,
    LedgerOrderEvent,
    OrderLedger,
    OrderSide,
    OrderStatus,
    create_ledger_schema,
)
from trading.ledger.paper_broker import (
    DeterministicPaperBroker,
    FeeSchedule,
    FixedBpsSlippage,
    MarketSnapshot,
    PaperOrder,
    deterministic_order_id,
)

UTC = timezone.utc
T0 = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


class _Clock:
    def __init__(self):
        self.t = T0

    def __call__(self):
        self.t += timedelta(milliseconds=1)
        return self.t


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(socket, "getaddrinfo", boom)
    monkeypatch.setattr(socket, "create_connection", boom)


def _env(**kw):
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    create_ledger_schema(eng)
    clock = _Clock()
    from trading.ledger.paper_broker import deterministic_order_id as oid_f

    led = OrderLedger(sessionmaker(bind=eng, autoflush=False, expire_on_commit=False), clock=clock,
                      order_id_factory=oid_f)
    return DeterministicPaperBroker(led, clock, **kw), led, eng


def _order(**over):
    base = dict(idempotency_key="sig-1:v1:BTCUSDT:BUY", signal_id="sig-1", strategy_version="v1",
                symbol="BTCUSDT", side=OrderSide.BUY, quantity=Decimal("0.5"))
    base.update(over)
    return PaperOrder(**base)


def _snap(**over):
    base = dict(symbol="BTCUSDT", price=Decimal("50000"), spread_bps=Decimal("2"), as_of=T0, snapshot_id="snap-1")
    base.update(over)
    return MarketSnapshot(**base)


def _dump(eng):
    with eng.connect() as c:
        ev = c.execute(select(LedgerOrderEvent.__table__).order_by("order_id", "seq")).all()
    return repr([tuple(r) for r in ev]).encode()


# ── basic fill / pricing ─────────────────────────────────────────────────────

def test_market_buy_full_fill_exact_numbers():
    br, led, _ = _env()
    r = br.submit(_order(), _snap())
    assert r.created and r.status is OrderStatus.FILLED
    (f,) = r.fills
    # half-spread 1bp + slippage 5bp = 6bp → 50000 * 1.0006
    assert f.price == Decimal("50030") and f.quantity == Decimal("0.5")
    assert f.fee == Decimal("25.015")  # 0.5 * 50030 * 10bp
    assert f.fee_asset == "USDT" and f.exchange_fill_id == f"paper:{r.order.order_id}:1"
    types = [e.event_type for e in led.events(r.order.order_id)]
    assert types == ["REQUEST", "EVIDENCE", "DECISION", "SUBMISSION", "RESULT"]
    assert led.verify_chain(r.order.order_id) == 5


def test_sell_price_moves_against_seller():
    br, _, _ = _env()
    r = br.submit(_order(side=OrderSide.SELL, idempotency_key="k-sell"), _snap())
    assert r.fills[0].price == Decimal("49970")


def test_decimal_precision_and_adverse_rounding():
    br, _, _ = _env(slippage=FixedBpsSlippage(Decimal("1.5")), fees=FeeSchedule(taker_bps=Decimal("7.5")))
    s = _snap(price=Decimal("0.123456789123"), spread_bps=Decimal("3"))
    buy = br.submit(_order(idempotency_key="b", quantity=Decimal("1234.56789")), s).fills[0]
    sell = br.submit(_order(idempotency_key="s", side=OrderSide.SELL, quantity=Decimal("1234.56789")), s).fills[0]
    # total 3bp: buy raw 0.1234938261597369 → ceil 1e-8; sell raw 0.1234197520862631 → floor 1e-8
    assert buy.price == Decimal("0.12349383")
    assert sell.price == Decimal("0.12341975")
    # fee = qty*px*7.5bp rounded up to 1e-8, exact Decimal (no float drift)
    assert buy.fee == Decimal("0.11434614")  # raw 0.11434613784… → ceil 1e-8
    assert isinstance(buy.fee, Decimal) and isinstance(buy.price, Decimal)


def test_quote_is_pure_and_float_free():
    br, _, _ = _env()
    q1 = br.quote(_order(), _snap())
    q2 = br.quote(_order(), _snap())
    assert q1 == q2 and all(isinstance(v, Decimal) for v in q1.values())


def test_min_fee_applies():
    br, _, _ = _env(fees=FeeSchedule(taker_bps=Decimal("0"), min_fee=Decimal("0.01")))
    assert br.submit(_order(), _snap()).fills[0].fee == Decimal("0.01")


# ── determinism ──────────────────────────────────────────────────────────────

def _scenario():
    br, led, eng = _env()
    br.submit(_order(), _snap())
    br.submit(_order(idempotency_key="k2", quantity=Decimal("3")), _snap(available_qty=Decimal("1.25")))
    br.submit(_order(idempotency_key="k3"), _snap(price=None))
    br.submit(_order(), _snap())  # resubmit
    with eng.connect() as c:
        fills = c.execute(select(led_fills_table()).order_by("exchange_fill_id")).all()
    return _dump(eng), repr([tuple(f) for f in fills]).encode()


def led_fills_table():
    from trading.ledger.models import LedgerFill

    return LedgerFill.__table__


def test_same_inputs_byte_identical_ledger():
    a_ev, a_f = _scenario()
    b_ev, b_f = _scenario()
    assert a_ev == b_ev and a_f == b_f
    assert len(a_ev) > 1000


def test_order_id_is_uuid5_of_key():
    br, _, _ = _env()
    r = br.submit(_order(), _snap())
    assert r.order.order_id == deterministic_order_id(_order().to_request())


def test_different_snapshot_changes_hashes():
    br1, _, e1 = _env()
    br2, _, e2 = _env()
    br1.submit(_order(), _snap())
    br2.submit(_order(), _snap(price=Decimal("50000.01")))
    assert _dump(e1) != _dump(e2)


# ── idempotency ──────────────────────────────────────────────────────────────

def test_resubmit_returns_same_order_no_double_fill():
    br, led, _ = _env()
    r1 = br.submit(_order(), _snap())
    n = len(led.events(r1.order.order_id))
    r2 = br.submit(_order(), _snap(price=Decimal("60000")))  # different market: must not refill
    assert not r2.created and r2.order.order_id == r1.order.order_id
    assert len(r2.fills) == 1 and r2.fills[0].price == Decimal("50030")
    assert len(led.events(r1.order.order_id)) == n


def test_resubmit_conflicting_payload_raises():
    br, _, _ = _env()
    br.submit(_order(), _snap())
    with pytest.raises(IdempotencyConflict):
        br.submit(_order(quantity=Decimal("0.6")), _snap())


def test_resubmit_blocked_stays_blocked():
    br, led, _ = _env()
    r1 = br.submit(_order(), None)
    r2 = br.submit(_order(), _snap())
    assert r1.status is r2.status is OrderStatus.BLOCKED and r2.fills == [] and not r2.created


# ── partial fills / liquidity / limit ────────────────────────────────────────

def test_partial_fill_by_available_liquidity():
    br, led, _ = _env()
    r = br.submit(_order(quantity=Decimal("3")), _snap(available_qty=Decimal("1.25")))
    assert r.status is OrderStatus.CANCELLED  # IOC remainder cancelled
    assert [f.quantity for f in r.fills] == [Decimal("1.25")]
    evs = led.events(r.order.order_id)
    assert [e.status_after for e in evs][-2:] == ["PARTIALLY_FILLED", "CANCELLED"]
    assert led.verify_chain(r.order.order_id) == len(evs)


def test_liquidity_exceeding_qty_fills_fully():
    br, _, _ = _env()
    r = br.submit(_order(), _snap(available_qty=Decimal("10")))
    assert r.status is OrderStatus.FILLED and r.fills[0].quantity == Decimal("0.5")


def test_zero_liquidity_cancels_without_fill():
    br, _, _ = _env()
    r = br.submit(_order(), _snap(available_qty=Decimal("0")))
    assert r.status is OrderStatus.CANCELLED and r.fills == []


def test_limit_not_marketable_cancelled():
    br, _, _ = _env()
    r = br.submit(_order(limit_price=Decimal("50029.99")), _snap())
    assert r.status is OrderStatus.CANCELLED and r.fills == []


def test_limit_marketable_fills_at_exec_price():
    br, _, _ = _env()
    r = br.submit(_order(limit_price=Decimal("50030")), _snap())
    assert r.status is OrderStatus.FILLED and r.fills[0].price == Decimal("50030")


# ── missing market data → BLOCKED, never invent prices ───────────────────────

@pytest.mark.parametrize("snap,why", [
    (None, "no snapshot"),
    (_snap(price=None), "market_data_missing: price"),
    (_snap(spread_bps=None), "spread_bps"),
    (_snap(as_of=None), "as_of"),
    (_snap(symbol="ETHUSDT"), "symbol"),
    (_snap(price=Decimal("0")), "market_data_invalid"),
    (_snap(price=Decimal("NaN")), "market_data_invalid"),
    (_snap(price=50000.0), "market_data_invalid"),
    (_snap(spread_bps=Decimal("-1")), "market_data_invalid"),
    (_snap(available_qty=Decimal("-1")), "market_data_invalid"),
    (_snap(as_of=datetime(2026, 10, 28, 12, 0)), "timezone-aware"),
])
def test_missing_or_invalid_market_data_blocked(snap, why):
    br, led, _ = _env()
    r = br.submit(_order(), snap)
    assert r.status is OrderStatus.BLOCKED and r.fills == []
    evs = led.events(r.order.order_id)
    assert [e.event_type for e in evs] == ["REQUEST", "REFUSAL"]
    assert evs[-1].decision == "BLOCKED" and why in evs[-1].reason
    assert led.verify_chain(r.order.order_id) == 2


def test_stale_snapshot_blocked():
    br, _, _ = _env(max_snapshot_age_s=Decimal("5"))
    r = br.submit(_order(), _snap(as_of=T0 - timedelta(seconds=60)))
    assert r.status is OrderStatus.BLOCKED


def test_module_has_no_price_source_imports():
    import trading.ledger.paper_broker as m

    src = pathlib.Path(m.__file__).read_text()
    for bad in ("data_provider", "fetch_current_price", "requests", "ccxt", "random", "time.time"):
        assert bad not in src


# ── chain verification / tamper ──────────────────────────────────────────────

def test_chain_verifies_and_detects_tamper():
    br, led, eng = _env()
    r = br.submit(_order(), _snap())
    oid = r.order.order_id
    assert led.verify_chain(oid) == 5
    with eng.begin() as c:
        c.execute(update(LedgerOrderEvent.__table__)
                  .where(LedgerOrderEvent.order_id == oid, LedgerOrderEvent.event_type == EventType.EVIDENCE.value)
                  .values(payload_json='{"snapshot":{"price":"1"}}'))
    with pytest.raises(ChainBroken):
        led.verify_chain(oid)


# ── config validation / isolation ────────────────────────────────────────────

@pytest.mark.parametrize("kw", [
    {"price_quantum": Decimal("0")},
    {"price_quantum": Decimal("1e-19")},
    {"fee_quantum": 0.01},
])
def test_bad_quantum_rejected(kw):
    with pytest.raises(ValueError):
        _env(**kw)


def test_bad_models_rejected():
    with pytest.raises(ValueError):
        FixedBpsSlippage(5.0)
    with pytest.raises(ValueError):
        FeeSchedule(taker_bps=Decimal("-1"))


def test_float_quantity_refused():
    br, _, _ = _env()
    with pytest.raises((TypeError, ValueError)):
        br.submit(_order(quantity=0.5), _snap())


def test_frozen_inputs():
    with pytest.raises(Exception):
        replace(_snap(), price=Decimal("1")).__setattr__("price", Decimal("2"))


def test_not_wired_into_factory_or_live():
    root = pathlib.Path(__file__).resolve().parents[2]
    offenders = []
    for p in root.rglob("*.py"):
        rel = p.relative_to(root).as_posix()
        if rel.startswith(("tests/", "trading/ledger/", ".venv/", "venv/")) or "/site-packages/" in rel:
            continue
        txt = p.read_text(errors="ignore")
        if "paper_broker import DeterministicPaperBroker" in txt or "ledger.paper_broker" in txt:
            offenders.append(rel)
    assert offenders == []
    import trading.factory as f

    assert "Deterministic" not in pathlib.Path(f.__file__).read_text()

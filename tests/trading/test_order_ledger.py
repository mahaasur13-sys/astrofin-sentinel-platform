"""Persistent order ledger (trading/ledger): idempotency, hash chain, Decimal, transitions.

SQLite only (in-memory StaticPool per repo convention, file DB for concurrency). No network.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, inspect, text, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from trading.ledger import (
    GENESIS_HASH,
    ChainBroken,
    Decision,
    EventType,
    FillRejected,
    IdempotencyConflict,
    InvalidTransition,
    LedgerOrderEvent,
    OrderLedger,
    OrderNotFound,
    OrderRequest,
    OrderSide,
    OrderStatus,
    create_ledger_schema,
)

UTC = timezone.utc
T0 = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


class _Clock:
    def __init__(self):
        self.t = T0

    def __call__(self):
        self.t += timedelta(milliseconds=1)
        return self.t


def _engine_memory():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    create_ledger_schema(eng)
    return eng


@pytest.fixture()
def ledger():
    eng = _engine_memory()
    yield OrderLedger(sessionmaker(bind=eng, autoflush=False, expire_on_commit=False), clock=_Clock())
    eng.dispose()


def _req(**over):
    base = dict(
        idempotency_key="sig-1:ema:1.0:BTCUSDT:BUY",
        signal_id="sig-1",
        strategy_version="ema_cross@1.0",
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type="market",
        quantity=Decimal("0.02"),
        price=None,
    )
    base.update(over)
    return OrderRequest(**base)


def _submitted(ledger, qty=Decimal("0.02"), **over):
    o, _ = ledger.create_order(_req(quantity=qty, **over))
    ledger.record_decision(o.order_id, Decision.APPROVED, "all checks passed")
    ledger.transition(o.order_id, OrderStatus.SUBMITTED, reason="paper submit")
    return o


# ── schema / isolation ──────────────────────────────────────────────────────


def test_schema_tables_and_not_in_app_metadata():
    eng = _engine_memory()
    names = set(inspect(eng).get_table_names())
    assert {"ledger_orders", "ledger_order_events", "ledger_fills"} <= names
    from db.models import Base

    assert not {"ledger_orders", "ledger_order_events", "ledger_fills"} & set(Base.metadata.tables)


def test_unique_constraints_present():
    eng = _engine_memory()
    insp = inspect(eng)
    uq_orders = {tuple(u["column_names"]) for u in insp.get_unique_constraints("ledger_orders")}
    uq_fills = {tuple(u["column_names"]) for u in insp.get_unique_constraints("ledger_fills")}
    uq_events = {tuple(u["column_names"]) for u in insp.get_unique_constraints("ledger_order_events")}
    assert ("idempotency_key",) in uq_orders
    assert ("exchange_fill_id",) in uq_fills
    assert ("order_id", "seq") in uq_events and ("order_id", "prev_hash") in uq_events


# ── idempotent create ───────────────────────────────────────────────────────


def test_create_order_records_request_event(ledger):
    o, created = ledger.create_order(_req(), evidence={"source": "QuantAgent", "reason": "EMA cross"})
    assert created and o.status == "PENDING"
    evs = ledger.events(o.order_id)
    assert [e.event_type for e in evs] == ["REQUEST", "EVIDENCE"]
    assert evs[0].prev_hash == GENESIS_HASH and evs[1].prev_hash == evs[0].event_hash
    assert ledger.verify_chain(o.order_id) == 2


def test_create_order_idempotent_same_payload(ledger):
    a, c1 = ledger.create_order(_req())
    for _ in range(10):
        b, c2 = ledger.create_order(_req())
        assert b.order_id == a.order_id and c2 is False
    assert len(ledger.events(a.order_id)) == 1  # repeats add no events


@pytest.mark.parametrize(
    "over",
    [
        {"quantity": Decimal("0.03")},
        {"side": OrderSide.SELL},
        {"symbol": "ETHUSDT"},
        {"signal_id": "sig-2"},
        {"strategy_version": "ema_cross@1.1"},
        {"price": Decimal("50000")},
    ],
)
def test_create_order_conflicting_payload_same_key(ledger, over):
    ledger.create_order(_req())
    with pytest.raises(IdempotencyConflict):
        ledger.create_order(_req(**over))


def test_equal_decimals_are_same_payload(ledger):
    a, _ = ledger.create_order(_req(quantity=Decimal("0.020")))
    b, created = ledger.create_order(_req(quantity=Decimal("0.02")))
    assert b.order_id == a.order_id and created is False


@pytest.mark.parametrize(
    "over,exc",
    [
        ({"quantity": 0.02}, TypeError),  # float refused
        ({"quantity": Decimal("0")}, ValueError),
        ({"quantity": Decimal("-1")}, ValueError),
        ({"quantity": Decimal("NaN")}, TypeError),
        ({"price": Decimal("-5")}, ValueError),
        ({"idempotency_key": " "}, ValueError),
        ({"signal_id": ""}, ValueError),
    ],
)
def test_create_order_invalid_input(ledger, over, exc):
    with pytest.raises(exc):
        ledger.create_order(_req(**over))


def test_concurrent_duplicate_insert_single_order(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'ledger.db'}", connect_args={"timeout": 30, "check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _wal(dbapi_conn, _rec):
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

    create_ledger_schema(eng)
    led = OrderLedger(sessionmaker(bind=eng, autoflush=False, expire_on_commit=False))
    results, errors = [], []
    barrier = threading.Barrier(8)

    def worker():
        try:
            barrier.wait()
            results.append(led.create_order(_req()))
        except Exception as e:  # pragma: no cover - surfaced below
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert errors == []
    assert len({o.order_id for o, _ in results}) == 1
    assert sum(1 for _, created in results if created) == 1
    with eng.connect() as c:
        assert c.execute(text("select count(*) from ledger_orders")).scalar() == 1
        assert c.execute(text("select count(*) from ledger_order_events")).scalar() == 1
    eng.dispose()


# ── decisions / transitions ─────────────────────────────────────────────────


def test_approved_and_reduced(ledger):
    o, _ = ledger.create_order(_req(quantity=Decimal("1.0")))
    r = ledger.record_decision(o.order_id, Decision.REDUCED, "sanity_scaled", approved_quantity=Decimal("0.4"))
    assert r.status == "APPROVED" and r.approved_quantity == Decimal("0.4")
    e = ledger.events(o.order_id)[-1]
    assert e.event_type == "DECISION" and e.decision == "REDUCED" and e.reason == "sanity_scaled"


@pytest.mark.parametrize("decision,status", [(Decision.REJECTED, "REJECTED"), (Decision.BLOCKED, "BLOCKED")])
def test_refusals_are_distinct_event_type(ledger, decision, status):
    o, _ = ledger.create_order(_req())
    r = ledger.record_decision(o.order_id, decision, "kill_switch:drawdown")
    assert r.status == status
    e = ledger.events(o.order_id)[-1]
    assert e.event_type == "REFUSAL" and e.decision == decision.value
    with pytest.raises(InvalidTransition):  # terminal
        ledger.transition(o.order_id, OrderStatus.SUBMITTED, reason="x")


def test_error_event_distinct_and_no_state_change(ledger):
    o, _ = ledger.create_order(_req())
    ledger.record_error(o.order_id, "market_data_error", {"exc": "TimeoutError"})
    e = ledger.events(o.order_id)[-1]
    assert e.event_type == "ERROR" and e.status_before == e.status_after == "PENDING"
    with pytest.raises(ValueError):
        ledger.record_error(o.order_id, "")


@pytest.mark.parametrize(
    "steps,bad",
    [
        ([], OrderStatus.SUBMITTED),  # PENDING -> SUBMITTED without decision
        ([], OrderStatus.CANCELLED),
        (["approve"], OrderStatus.REJECTED),  # APPROVED -> REJECTED (broker reject only after submit)
        (["approve", "submit", "cancel"], OrderStatus.SUBMITTED),  # from terminal
        (["approve"], OrderStatus.FILLED),  # fills only via record_fill
        (["approve"], OrderStatus.APPROVED),
        ([], OrderStatus.REJECTED),  # policy reject must use record_decision
    ],
)
def test_invalid_transitions_refused(ledger, steps, bad):
    o, _ = ledger.create_order(_req())
    for st in steps:
        if st == "approve":
            ledger.record_decision(o.order_id, Decision.APPROVED, "ok")
        elif st == "submit":
            ledger.transition(o.order_id, OrderStatus.SUBMITTED, reason="s")
        elif st == "cancel":
            ledger.transition(o.order_id, OrderStatus.CANCELLED, reason="c")
    n = len(ledger.events(o.order_id))
    with pytest.raises(InvalidTransition):
        ledger.transition(o.order_id, bad, reason="bad")
    assert len(ledger.events(o.order_id)) == n  # refused transition leaves no trace in chain


def test_double_decision_refused(ledger):
    o, _ = ledger.create_order(_req())
    ledger.record_decision(o.order_id, Decision.APPROVED, "ok")
    with pytest.raises(InvalidTransition):
        ledger.record_decision(o.order_id, Decision.BLOCKED, "late")


def test_reduced_requires_qty_and_not_above_request(ledger):
    o, _ = ledger.create_order(_req(quantity=Decimal("1")))
    with pytest.raises(ValueError):
        ledger.record_decision(o.order_id, Decision.REDUCED, "x")
    with pytest.raises(ValueError):
        ledger.record_decision(o.order_id, Decision.REDUCED, "x", approved_quantity=Decimal("2"))


def test_unknown_then_reconcile(ledger):
    o = _submitted(ledger)
    ledger.transition(o.order_id, OrderStatus.UNKNOWN, reason="crash before ack")
    ledger.transition(o.order_id, OrderStatus.CANCELLED, reason="reconciled: not on exchange")
    assert ledger.get_order(o.order_id).status == "CANCELLED"
    assert ledger.verify_chain(o.order_id) == 5


def test_unknown_order_id(ledger):
    with pytest.raises(OrderNotFound):
        ledger.record_decision("nope", Decision.APPROVED, "x")


# ── fills ───────────────────────────────────────────────────────────────────


def test_fills_partial_then_full(ledger):
    o = _submitted(ledger, qty=Decimal("0.03"))
    kw = dict(price=Decimal("50000.12345678"), fee=Decimal("0.0000015"), fee_asset="BTC", filled_at=T0)
    f1, c1 = ledger.record_fill(o.order_id, exchange_fill_id="ex-1", quantity=Decimal("0.01"), **kw)
    assert c1 and ledger.get_order(o.order_id).status == "PARTIALLY_FILLED"
    ledger.record_fill(o.order_id, exchange_fill_id="ex-2", quantity=Decimal("0.02"), **kw)
    assert ledger.get_order(o.order_id).status == "FILLED"
    assert sum(f.quantity for f in ledger.fills(o.order_id)) == Decimal("0.03")
    assert ledger.verify_chain(o.order_id) == 5


def test_duplicate_fill_ignored_idempotently(ledger):
    o = _submitted(ledger, qty=Decimal("0.05"))
    kw = dict(exchange_fill_id="ex-1", quantity=Decimal("0.01"), price=Decimal("50000"), fee=Decimal("0"), fee_asset="USDT", filled_at=T0)
    f1, c1 = ledger.record_fill(o.order_id, **kw)
    n = len(ledger.events(o.order_id))
    for _ in range(5):
        f2, c2 = ledger.record_fill(o.order_id, **kw)
        assert c2 is False and f2.fill_id == f1.fill_id
    assert len(ledger.fills(o.order_id)) == 1 and len(ledger.events(o.order_id)) == n


def test_duplicate_fill_id_conflicting_data(ledger):
    o = _submitted(ledger, qty=Decimal("0.05"))
    kw = dict(exchange_fill_id="ex-1", price=Decimal("50000"), fee=Decimal("0"), fee_asset="USDT", filled_at=T0)
    ledger.record_fill(o.order_id, quantity=Decimal("0.01"), **kw)
    with pytest.raises(IdempotencyConflict):
        ledger.record_fill(o.order_id, quantity=Decimal("0.02"), **kw)


def test_overfill_refused(ledger):
    o = _submitted(ledger, qty=Decimal("0.02"))
    with pytest.raises(FillRejected):
        ledger.record_fill(o.order_id, exchange_fill_id="ex-1", quantity=Decimal("0.021"), price=Decimal("1"), fee=Decimal("0"), fee_asset="USDT", filled_at=T0)
    assert ledger.fills(o.order_id) == []


def test_fill_respects_reduced_quantity(ledger):
    o, _ = ledger.create_order(_req(quantity=Decimal("1")))
    ledger.record_decision(o.order_id, Decision.REDUCED, "scaled", approved_quantity=Decimal("0.5"))
    ledger.transition(o.order_id, OrderStatus.SUBMITTED, reason="s")
    ledger.record_fill(o.order_id, exchange_fill_id="a", quantity=Decimal("0.5"), price=Decimal("1"), fee=Decimal("0"), fee_asset="USDT", filled_at=T0)
    assert ledger.get_order(o.order_id).status == "FILLED"


def test_fill_before_submission_refused(ledger):
    o, _ = ledger.create_order(_req())
    ledger.record_decision(o.order_id, Decision.APPROVED, "ok")
    with pytest.raises(InvalidTransition):
        ledger.record_fill(o.order_id, exchange_fill_id="a", quantity=Decimal("0.01"), price=Decimal("1"), fee=Decimal("0"), fee_asset="USDT", filled_at=T0)


def test_fill_naive_timestamp_refused(ledger):
    o = _submitted(ledger)
    with pytest.raises(Exception):
        ledger.record_fill(o.order_id, exchange_fill_id="a", quantity=Decimal("0.01"), price=Decimal("1"), fee=Decimal("0"), fee_asset="USDT", filled_at=datetime(2026, 10, 28))
    assert ledger.fills(o.order_id) == []


# ── Decimal precision / UTC ─────────────────────────────────────────────────


def test_decimal_precision_roundtrip_exact(ledger):
    q = Decimal("0.123456789012345678")  # 18 fractional digits
    p = Decimal("12345678901234567890.123456789012345678")  # 38 significant digits
    o, _ = ledger.create_order(_req(quantity=q, price=p, order_type="limit"))
    got = ledger.get_order(o.order_id)
    assert got.quantity == q and isinstance(got.quantity, Decimal)
    assert got.price == p
    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")
    sub = _submitted(ledger, qty=Decimal("0.3"), idempotency_key="k2")
    for i, qq in enumerate(("0.1", "0.2")):
        ledger.record_fill(sub.order_id, exchange_fill_id=f"f{i}", quantity=Decimal(qq), price=Decimal("1"), fee=Decimal("0.000000000000000001"), fee_asset="USDT", filled_at=T0)
    assert ledger.get_order(sub.order_id).status == "FILLED"  # 0.1 + 0.2 == 0.3 exactly
    assert sum(f.fee for f in ledger.fills(sub.order_id)) == Decimal("0.000000000000000002")


def test_decimal_too_many_fraction_digits_refused(ledger):
    with pytest.raises(Exception):
        ledger.create_order(_req(quantity=Decimal("0.1234567890123456789")))


def test_timestamps_are_utc_aware(ledger):
    o, _ = ledger.create_order(_req())
    got = ledger.get_order(o.order_id)
    assert got.created_at.tzinfo is not None and got.created_at.utcoffset() == timedelta(0)
    assert all(e.created_at.utcoffset() == timedelta(0) for e in ledger.events(o.order_id))


def test_float_in_payload_refused(ledger):
    o, _ = ledger.create_order(_req())
    with pytest.raises(TypeError):
        ledger.append_event(o.order_id, EventType.EVIDENCE, {"score": 0.7})


# ── hash chain tamper detection ─────────────────────────────────────────────


def _chain(ledger):
    o = _submitted(ledger, qty=Decimal("0.02"))
    ledger.record_fill(o.order_id, exchange_fill_id="ex-1", quantity=Decimal("0.02"), price=Decimal("50000"), fee=Decimal("1"), fee_asset="USDT", filled_at=T0)
    assert ledger.verify_chain(o.order_id) == 4
    return o


def _tamper(ledger, order_id, seq, **values):
    with ledger._sf() as s, s.begin():
        s.execute(update(LedgerOrderEvent).where(LedgerOrderEvent.order_id == order_id, LedgerOrderEvent.seq == seq).values(**values))


@pytest.mark.parametrize(
    "seq,values",
    [
        (2, {"reason": "approved by admin"}),
        (2, {"decision": "REDUCED"}),
        (1, {"payload_json": '{"request":{"quantity":"2"}}'}),
        (4, {"status_after": "CANCELLED"}),
        (3, {"event_type": "STATE"}),
        (2, {"created_at": T0 - timedelta(days=1)}),
    ],
)
def test_tamper_content_detected(ledger, seq, values):
    o = _chain(ledger)
    _tamper(ledger, o.order_id, seq, **values)
    with pytest.raises(ChainBroken) as ei:
        ledger.verify_chain(o.order_id)
    assert ei.value.seq == seq


def test_tamper_rehash_single_event_detected_downstream(ledger):
    """Attacker recomputes event 2's own hash; event 3's prev_hash no longer matches."""
    from trading.ledger import compute_event_hash

    o = _chain(ledger)
    e2 = ledger.events(o.order_id)[1]
    new_reason = "forged"
    h = compute_event_hash(
        prev_hash=e2.prev_hash, order_id=e2.order_id, seq=e2.seq, event_type=e2.event_type, decision=e2.decision,
        reason=new_reason, status_before=e2.status_before, status_after=e2.status_after,
        payload_json=e2.payload_json, created_at=e2.created_at,
    )
    _tamper(ledger, o.order_id, 2, reason=new_reason, event_hash=h)
    with pytest.raises(ChainBroken) as ei:
        ledger.verify_chain(o.order_id)
    assert ei.value.seq == 3 and "prev_hash" in ei.value.why


def test_deleted_event_detected(ledger):
    o = _chain(ledger)
    with ledger._sf() as s, s.begin():
        s.execute(text("DELETE FROM ledger_order_events WHERE order_id=:o AND seq=4"), {"o": o.order_id})
    with pytest.raises(ChainBroken):
        ledger.verify_chain(o.order_id)


def test_order_status_tamper_detected(ledger):
    o = _chain(ledger)
    with ledger._sf() as s, s.begin():
        s.execute(text("UPDATE ledger_orders SET status='CANCELLED' WHERE order_id=:o"), {"o": o.order_id})
    with pytest.raises(ChainBroken):
        ledger.verify_chain(o.order_id)


def test_fork_prevented_by_unique_prev_hash(ledger):
    o, _ = ledger.create_order(_req())
    e1 = ledger.events(o.order_id)[0]
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        with ledger._sf() as s, s.begin():
            s.add(LedgerOrderEvent(order_id=o.order_id, seq=2, event_type="EVIDENCE", payload_json="{}",
                                   created_at=T0, prev_hash=e1.event_hash, event_hash="a" * 64,
                                   status_before="PENDING", status_after="PENDING"))
            s.add(LedgerOrderEvent(order_id=o.order_id, seq=3, event_type="EVIDENCE", payload_json="{}",
                                   created_at=T0, prev_hash=e1.event_hash, event_hash="b" * 64,
                                   status_before="PENDING", status_after="PENDING"))


def test_ledger_not_wired_into_live_paths():
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    hits = []
    for p in root.rglob("*.py"):
        rel = p.relative_to(root).as_posix()
        if rel.startswith(("trading/ledger/", "tests/")) or "/.venv/" in rel or rel.startswith(".venv/"):
            continue
        if "trading.ledger" in p.read_text(encoding="utf-8", errors="ignore"):
            hits.append(rel)
    assert hits == []

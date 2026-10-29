"""Kill switch (fail-closed, scoped, audited) + startup recovery + broker gate. SQLite, no network."""

from __future__ import annotations

import socket
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect, select, text, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from trading.ledger import (
    Decision,
    EventType,
    KillScope,
    KillSwitch,
    KillSwitchAuditBroken,
    LedgerFill,
    LedgerKillSwitchAudit,
    LedgerOrderEvent,
    OrderLedger,
    OrderRequest,
    OrderSide,
    OrderStatus,
    create_ledger_schema,
    recover,
)
from trading.ledger.paper_broker import DeterministicPaperBroker, MarketSnapshot, PaperOrder, deterministic_order_id
from trading.ledger.recovery import PAPER_VENUE

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


class Env:
    def __init__(self):
        self.eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        create_ledger_schema(self.eng)
        self.clock = _Clock()
        self.sf = sessionmaker(bind=self.eng, autoflush=False, expire_on_commit=False)
        self.led = OrderLedger(self.sf, clock=self.clock, order_id_factory=deterministic_order_id)
        self.ks = KillSwitch(self.sf, self.clock)
        self.broker = DeterministicPaperBroker(self.led, self.clock, kill_switch=self.ks)

    def dump(self):
        with self.eng.connect() as c:
            out = []
            for t in ("ledger_orders", "ledger_order_events", "ledger_fills", "ledger_kill_switch",
                      "ledger_kill_switch_audit"):
                out.append((t, [tuple(r) for r in c.execute(text(f"SELECT * FROM {t} ORDER BY 1"))]))
            return out

    def count(self, table):
        with self.eng.connect() as c:
            return c.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()


@pytest.fixture()
def env():
    e = Env()
    yield e
    e.eng.dispose()


def _req(key, symbol="BTCUSDT", qty="1"):
    return OrderRequest(idempotency_key=key, signal_id="s", strategy_version="v1", symbol=symbol,
                        side=OrderSide.BUY, order_type="MARKET", quantity=Decimal(qty))


def _mk(env, key, upto, *, venue=PAPER_VENUE, symbol="BTCUSDT", fill=None):
    """Create an order and drive it to state ``upto`` via the public ledger API."""
    o, _ = env.led.create_order(_req(key, symbol))
    oid = o.order_id
    if upto == "PENDING":
        return oid
    env.led.record_decision(oid, Decision.APPROVED, "ok")
    if upto == "APPROVED":
        return oid
    env.led.transition(oid, OrderStatus.SUBMITTED, reason="sub", payload={"venue": venue})
    if fill:
        env.led.record_fill(oid, exchange_fill_id=f"f-{key}", quantity=Decimal(fill), price=Decimal("100"),
                            fee=Decimal("0"), fee_asset="USDT", filled_at=T0)
    if upto == "UNKNOWN":
        env.led.transition(oid, OrderStatus.UNKNOWN, reason="lost ack")
    return oid


def _snap(**over):
    base = dict(symbol="BTCUSDT", price=Decimal("50000"), spread_bps=Decimal("2"), as_of=T0, snapshot_id="s1")
    base.update(over)
    return MarketSnapshot(**base)


def _po(key="k", **over):
    base = dict(idempotency_key=key, signal_id="s", strategy_version="v1", symbol="BTCUSDT",
                side=OrderSide.BUY, quantity=Decimal("0.5"))
    base.update(over)
    return PaperOrder(**base)


# ── kill switch ──────────────────────────────────────────────────────────────

def test_schema_has_kill_switch_tables_not_in_app_metadata(env):
    names = set(inspect(env.eng).get_table_names())
    assert {"ledger_kill_switch", "ledger_kill_switch_audit"} <= names
    from db.models import Base

    assert not {"ledger_kill_switch", "ledger_kill_switch_audit"} & set(Base.metadata.tables)


def test_default_released(env):
    st = env.ks.check(symbol="BTCUSDT", strategy="v1")
    assert not st.engaged and st.error is None


def test_engage_release_roundtrip_and_audit(env):
    assert env.ks.engage(KillScope.GLOBAL, reason="manual stop", actor="felix") is True
    assert env.ks.engage(KillScope.GLOBAL, reason="again", actor="felix") is False  # no-op, not audited
    assert env.ks.is_engaged()
    assert env.ks.release(KillScope.GLOBAL, actor="felix", reason="checked") is True
    assert env.ks.release(KillScope.GLOBAL, actor="felix", reason="again") is False
    assert not env.ks.is_engaged()
    a = env.ks.audit()
    assert [(r.action, r.actor, r.reason, r.engaged_after) for r in a] == [
        ("ENGAGE", "felix", "manual stop", True), ("RELEASE", "felix", "checked", False)]
    assert all(r.at.tzinfo is not None for r in a)
    assert env.ks.verify_audit() == 2


def test_audit_tamper_detected(env):
    env.ks.engage(KillScope.SYMBOL, "BTCUSDT", reason="r", actor="a")
    env.ks.release(KillScope.SYMBOL, "BTCUSDT", actor="a", reason="ok")
    with env.eng.begin() as c:
        c.execute(update(LedgerKillSwitchAudit.__table__).where(LedgerKillSwitchAudit.seq == 1).values(actor="mallory"))
    with pytest.raises(KillSwitchAuditBroken):
        env.ks.verify_audit()


@pytest.mark.parametrize("actor,reason", [("", "r"), ("   ", "r"), (None, "r"), ("felix", ""), ("felix", None)])
def test_release_requires_actor_and_reason(env, actor, reason):
    env.ks.engage(KillScope.GLOBAL, reason="stop", actor="system")
    with pytest.raises(ValueError):
        env.ks.release(KillScope.GLOBAL, actor=actor, reason=reason)
    assert env.ks.is_engaged()


def test_release_signature_requires_keywords(env):
    with pytest.raises(TypeError):
        env.ks.release(KillScope.GLOBAL)  # type: ignore[call-arg]


def test_engage_requires_reason_and_scope_key(env):
    with pytest.raises(ValueError):
        env.ks.engage(KillScope.GLOBAL, reason="")
    with pytest.raises(ValueError):
        env.ks.engage(KillScope.SYMBOL, None, reason="x")
    with pytest.raises(ValueError):
        env.ks.engage("BOGUS", "x", reason="x")


def test_scope_precedence_and_isolation(env):
    env.ks.engage(KillScope.SYMBOL, "BTCUSDT", reason="sym", actor="a")
    assert env.ks.is_engaged(symbol="BTCUSDT")
    assert not env.ks.is_engaged(symbol="ETHUSDT")
    env.ks.engage(KillScope.STRATEGY, "v1", reason="strat", actor="a")
    env.ks.engage(KillScope.GLOBAL, reason="glob", actor="a")
    st = env.ks.check(symbol="BTCUSDT", strategy="v1")
    assert st.scopes == (("GLOBAL", "*"), ("STRATEGY", "v1"), ("SYMBOL", "BTCUSDT"))
    assert st.reason.startswith("GLOBAL")
    # releasing a narrower scope never releases a wider one
    env.ks.release(KillScope.SYMBOL, "BTCUSDT", actor="a", reason="fixed")
    assert env.ks.is_engaged(symbol="BTCUSDT")
    env.ks.release(KillScope.GLOBAL, actor="a", reason="fixed")
    assert env.ks.is_engaged(symbol="BTCUSDT", strategy="v1")  # strategy still engaged
    assert not env.ks.is_engaged(symbol="BTCUSDT", strategy="v2")


def test_fail_closed_on_session_error(env):
    def broken():
        raise OperationalError("SELECT", {}, Exception("db down"))

    ks = KillSwitch(broken, env.clock)
    st = ks.check(symbol="BTCUSDT")
    assert st.engaged and st.error and "kill_switch_unreadable" in st.reason
    assert ks.is_engaged()


def test_fail_closed_on_missing_table(env):
    with env.eng.begin() as c:
        c.execute(text("DROP TABLE ledger_kill_switch"))
    assert env.ks.is_engaged()


def test_fail_closed_on_corrupt_row(env):
    env.ks.engage(KillScope.GLOBAL, reason="r", actor="a")
    env.ks.release(KillScope.GLOBAL, actor="a", reason="ok")
    with env.eng.begin() as c:
        c.execute(text("UPDATE ledger_kill_switch SET engaged='garbage'"))
    # unreadable value for a released switch must not read as released
    assert env.ks.is_engaged(symbol="ETHUSDT")


# ── broker gate ──────────────────────────────────────────────────────────────

def test_broker_blocked_when_engaged(env):
    env.ks.engage(KillScope.SYMBOL, "BTCUSDT", reason="halt", actor="a")
    r = env.broker.submit(_po(), _snap())
    assert r.status is OrderStatus.BLOCKED and r.fills == []
    evs = env.led.events(r.order.order_id)
    assert [e.event_type for e in evs] == ["REQUEST", "REFUSAL"]
    assert evs[-1].decision == "BLOCKED" and evs[-1].reason.startswith("kill_switch_engaged: SYMBOL:BTCUSDT")
    assert env.count("ledger_fills") == 0
    # other symbol unaffected
    assert env.broker.submit(_po("k-eth", symbol="ETHUSDT"), _snap(symbol="ETHUSDT")).status is OrderStatus.FILLED


def test_broker_blocked_by_strategy_scope(env):
    env.ks.engage(KillScope.STRATEGY, "v1", reason="bad model", actor="a")
    assert env.broker.submit(_po(), _snap()).status is OrderStatus.BLOCKED
    assert env.broker.submit(_po("k2", strategy_version="v2"), _snap()).status is OrderStatus.FILLED


def test_broker_blocked_on_kill_switch_error(env):
    with env.eng.begin() as c:
        c.execute(text("DROP TABLE ledger_kill_switch"))
    r = env.broker.submit(_po(), _snap())
    assert r.status is OrderStatus.BLOCKED
    assert "kill_switch_unreadable" in env.led.events(r.order.order_id)[-1].reason


def test_broker_blocked_when_check_raises(env):
    class Boom:
        def check(self, **k):
            raise RuntimeError("x")

    br = DeterministicPaperBroker(env.led, env.clock, kill_switch=Boom())
    assert br.submit(_po(), _snap()).status is OrderStatus.BLOCKED


def test_broker_after_release_and_resubmit_stays_blocked(env):
    env.ks.engage(KillScope.GLOBAL, reason="halt", actor="a")
    r1 = env.broker.submit(_po(), _snap())
    env.ks.release(KillScope.GLOBAL, actor="felix", reason="ok")
    r2 = env.broker.submit(_po(), _snap())  # same key: idempotent, stays BLOCKED, no fill
    assert r2.order.order_id == r1.order.order_id and r2.status is OrderStatus.BLOCKED and not r2.created
    assert env.broker.submit(_po("k-new"), _snap()).status is OrderStatus.FILLED


def test_kill_switch_checked_before_market_data(env):
    env.ks.engage(KillScope.GLOBAL, reason="halt", actor="a")
    r = env.broker.submit(_po(), None)
    assert env.led.events(r.order.order_id)[-1].reason.startswith("kill_switch_engaged")


# ── recovery ─────────────────────────────────────────────────────────────────

def test_recovery_empty_ledger(env):
    rep = recover(env.led, env.ks)
    assert rep.scanned == 0 and rep.actions == [] and rep.clean


@pytest.mark.parametrize("state,expect_status,action", [
    ("PENDING", "BLOCKED", "BLOCKED"),
    ("APPROVED", "CANCELLED", "CANCELLED"),
    ("SUBMITTED", "CANCELLED", "CANCELLED"),
    ("UNKNOWN", "CANCELLED", "CANCELLED"),
])
def test_recovery_paper_states(env, state, expect_status, action):
    oid = _mk(env, "k", state)
    rep = recover(env.led, env.ks)
    assert [(a.order_id, a.status_before, a.action, a.status_after) for a in rep.actions] == [
        (oid, state, action, expect_status)]
    assert env.led.get_order(oid).status == expect_status
    last = env.led.events(oid)[-1]
    assert last.reason.startswith("recovery:") and '"recovery":true' in last.payload_json
    assert env.led.verify_chain(oid) == len(env.led.events(oid))
    assert not env.ks.is_engaged(symbol="BTCUSDT") and rep.clean


def test_recovery_partially_filled_paper_cancels_remainder(env):
    oid = _mk(env, "k", "SUBMITTED", fill="0.4")
    assert env.led.get_order(oid).status == "PARTIALLY_FILLED"
    rep = recover(env.led, env.ks)
    assert rep.actions[0].action == "CANCELLED" and "0.4/1" in rep.actions[0].detail
    assert env.led.get_order(oid).status == "CANCELLED"
    assert [f.quantity for f in env.led.fills(oid)] == [Decimal("0.4")]


def test_recovery_unknown_venue_marks_unknown_and_engages_symbol(env):
    oid = _mk(env, "k", "SUBMITTED", venue="binance")
    rep = recover(env.led, env.ks)
    assert [a.action for a in rep.actions] == ["MARKED_UNKNOWN", "KILL_SWITCH"]
    assert env.led.get_order(oid).status == "UNKNOWN"
    st = env.ks.check(symbol="BTCUSDT")
    assert st.engaged and st.scopes == (("SYMBOL", "BTCUSDT"),) and oid in st.reason
    assert not env.ks.is_engaged(symbol="ETHUSDT")
    assert rep.kill_switch_engaged and not rep.clean


def test_recovery_partially_filled_other_venue_unknown(env):
    oid = _mk(env, "k", "SUBMITTED", venue="binance", fill="0.3")
    rep = recover(env.led, env.ks)
    assert rep.actions[0].action == "MARKED_UNKNOWN" and env.led.get_order(oid).status == "UNKNOWN"


def test_recovery_unknown_other_venue_kept(env):
    oid = _mk(env, "k", "UNKNOWN", venue="binance")
    n = len(env.led.events(oid))
    rep = recover(env.led, env.ks)
    assert [a.action for a in rep.actions] == ["KEPT_UNKNOWN", "KILL_SWITCH"]
    assert len(env.led.events(oid)) == n


def test_recovery_broken_chain_engages_global_and_leaves_order(env):
    good = _mk(env, "good", "APPROVED")
    bad = _mk(env, "bad", "SUBMITTED")
    with env.eng.begin() as c:
        c.execute(update(LedgerOrderEvent.__table__)
                  .where(LedgerOrderEvent.order_id == bad, LedgerOrderEvent.seq == 1)
                  .values(payload_json='{"forged":true}'))
    before = env.led.get_order(bad).status
    rep = recover(env.led, env.ks)
    assert rep.broken_chains == [bad]
    acts = {(a.order_id, a.action) for a in rep.actions}
    assert (bad, "CHAIN_BROKEN") in acts and (bad, "KILL_SWITCH") in acts and (good, "CANCELLED") in acts
    assert env.led.get_order(bad).status == before
    st = env.ks.check(symbol="ETHUSDT")
    assert st.engaged and st.scopes == (("GLOBAL", "*"),)
    assert env.broker.submit(_po("after"), _snap()).status is OrderStatus.BLOCKED


def test_recovery_never_submits_or_fills(env):
    for i, st in enumerate(["PENDING", "APPROVED", "SUBMITTED", "UNKNOWN"]):
        _mk(env, f"k{i}", st)
    _mk(env, "kb", "SUBMITTED", venue="binance")
    _mk(env, "kp", "SUBMITTED", fill="0.5")
    with env.eng.connect() as c:
        subs = c.execute(select(LedgerOrderEvent.__table__)
                         .where(LedgerOrderEvent.event_type == EventType.SUBMISSION.value)).all()
    fills = env.count("ledger_fills")
    recover(env.led, env.ks)
    with env.eng.connect() as c:
        subs2 = c.execute(select(LedgerOrderEvent.__table__)
                          .where(LedgerOrderEvent.event_type == EventType.SUBMISSION.value)).all()
    assert subs2 == subs and env.count("ledger_fills") == fills
    assert env.led.open_orders()[0].status == "UNKNOWN" and len(env.led.open_orders()) == 1


def test_recovery_idempotent(env):
    for i, st in enumerate(["PENDING", "APPROVED", "SUBMITTED", "UNKNOWN"]):
        _mk(env, f"k{i}", st)
    _mk(env, "kb", "SUBMITTED", venue="binance", symbol="ETHUSDT")
    _mk(env, "ku", "UNKNOWN", venue="binance", symbol="SOLUSDT")
    _mk(env, "kp", "SUBMITTED", fill="0.5")
    rep1 = recover(env.led, env.ks)
    snap1 = env.dump()
    rep2 = recover(env.led, env.ks)
    assert env.dump() == snap1  # no duplicate events / audit / state change
    assert rep2.kill_switch_engaged == [] and len(rep1.kill_switch_engaged) == 2
    assert {a.action for a in rep2.actions} <= {"KEPT_UNKNOWN", "KILL_SWITCH"}
    assert {a.order_id for a in rep2.actions} == {a.order_id for a in rep1.actions if a.status_after == "UNKNOWN"}
    rep3 = recover(env.led, env.ks)
    assert rep3.actions == rep2.actions and env.dump() == snap1


def test_recovery_idempotent_with_broken_chain(env):
    bad = _mk(env, "bad", "SUBMITTED")
    with env.eng.begin() as c:
        c.execute(update(LedgerOrderEvent.__table__)
                  .where(LedgerOrderEvent.order_id == bad, LedgerOrderEvent.seq == 2).values(reason="forged"))
    recover(env.led, env.ks)
    a = env.count("ledger_kill_switch_audit")
    snap = env.dump()
    rep2 = recover(env.led, env.ks)
    assert env.count("ledger_kill_switch_audit") == a == 1 and env.dump() == snap
    assert rep2.broken_chains == [bad] and rep2.kill_switch_engaged == []


def test_recovery_deterministic_order(env):
    ids = [_mk(env, f"k{i}", "APPROVED") for i in range(5)]
    rep = recover(env.led, env.ks)
    assert [a.order_id for a in rep.actions] == ids


def test_recovery_after_paper_broker_crash_mid_submit(env, monkeypatch):
    """Simulate crash between SUBMISSION and fill: recovery cancels, no fill invented."""
    from trading.ledger import repository

    def crash(self, *a, **k):
        raise RuntimeError("process died")

    monkeypatch.setattr(repository.OrderLedger, "record_fill", crash)
    with pytest.raises(RuntimeError):
        env.broker.submit(_po(), _snap())
    monkeypatch.undo()
    oid = deterministic_order_id(_po().to_request())
    assert env.led.get_order(oid).status == "SUBMITTED"
    rep = recover(env.led, env.ks)
    assert rep.actions[0].action == "CANCELLED" and env.led.fills(oid) == []
    # resubmitting the same key after recovery does not fill
    assert env.broker.submit(_po(), _snap()).status is OrderStatus.CANCELLED
    assert env.count("ledger_fills") == 0


def test_not_wired():
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    bad = []
    for p in root.rglob("*.py"):
        rel = p.relative_to(root).as_posix()
        if rel.startswith(("tests/", "trading/ledger/", ".venv/", "venv/")) or "/site-packages/" in rel:
            continue
        t = p.read_text(errors="ignore")
        if "ledger.killswitch" in t or "ledger.recovery" in t or "KillSwitch(" in t:
            bad.append(rel)
    assert bad == []


def test_fill_model_unchanged():
    assert LedgerFill.__tablename__ == "ledger_fills"

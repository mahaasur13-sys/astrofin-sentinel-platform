"""trading/ledger/models.py — persistent order ledger schema.

Uses its OWN declarative base (``LedgerBase``), deliberately NOT ``db.models.Base``:
the running app calls ``Base.metadata.create_all`` on start (db/init.py), and this PR
must not create tables in any live database. Create the schema explicitly with
``create_ledger_schema(engine)``.
"""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

from .types import ExactDecimal, UTCDateTime

LedgerBase = declarative_base()


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"  # request recorded, no decision yet
    APPROVED = "APPROVED"  # risk/safety approved (possibly REDUCED qty)
    REJECTED = "REJECTED"  # policy refusal (terminal)
    BLOCKED = "BLOCKED"  # check could not be performed (terminal)
    SUBMITTED = "SUBMITTED"  # sent to broker
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"  # terminal
    CANCELLED = "CANCELLED"  # terminal
    UNKNOWN = "UNKNOWN"  # outcome not determined (e.g. after crash) → must be reconciled


class EventType(str, enum.Enum):
    REQUEST = "REQUEST"
    EVIDENCE = "EVIDENCE"
    DECISION = "DECISION"  # APPROVED / REDUCED
    REFUSAL = "REFUSAL"  # REJECTED / BLOCKED
    SUBMISSION = "SUBMISSION"
    RESULT = "RESULT"  # fills / final broker outcome
    ERROR = "ERROR"  # technical error (distinct from REFUSAL)
    STATE = "STATE"  # other explicit state transition (cancel, unknown, reconcile)


class Decision(str, enum.Enum):
    APPROVED = "APPROVED"
    REDUCED = "REDUCED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


TERMINAL_STATUSES = frozenset({OrderStatus.REJECTED, OrderStatus.BLOCKED, OrderStatus.FILLED, OrderStatus.CANCELLED})

ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PENDING: frozenset({OrderStatus.APPROVED, OrderStatus.REJECTED, OrderStatus.BLOCKED}),
    OrderStatus.APPROVED: frozenset({OrderStatus.SUBMITTED, OrderStatus.CANCELLED, OrderStatus.UNKNOWN}),
    OrderStatus.SUBMITTED: frozenset(
        {
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.UNKNOWN,
        }
    ),
    OrderStatus.PARTIALLY_FILLED: frozenset(
        {OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.UNKNOWN}
    ),
    OrderStatus.UNKNOWN: frozenset(
        {
            OrderStatus.SUBMITTED,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        }
    ),
    **{s: frozenset() for s in TERMINAL_STATUSES},
}

_STATUS_VALUES = ",".join(f"'{s.value}'" for s in OrderStatus)
_EVENT_VALUES = ",".join(f"'{e.value}'" for e in EventType)
_DECISION_VALUES = ",".join(f"'{d.value}'" for d in Decision)


class LedgerOrder(LedgerBase):
    __tablename__ = "ledger_orders"

    order_id = Column(String(36), primary_key=True)
    idempotency_key = Column(String(128), nullable=False, unique=True)
    payload_hash = Column(String(64), nullable=False)  # sha256 of the identity payload
    signal_id = Column(String(128), nullable=False)
    strategy_version = Column(String(64), nullable=False)
    symbol = Column(String(32), nullable=False)
    side = Column(String(4), nullable=False)
    order_type = Column(String(16), nullable=False)
    quantity = Column(ExactDecimal(), nullable=False)
    price = Column(ExactDecimal(), nullable=True)  # NULL for market orders
    approved_quantity = Column(ExactDecimal(), nullable=True)  # set by DECISION (REDUCED may lower it)
    status = Column(String(20), nullable=False)
    last_event_seq = Column(Integer, nullable=False, default=0)
    created_at = Column(UTCDateTime(), nullable=False)
    updated_at = Column(UTCDateTime(), nullable=False)

    __table_args__ = (
        CheckConstraint(f"status IN ({_STATUS_VALUES})", name="ck_ledger_orders_status"),
        CheckConstraint("side IN ('BUY','SELL')", name="ck_ledger_orders_side"),
        Index("ix_ledger_orders_signal", "signal_id"),
        Index("ix_ledger_orders_status", "status"),
    )


class LedgerOrderEvent(LedgerBase):
    """Append-only evidence chain. ``event_hash`` = sha256(prev_hash || canonical event)."""

    __tablename__ = "ledger_order_events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), ForeignKey("ledger_orders.order_id"), nullable=False)
    seq = Column(Integer, nullable=False)  # 1..n per order
    event_type = Column(String(16), nullable=False)
    decision = Column(String(16), nullable=True)
    reason = Column(Text, nullable=True)
    status_before = Column(String(20), nullable=True)
    status_after = Column(String(20), nullable=True)
    payload_json = Column(Text, nullable=False)  # canonical JSON (sorted keys, Decimal as str)
    created_at = Column(UTCDateTime(), nullable=False)
    prev_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False, unique=True)

    __table_args__ = (
        UniqueConstraint("order_id", "seq", name="uq_ledger_events_order_seq"),
        UniqueConstraint("order_id", "prev_hash", name="uq_ledger_events_order_prev"),  # no forks
        CheckConstraint(f"event_type IN ({_EVENT_VALUES})", name="ck_ledger_events_type"),
        CheckConstraint(f"decision IS NULL OR decision IN ({_DECISION_VALUES})", name="ck_ledger_events_decision"),
    )


class LedgerFill(LedgerBase):
    __tablename__ = "ledger_fills"

    fill_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), ForeignKey("ledger_orders.order_id"), nullable=False)
    exchange_fill_id = Column(String(128), nullable=False, unique=True)
    quantity = Column(ExactDecimal(), nullable=False)
    price = Column(ExactDecimal(), nullable=False)
    fee = Column(ExactDecimal(), nullable=False)
    fee_asset = Column(String(16), nullable=False)
    filled_at = Column(UTCDateTime(), nullable=False)
    recorded_at = Column(UTCDateTime(), nullable=False)

    __table_args__ = (Index("ix_ledger_fills_order", "order_id"),)


class KillScope(str, enum.Enum):
    GLOBAL = "GLOBAL"
    SYMBOL = "SYMBOL"
    STRATEGY = "STRATEGY"


GLOBAL_KEY = "*"


class LedgerKillSwitch(LedgerBase):
    """Current kill-switch state, one row per (scope, scope_key). Changes only via KillSwitch."""

    __tablename__ = "ledger_kill_switch"

    switch_id = Column(Integer, primary_key=True, autoincrement=True)
    scope = Column(String(16), nullable=False)
    scope_key = Column(String(128), nullable=False)
    engaged = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=False)
    actor = Column(String(128), nullable=False)
    engaged_at = Column(UTCDateTime(), nullable=True)
    updated_at = Column(UTCDateTime(), nullable=False)

    __table_args__ = (
        UniqueConstraint("scope", "scope_key", name="uq_ledger_kill_switch_scope"),
        CheckConstraint("scope IN ('GLOBAL','SYMBOL','STRATEGY')", name="ck_ledger_kill_switch_scope"),
    )


class LedgerKillSwitchAudit(LedgerBase):
    """Append-only, hash-chained audit of every kill-switch change."""

    __tablename__ = "ledger_kill_switch_audit"

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    seq = Column(Integer, nullable=False, unique=True)
    scope = Column(String(16), nullable=False)
    scope_key = Column(String(128), nullable=False)
    action = Column(String(8), nullable=False)
    engaged_after = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=False)
    actor = Column(String(128), nullable=False)
    at = Column(UTCDateTime(), nullable=False)
    prev_hash = Column(String(64), nullable=False, unique=True)
    entry_hash = Column(String(64), nullable=False, unique=True)

    __table_args__ = (CheckConstraint("action IN ('ENGAGE','RELEASE')", name="ck_ledger_kill_audit_action"),)


def create_ledger_schema(engine) -> None:
    """Explicitly create ledger tables (checkfirst). Never called by the app on its own."""
    LedgerBase.metadata.create_all(engine)

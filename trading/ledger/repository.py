"""trading/ledger/repository.py — order ledger repository (idempotent, append-only, hash-chained).

Not wired into the orchestrator or any live path. Callers inject a SQLAlchemy
``sessionmaker``; every public method runs in its own transaction.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .types import decimal_to_str
from .models import (
    ALLOWED_TRANSITIONS,
    Decision,
    EventType,
    LedgerFill,
    LedgerOrder,
    LedgerOrderEvent,
    OrderSide,
    OrderStatus,
)

GENESIS_HASH = "0" * 64


class LedgerError(Exception):
    """Base class for ledger refusals."""


class IdempotencyConflict(LedgerError):
    """Same idempotency_key (or exchange_fill_id) with a different payload."""


class InvalidTransition(LedgerError):
    pass


class OrderNotFound(LedgerError):
    pass


class ConcurrentAppend(LedgerError):
    """Another writer appended to the same order chain concurrently; caller must retry."""


class ChainBroken(LedgerError):
    def __init__(self, order_id: str, seq: int, why: str):
        self.order_id, self.seq, self.why = order_id, seq, why
        super().__init__(f"evidence chain broken for order {order_id} at seq {seq}: {why}")


class FillRejected(LedgerError):
    pass


# ── canonical serialisation / hashing ────────────────────────────────────────


def _canon(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return decimal_to_str(obj)
    if isinstance(obj, datetime):
        return obj.astimezone(timezone.utc).isoformat()
    if isinstance(obj, (OrderStatus, EventType, Decision, OrderSide)):
        return obj.value
    if isinstance(obj, Mapping):
        return {str(k): _canon(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_canon(v) for v in obj]
    if isinstance(obj, float):
        raise TypeError("float not allowed in ledger payloads; use Decimal")
    return obj


def canonical_json(obj: Any) -> str:
    return json.dumps(_canon(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def compute_event_hash(
    *,
    prev_hash: str,
    order_id: str,
    seq: int,
    event_type: str,
    decision: str | None,
    reason: str | None,
    status_before: str | None,
    status_after: str | None,
    payload_json: str,
    created_at: datetime,
) -> str:
    body = canonical_json(
        {
            "order_id": order_id,
            "seq": seq,
            "event_type": event_type,
            "decision": decision,
            "reason": reason,
            "status_before": status_before,
            "status_after": status_after,
            "payload": payload_json,
            "created_at": created_at,
        }
    )
    return _sha256(prev_hash + "|" + body)


def _require_decimal(name: str, v: Any, *, positive: bool = True, allow_zero: bool = False) -> Decimal:
    if not isinstance(v, Decimal) or not v.is_finite():
        raise TypeError(f"{name} must be a finite Decimal, got {type(v).__name__}")
    if positive and (v < 0 or (v == 0 and not allow_zero)):
        raise ValueError(f"{name} must be {'>= 0' if allow_zero else '> 0'}")
    return v


@dataclass(frozen=True)
class OrderRequest:
    idempotency_key: str
    signal_id: str
    strategy_version: str
    symbol: str
    side: OrderSide
    order_type: str
    quantity: Decimal
    price: Decimal | None = None

    def identity_payload(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "strategy_version": self.strategy_version,
            "symbol": self.symbol,
            "side": OrderSide(self.side),
            "order_type": self.order_type.upper(),
            "quantity": self.quantity,
            "price": self.price,
        }


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrderLedger:
    def __init__(self, session_factory: Callable[[], Session], clock: Callable[[], datetime] = _utcnow):
        self._sf = session_factory
        self._clock = clock

    # ── helpers ──────────────────────────────────────────────────────────────

    def _now(self) -> datetime:
        t = self._clock()
        if t.tzinfo is None:
            raise ValueError("clock must return timezone-aware datetimes")
        return t.astimezone(timezone.utc)

    @staticmethod
    def _lock_order(s: Session, order_id: str) -> LedgerOrder:
        o = s.execute(select(LedgerOrder).where(LedgerOrder.order_id == order_id).with_for_update()).scalar_one_or_none()
        if o is None:
            raise OrderNotFound(order_id)
        return o

    def _append(
        self,
        s: Session,
        order: LedgerOrder,
        event_type: EventType,
        payload: Mapping[str, Any] | None,
        *,
        decision: Decision | None = None,
        reason: str | None = None,
        status_after: OrderStatus | None = None,
    ) -> LedgerOrderEvent:
        prev = s.execute(
            select(LedgerOrderEvent)
            .where(LedgerOrderEvent.order_id == order.order_id)
            .order_by(LedgerOrderEvent.seq.desc())
            .limit(1)
        ).scalar_one_or_none()
        prev_hash = prev.event_hash if prev else GENESIS_HASH
        seq = (prev.seq if prev else 0) + 1
        if seq != order.last_event_seq + 1:
            raise ConcurrentAppend(f"order {order.order_id}: expected seq {order.last_event_seq + 1}, chain at {seq}")
        now = self._now()
        status_before = order.status
        pj = canonical_json(payload or {})
        ev = LedgerOrderEvent(
            order_id=order.order_id,
            seq=seq,
            event_type=event_type.value,
            decision=decision.value if decision else None,
            reason=reason,
            status_before=status_before,
            status_after=(status_after.value if status_after else status_before),
            payload_json=pj,
            created_at=now,
            prev_hash=prev_hash,
        )
        ev.event_hash = compute_event_hash(
            prev_hash=prev_hash,
            order_id=order.order_id,
            seq=seq,
            event_type=ev.event_type,
            decision=ev.decision,
            reason=reason,
            status_before=ev.status_before,
            status_after=ev.status_after,
            payload_json=pj,
            created_at=now,
        )
        s.add(ev)
        order.last_event_seq = seq
        if status_after is not None:
            order.status = status_after.value
        order.updated_at = now
        s.flush()  # make the event visible to the next _append in this transaction (autoflush may be off)
        return ev

    @staticmethod
    def _check_transition(current: str, target: OrderStatus) -> None:
        cur = OrderStatus(current)
        if target not in ALLOWED_TRANSITIONS[cur]:
            raise InvalidTransition(f"{cur.value} -> {target.value} is not allowed")

    # ── public API ───────────────────────────────────────────────────────────

    def create_order(self, req: OrderRequest, *, evidence: Mapping[str, Any] | None = None) -> tuple[LedgerOrder, bool]:
        """Idempotent create. Returns (order, created). Same key + same payload → existing order;
        same key + different payload → IdempotencyConflict."""
        if not (isinstance(req.idempotency_key, str) and req.idempotency_key.strip()):
            raise ValueError("idempotency_key required")
        for name in ("signal_id", "strategy_version", "symbol", "order_type"):
            if not (isinstance(getattr(req, name), str) and getattr(req, name).strip()):
                raise ValueError(f"{name} required")
        _require_decimal("quantity", req.quantity)
        if req.price is not None:
            _require_decimal("price", req.price)
        identity = req.identity_payload()
        phash = _sha256(canonical_json(identity))

        try:
            with self._sf() as s, s.begin():
                now = self._now()
                order = LedgerOrder(
                    order_id=str(uuid.uuid4()),
                    idempotency_key=req.idempotency_key,
                    payload_hash=phash,
                    signal_id=req.signal_id,
                    strategy_version=req.strategy_version,
                    symbol=req.symbol,
                    side=OrderSide(req.side).value,
                    order_type=req.order_type.upper(),
                    quantity=req.quantity,
                    price=req.price,
                    status=OrderStatus.PENDING.value,
                    last_event_seq=0,
                    created_at=now,
                    updated_at=now,
                )
                s.add(order)
                s.flush()  # UNIQUE(idempotency_key) enforced here
                self._append(s, order, EventType.REQUEST, {"request": identity, "idempotency_key": req.idempotency_key})
                if evidence:
                    self._append(s, order, EventType.EVIDENCE, evidence)
            created = True
        except IntegrityError:
            created = False
        with self._sf() as s:
            existing = s.execute(
                select(LedgerOrder).where(LedgerOrder.idempotency_key == req.idempotency_key)
            ).scalar_one_or_none()
            if existing is None:  # pragma: no cover - integrity error for another reason
                raise LedgerError(f"create_order failed for key {req.idempotency_key!r}")
            if existing.payload_hash != phash:
                raise IdempotencyConflict(
                    f"idempotency_key {req.idempotency_key!r} already used with a different payload"
                )
            s.expunge(existing)
            return existing, created

    def append_event(
        self,
        order_id: str,
        event_type: EventType,
        payload: Mapping[str, Any] | None = None,
        *,
        reason: str | None = None,
    ) -> LedgerOrderEvent:
        """Append a non-transition event (EVIDENCE / ERROR / REQUEST note)."""
        if event_type not in (EventType.EVIDENCE, EventType.ERROR):
            raise ValueError("append_event only for EVIDENCE/ERROR; use record_decision/transition for state changes")
        if event_type is EventType.ERROR and not reason:
            raise ValueError("ERROR event requires reason")
        with self._sf() as s, s.begin():
            order = self._lock_order(s, order_id)
            ev = self._append(s, order, event_type, payload, reason=reason)
            s.flush()
            s.expunge(ev)
            return ev

    def record_decision(
        self,
        order_id: str,
        decision: Decision,
        reason: str,
        *,
        approved_quantity: Decimal | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> LedgerOrder:
        """APPROVED/REDUCED → DECISION event, status APPROVED. REJECTED/BLOCKED → REFUSAL event."""
        if not reason:
            raise ValueError("decision requires reason")
        decision = Decision(decision)
        with self._sf() as s, s.begin():
            order = self._lock_order(s, order_id)
            data = dict(payload or {})
            if decision in (Decision.APPROVED, Decision.REDUCED):
                target = OrderStatus.APPROVED
                qty = order.quantity if approved_quantity is None else _require_decimal("approved_quantity", approved_quantity)
                if decision is Decision.REDUCED and approved_quantity is None:
                    raise ValueError("REDUCED requires approved_quantity")
                if qty > order.quantity:
                    raise ValueError("approved_quantity exceeds requested quantity")
                self._check_transition(order.status, target)
                order.approved_quantity = qty
                data["approved_quantity"] = qty
                self._append(s, order, EventType.DECISION, data, decision=decision, reason=reason, status_after=target)
            else:
                target = OrderStatus.REJECTED if decision is Decision.REJECTED else OrderStatus.BLOCKED
                self._check_transition(order.status, target)
                self._append(s, order, EventType.REFUSAL, data, decision=decision, reason=reason, status_after=target)
            s.flush()
            s.expunge(order)
            return order

    def transition(
        self,
        order_id: str,
        target: OrderStatus,
        *,
        reason: str,
        payload: Mapping[str, Any] | None = None,
    ) -> LedgerOrder:
        """Explicit transitions: SUBMITTED (SUBMISSION), CANCELLED/UNKNOWN (STATE), broker REJECTED (RESULT)."""
        target = OrderStatus(target)
        if target in (OrderStatus.APPROVED, OrderStatus.BLOCKED, OrderStatus.PENDING):
            raise InvalidTransition(f"use record_decision for {target.value}")
        if target in (OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED):
            raise InvalidTransition("fill states are reached only via record_fill")
        if not reason:
            raise ValueError("transition requires reason")
        etype = {
            OrderStatus.SUBMITTED: EventType.SUBMISSION,
            OrderStatus.REJECTED: EventType.RESULT,
        }.get(target, EventType.STATE)
        with self._sf() as s, s.begin():
            order = self._lock_order(s, order_id)
            if target is OrderStatus.REJECTED and order.status == OrderStatus.PENDING.value:
                raise InvalidTransition("policy rejection must go through record_decision")
            self._check_transition(order.status, target)
            self._append(s, order, etype, payload, reason=reason, status_after=target)
            s.flush()
            s.expunge(order)
            return order

    def record_error(self, order_id: str, reason: str, payload: Mapping[str, Any] | None = None) -> LedgerOrderEvent:
        return self.append_event(order_id, EventType.ERROR, payload, reason=reason)

    def record_fill(
        self,
        order_id: str,
        *,
        exchange_fill_id: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        fee_asset: str,
        filled_at: datetime,
    ) -> tuple[LedgerFill, bool]:
        """Idempotent on exchange_fill_id. Returns (fill, created)."""
        _require_decimal("quantity", quantity)
        _require_decimal("price", price)
        _require_decimal("fee", fee, allow_zero=True)
        if not (isinstance(exchange_fill_id, str) and exchange_fill_id.strip()):
            raise ValueError("exchange_fill_id required")
        if not fee_asset:
            raise ValueError("fee_asset required")

        def _same(f: LedgerFill) -> bool:
            return (
                f.order_id == order_id
                and f.quantity == quantity
                and f.price == price
                and f.fee == fee
                and f.fee_asset == fee_asset
            )

        with self._sf() as s:
            existing = s.execute(
                select(LedgerFill).where(LedgerFill.exchange_fill_id == exchange_fill_id)
            ).scalar_one_or_none()
            if existing is not None:
                if not _same(existing):
                    raise IdempotencyConflict(f"exchange_fill_id {exchange_fill_id!r} already recorded with other data")
                s.expunge(existing)
                return existing, False
        try:
            with self._sf() as s, s.begin():
                order = self._lock_order(s, order_id)
                if order.status not in (
                    OrderStatus.SUBMITTED.value,
                    OrderStatus.PARTIALLY_FILLED.value,
                    OrderStatus.UNKNOWN.value,
                ):
                    raise InvalidTransition(f"fill not allowed in status {order.status}")
                filled = sum(
                    (f.quantity for f in s.execute(select(LedgerFill).where(LedgerFill.order_id == order_id)).scalars()),
                    Decimal(0),
                )
                limit = order.approved_quantity if order.approved_quantity is not None else order.quantity
                total = filled + quantity
                if total > limit:
                    raise FillRejected(f"overfill: {total} > approved {limit}")
                target = OrderStatus.FILLED if total == limit else OrderStatus.PARTIALLY_FILLED
                self._check_transition(order.status, target)
                fill = LedgerFill(
                    order_id=order_id,
                    exchange_fill_id=exchange_fill_id,
                    quantity=quantity,
                    price=price,
                    fee=fee,
                    fee_asset=fee_asset,
                    filled_at=filled_at,
                    recorded_at=self._now(),
                )
                s.add(fill)
                s.flush()
                self._append(
                    s,
                    order,
                    EventType.RESULT,
                    {
                        "exchange_fill_id": exchange_fill_id,
                        "quantity": quantity,
                        "price": price,
                        "fee": fee,
                        "fee_asset": fee_asset,
                        "filled_at": filled_at,
                        "filled_total": total,
                    },
                    reason="fill",
                    status_after=target,
                )
                s.flush()
                s.expunge(fill)
                return fill, True
        except IntegrityError:
            # concurrent duplicate of the same exchange_fill_id
            with self._sf() as s:
                existing = s.execute(
                    select(LedgerFill).where(LedgerFill.exchange_fill_id == exchange_fill_id)
                ).scalar_one_or_none()
                if existing is None:
                    raise ConcurrentAppend(f"concurrent append on order {order_id}") from None
                if not _same(existing):
                    raise IdempotencyConflict(
                        f"exchange_fill_id {exchange_fill_id!r} already recorded with other data"
                    ) from None
                s.expunge(existing)
                return existing, False

    # ── read / verify ────────────────────────────────────────────────────────

    def get_order(self, order_id: str) -> LedgerOrder:
        with self._sf() as s:
            o = s.get(LedgerOrder, order_id)
            if o is None:
                raise OrderNotFound(order_id)
            s.expunge(o)
            return o

    def events(self, order_id: str) -> list[LedgerOrderEvent]:
        with self._sf() as s:
            evs = list(
                s.execute(
                    select(LedgerOrderEvent).where(LedgerOrderEvent.order_id == order_id).order_by(LedgerOrderEvent.seq)
                ).scalars()
            )
            for e in evs:
                s.expunge(e)
            return evs

    def fills(self, order_id: str) -> list[LedgerFill]:
        with self._sf() as s:
            fs = list(s.execute(select(LedgerFill).where(LedgerFill.order_id == order_id).order_by(LedgerFill.fill_id)).scalars())
            for f in fs:
                s.expunge(f)
            return fs

    def verify_chain(self, order_id: str) -> int:
        """Recompute the hash chain. Returns number of events; raises ChainBroken on tampering."""
        order = self.get_order(order_id)
        evs = self.events(order_id)
        prev = GENESIS_HASH
        for i, e in enumerate(evs, start=1):
            if e.seq != i:
                raise ChainBroken(order_id, e.seq, f"sequence gap (expected {i})")
            if e.prev_hash != prev:
                raise ChainBroken(order_id, e.seq, "prev_hash mismatch")
            h = compute_event_hash(
                prev_hash=e.prev_hash,
                order_id=e.order_id,
                seq=e.seq,
                event_type=e.event_type,
                decision=e.decision,
                reason=e.reason,
                status_before=e.status_before,
                status_after=e.status_after,
                payload_json=e.payload_json,
                created_at=e.created_at,
            )
            if h != e.event_hash:
                raise ChainBroken(order_id, e.seq, "event_hash mismatch (content altered)")
            prev = e.event_hash
        if len(evs) != order.last_event_seq:
            raise ChainBroken(order_id, len(evs), f"order.last_event_seq={order.last_event_seq} != events={len(evs)}")
        if evs and evs[-1].status_after != order.status:
            raise ChainBroken(order_id, evs[-1].seq, "order.status differs from last event status_after")
        return len(evs)

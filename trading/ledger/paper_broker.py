"""trading/ledger/paper_broker.py — deterministic, ledger-backed paper broker.

Properties:
  * no network, no keys, no RNG: prices come only from the MarketSnapshot passed in,
    the clock is injected, order ids are uuid5(idempotency_key), fill ids derive from order id;
  * Decimal everywhere (floats are refused), explicit quantisation with adverse rounding;
  * every step is written to OrderLedger (REQUEST → EVIDENCE → DECISION/REFUSAL → SUBMISSION →
    RESULT/fill → STATE), so the hash chain is the audit trail;
  * idempotent: resubmitting the same idempotency_key returns the existing order and never fills twice;
  * missing/invalid market data → REFUSAL BLOCKED; a price is never invented.

Required ``kill_switch``: checked before every new submission (engaged or unreadable → BLOCKED);
there is no way to construct the broker without one (fail-closed by construction).
Not wired into trading.factory / orchestrator / live paths; the legacy trading.paper_broker.PaperBroker
is untouched.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, localcontext
from typing import Callable

from .killswitch import KillSwitch
from .models import Decision, EventType, LedgerFill, LedgerOrder, OrderSide, OrderStatus
from .repository import OrderLedger, OrderRequest

PAPER_NAMESPACE = uuid.UUID("5b0f3c2e-8d1a-4f6e-9a57-2f0c1d7e4b90")
_BPS = Decimal(10000)
_PREC = 80  # working precision: exact for all supported magnitudes, no silent context rounding


def deterministic_order_id(req: OrderRequest) -> str:
    return str(uuid.uuid5(PAPER_NAMESPACE, req.idempotency_key))


def _is_dec(v: object) -> bool:
    return isinstance(v, Decimal) and v.is_finite()


@dataclass(frozen=True)
class MarketSnapshot:
    """Point-in-time market view supplied by the caller. Never fetched by the broker."""

    symbol: str
    price: Decimal | None  # reference (mid) price
    spread_bps: Decimal | None  # full bid-ask spread in bps; taker pays half
    as_of: datetime | None
    snapshot_id: str = ""
    available_qty: Decimal | None = None  # liquidity at the touch for the taker side; None = unlimited

    def evidence(self) -> dict:
        """Ledger-safe view: non-Decimal numerics (e.g. floats) are recorded as tagged reprs, never coerced."""

        def safe(v):
            if v is None or isinstance(v, (Decimal, str)):
                return v
            if isinstance(v, datetime):
                return v if v.tzinfo is not None else f"naive:{v.isoformat()}"
            return f"invalid:{type(v).__name__}:{v!r}"

        return {
            "snapshot_id": safe(self.snapshot_id),
            "symbol": safe(self.symbol),
            "price": safe(self.price),
            "spread_bps": safe(self.spread_bps),
            "available_qty": safe(self.available_qty),
            "as_of": safe(self.as_of),
        }


@dataclass(frozen=True)
class FixedBpsSlippage:
    """Decimal fixed-bps slippage applied on top of the half-spread (adverse direction)."""

    slippage_bps: Decimal = Decimal("5")

    def __post_init__(self) -> None:
        if not _is_dec(self.slippage_bps) or self.slippage_bps < 0:
            raise ValueError("slippage_bps must be a non-negative Decimal")

    def bps(self, side: OrderSide, qty: Decimal, snapshot: MarketSnapshot) -> Decimal:
        return self.slippage_bps


@dataclass(frozen=True)
class FeeSchedule:
    taker_bps: Decimal = Decimal("10")
    fee_asset: str = "USDT"
    min_fee: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not _is_dec(self.taker_bps) or self.taker_bps < 0:
            raise ValueError("taker_bps must be a non-negative Decimal")
        if not _is_dec(self.min_fee) or self.min_fee < 0:
            raise ValueError("min_fee must be a non-negative Decimal")


@dataclass(frozen=True)
class PaperOrder:
    idempotency_key: str
    signal_id: str
    strategy_version: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    limit_price: Decimal | None = None  # None → MARKET (IOC); else LIMIT IOC

    def to_request(self) -> OrderRequest:
        return OrderRequest(
            idempotency_key=self.idempotency_key,
            signal_id=self.signal_id,
            strategy_version=self.strategy_version,
            symbol=self.symbol,
            side=OrderSide(self.side),
            order_type="MARKET" if self.limit_price is None else "LIMIT",
            quantity=self.quantity,
            price=self.limit_price,
        )


@dataclass(frozen=True)
class PaperResult:
    order: LedgerOrder
    fills: list[LedgerFill]
    created: bool  # False → idempotent resubmit, nothing new was written

    @property
    def status(self) -> OrderStatus:
        return OrderStatus(self.order.status)


class DeterministicPaperBroker:
    def __init__(
        self,
        ledger: OrderLedger,
        clock: Callable[[], datetime],
        *,
        slippage: FixedBpsSlippage | None = None,
        fees: FeeSchedule | None = None,
        price_quantum: Decimal = Decimal("1e-8"),
        fee_quantum: Decimal = Decimal("1e-8"),
        max_snapshot_age_s: Decimal | None = None,
        kill_switch: KillSwitch,
    ):
        for name, q in (("price_quantum", price_quantum), ("fee_quantum", fee_quantum)):
            if not _is_dec(q) or q <= 0 or q.as_tuple().exponent < -18:
                raise ValueError(f"{name} must be a positive Decimal with ≤18 fractional digits")
        self.ledger = ledger
        self.clock = clock
        self.slippage = slippage or FixedBpsSlippage()
        self.fees = fees or FeeSchedule()
        self.price_quantum = price_quantum
        self.fee_quantum = fee_quantum
        self.max_snapshot_age_s = max_snapshot_age_s
        if not isinstance(kill_switch, KillSwitch) and not callable(getattr(kill_switch, "check", None)):
            raise TypeError("kill_switch is required (fail-closed): pass a KillSwitch")
        self.kill_switch = kill_switch

    # ── validation ───────────────────────────────────────────────────────────

    def _market_data_problem(self, order: PaperOrder, snap: MarketSnapshot | None) -> str | None:
        if snap is None:
            return "market_data_missing: no snapshot"
        if snap.symbol != order.symbol:
            return f"market_data_missing: snapshot symbol {snap.symbol!r} != order symbol {order.symbol!r}"
        if snap.price is None:
            return "market_data_missing: price"
        if not _is_dec(snap.price) or snap.price <= 0:
            return "market_data_invalid: price must be a positive finite Decimal"
        if snap.spread_bps is None:
            return "market_data_missing: spread_bps"
        if not _is_dec(snap.spread_bps) or snap.spread_bps < 0:
            return "market_data_invalid: spread_bps must be a non-negative finite Decimal"
        if snap.available_qty is not None and (not _is_dec(snap.available_qty) or snap.available_qty < 0):
            return "market_data_invalid: available_qty must be a non-negative finite Decimal"
        if snap.as_of is None:
            return "market_data_missing: as_of"
        if not isinstance(snap.as_of, datetime) or snap.as_of.tzinfo is None:
            return "market_data_invalid: as_of must be timezone-aware"
        if self.max_snapshot_age_s is not None:
            age = Decimal(str((self.clock() - snap.as_of).total_seconds()))
            if age > self.max_snapshot_age_s:
                return f"market_data_stale: age {age}s > {self.max_snapshot_age_s}s"
            if age < 0:
                return "market_data_invalid: snapshot from the future"
        return None

    # ── pricing (pure) ───────────────────────────────────────────────────────

    def quote(self, order: PaperOrder, snap: MarketSnapshot) -> dict:
        """Pure, deterministic execution quote. Requires a validated snapshot."""
        side = OrderSide(order.side)
        with localcontext() as ctx:
            ctx.prec = _PREC
            slip = self.slippage.bps(side, order.quantity, snap)
            total_bps = snap.spread_bps / 2 + slip
            if side is OrderSide.BUY:
                raw = snap.price * (1 + total_bps / _BPS)
                px = raw.quantize(self.price_quantum, rounding=ROUND_CEILING)
            else:
                raw = snap.price * (1 - total_bps / _BPS)
                px = raw.quantize(self.price_quantum, rounding=ROUND_FLOOR)
            qty = order.quantity if snap.available_qty is None else min(order.quantity, snap.available_qty)
            fee = max(
                (qty * px * self.fees.taker_bps / _BPS).quantize(self.fee_quantum, rounding=ROUND_CEILING),
                self.fees.min_fee if qty > 0 else Decimal(0),
            )
        return {"exec_price": px, "fill_qty": qty, "fee": fee, "total_bps": total_bps, "slippage_bps": slip}

    # ── main entry ───────────────────────────────────────────────────────────

    def submit(self, order: PaperOrder, snapshot: MarketSnapshot | None) -> PaperResult:
        led = self.ledger
        rec, created = led.create_order(order.to_request())
        oid = rec.order_id
        if not created:
            return PaperResult(led.get_order(oid), led.fills(oid), created=False)

        scopes: list[list[str]] = []
        try:
            ks = self.kill_switch.check(symbol=order.symbol, strategy=order.strategy_version)
            engaged, why = ks.engaged, ks.reason
            scopes = [list(x) for x in ks.scopes]
        except Exception as e:  # noqa: BLE001 — fail closed
            engaged, why = True, f"kill_switch_unreadable: {type(e).__name__}"
        if engaged:
            led.record_decision(oid, Decision.BLOCKED, f"kill_switch_engaged: {why}",
                                payload={"kill_switch": {"scopes": scopes, "reason": why}})
            return PaperResult(led.get_order(oid), [], created=True)

        problem = self._market_data_problem(order, snapshot)
        if problem is not None:
            led.record_decision(
                oid, Decision.BLOCKED, problem,
                payload={"snapshot": snapshot.evidence() if isinstance(snapshot, MarketSnapshot) else None},
            )
            return PaperResult(led.get_order(oid), [], created=True)

        q = self.quote(order, snapshot)
        led.append_event(oid, EventType.EVIDENCE, {
            "snapshot": snapshot.evidence(),
            "quote": q,
            "model": {"slippage_bps": self.slippage.slippage_bps, "taker_fee_bps": self.fees.taker_bps,
                      "fee_asset": self.fees.fee_asset, "price_quantum": self.price_quantum},
        })
        led.record_decision(oid, Decision.APPROVED, "paper: market data present")
        led.transition(oid, OrderStatus.SUBMITTED, reason="paper submit",
                       payload={"venue": "paper-deterministic", "snapshot_id": snapshot.snapshot_id})

        px, qty = q["exec_price"], q["fill_qty"]
        side = OrderSide(order.side)
        if order.limit_price is not None and (
            (side is OrderSide.BUY and px > order.limit_price) or (side is OrderSide.SELL and px < order.limit_price)
        ):
            led.transition(oid, OrderStatus.CANCELLED, reason="IOC: limit not marketable",
                           payload={"exec_price": px, "limit_price": order.limit_price})
            return PaperResult(led.get_order(oid), [], created=True)
        if qty <= 0:
            led.transition(oid, OrderStatus.CANCELLED, reason="IOC: no liquidity at touch",
                           payload={"available_qty": snapshot.available_qty})
            return PaperResult(led.get_order(oid), [], created=True)

        led.record_fill(oid, exchange_fill_id=f"paper:{oid}:1", quantity=qty, price=px,
                        fee=q["fee"], fee_asset=self.fees.fee_asset, filled_at=self.clock())
        if qty < order.quantity:
            led.transition(oid, OrderStatus.CANCELLED, reason="IOC: remainder cancelled (liquidity)",
                           payload={"filled": qty, "remainder": order.quantity - qty})
        return PaperResult(led.get_order(oid), led.fills(oid), created=True)

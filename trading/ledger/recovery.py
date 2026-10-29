"""trading/ledger/recovery.py — startup recovery of non-terminal ledger orders.

Never submits orders and never records fills. For each non-terminal order (deterministic order):

  1. verify its hash chain — broken → GLOBAL kill switch engaged, order left untouched;
  2. reconcile:
     * PENDING (never submitted)       → REFUSAL BLOCKED "recovery: not submitted before restart"
     * APPROVED (never submitted)      → CANCELLED
     * SUBMITTED / PARTIALLY_FILLED / UNKNOWN on the deterministic paper venue: paper orders are
       IOC and fills are written atomically, so the recorded fills are the truth → remainder CANCELLED
       (or nothing to do if inconsistent, see below);
     * anything that cannot be reconciled (other/unknown venue, fills inconsistent with status)
       → UNKNOWN (if not already) + kill switch engaged for that order's SYMBOL scope.

Idempotent: a second run finds only the irreconcilable UNKNOWN orders, whose kill switch is
already engaged; no events or audit rows are written again.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal

from .killswitch import KillSwitch
from .models import Decision, EventType, KillScope, OrderStatus
from .repository import ChainBroken, OrderLedger

PAPER_VENUE = "paper-deterministic"


@dataclass(frozen=True)
class RecoveryAction:
    order_id: str
    status_before: str
    action: str  # BLOCKED | CANCELLED | MARKED_UNKNOWN | KEPT_UNKNOWN | CHAIN_BROKEN | KILL_SWITCH
    detail: str
    status_after: str


@dataclass
class RecoveryReport:
    scanned: int = 0
    actions: list[RecoveryAction] = field(default_factory=list)
    broken_chains: list[str] = field(default_factory=list)
    kill_switch_engaged: list[tuple[str, str, str]] = field(default_factory=list)  # (scope, key, reason) changed now

    @property
    def clean(self) -> bool:
        return not self.broken_chains and not any(a.action in ("MARKED_UNKNOWN", "KEPT_UNKNOWN") for a in self.actions)


def _submission_venue(events) -> str | None:
    for e in events:
        if e.event_type == EventType.SUBMISSION.value:
            try:
                return json.loads(e.payload_json).get("venue")
            except (ValueError, AttributeError):
                return None
    return None


def recover(ledger: OrderLedger, kill_switch: KillSwitch, *, actor: str = "recovery") -> RecoveryReport:
    rep = RecoveryReport()
    tag = {"recovery": True}

    def engage(scope: KillScope, key: str | None, reason: str) -> None:
        if kill_switch.engage(scope, key, reason=reason, actor=actor):
            rep.kill_switch_engaged.append((scope.value, key or "*", reason))
        rep.actions.append(RecoveryAction(oid, status, "KILL_SWITCH", f"{scope.value}:{key or '*'} {reason}", status))

    for order in ledger.open_orders():
        rep.scanned += 1
        oid, status = order.order_id, order.status
        try:
            ledger.verify_chain(oid)
        except ChainBroken as e:
            rep.broken_chains.append(oid)
            rep.actions.append(RecoveryAction(oid, status, "CHAIN_BROKEN", str(e), status))
            engage(KillScope.GLOBAL, None, f"recovery: broken hash chain on order {oid}")
            continue

        st = OrderStatus(status)
        if st is OrderStatus.PENDING:
            ledger.record_decision(oid, Decision.BLOCKED, "recovery: not submitted before restart", payload=tag)
            rep.actions.append(RecoveryAction(oid, status, "BLOCKED", "never submitted", OrderStatus.BLOCKED.value))
            continue
        if st is OrderStatus.APPROVED:
            ledger.transition(oid, OrderStatus.CANCELLED, reason="recovery: approved but never submitted", payload=tag)
            rep.actions.append(RecoveryAction(oid, status, "CANCELLED", "never submitted", OrderStatus.CANCELLED.value))
            continue

        events = ledger.events(oid)
        venue = _submission_venue(events)
        filled = sum((f.quantity for f in ledger.fills(oid)), Decimal(0))
        limit = order.approved_quantity if order.approved_quantity is not None else order.quantity
        why = None
        if venue != PAPER_VENUE:
            why = f"venue {venue!r} cannot be reconciled offline"
        elif filled >= limit:
            why = f"inconsistent: filled {filled} >= approved {limit} but status {status}"
        elif st is OrderStatus.PARTIALLY_FILLED and filled == 0:
            why = "inconsistent: PARTIALLY_FILLED without fills"

        if why is None:
            ledger.transition(oid, OrderStatus.CANCELLED,
                              reason=f"recovery: paper IOC remainder cancelled (filled {filled} of {limit})",
                              payload={**tag, "filled": filled, "approved": limit})
            rep.actions.append(RecoveryAction(oid, status, "CANCELLED", f"paper filled {filled}/{limit}",
                                              OrderStatus.CANCELLED.value))
            continue

        if st is OrderStatus.UNKNOWN:
            rep.actions.append(RecoveryAction(oid, status, "KEPT_UNKNOWN", why, status))
        else:
            ledger.transition(oid, OrderStatus.UNKNOWN, reason=f"recovery: {why}", payload=tag)
            rep.actions.append(RecoveryAction(oid, status, "MARKED_UNKNOWN", why, OrderStatus.UNKNOWN.value))
            status = OrderStatus.UNKNOWN.value
        engage(KillScope.SYMBOL, order.symbol, f"recovery: unreconciled order {oid}: {why}")
    return rep

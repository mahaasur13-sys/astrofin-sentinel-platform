#!/usr/bin/env python3
"""ROMA Billing Ledger — append-only ledger of all billing state changes."""
import json
import logging
import time
from typing import Optional

log = logging.getLogger(__name__)


class BillingLedger:
    """Append-only ledger — every billing event is recorded, never mutated."""
    def __init__(self):
        self._entries: list[dict] = []

    def append(self, tenant_id: str, entry_type: str, amount: float, currency: str = "USD", metadata: dict = None, partner_id: str = None, revenue_share_percent: float = None) -> None:
        entry = {
            "ledger_id": f"led-{len(self._entries) + 1:06d}",
            "timestamp": time.time(),
            "tenant_id": tenant_id,
            "type": entry_type,
            "amount": amount,
    "partner_id": partner_id or "platform",
    "revenue_share_percent_applied": revenue_share_percent,
            "currency": currency,
            "metadata": metadata or {},
        }
        self._entries.append(entry)

    def credit(self, tenant_id: str, amount: float, currency: str = "USD", **meta) -> None:
        self.append(tenant_id, "CREDIT", amount, currency, meta)

    def debit(self, tenant_id: str, amount: float, currency: str = "USD", **meta) -> None:
        self.append(tenant_id, "DEBIT", amount, currency, meta)

    def get_tenant_balance(self, tenant_id: str) -> float:
        balance = 0.0
        for e in self._entries:
            if e["tenant_id"] == tenant_id:
                if e["type"] == "CREDIT":
                    balance += e["amount"]
                elif e["type"] == "DEBIT":
                    balance -= e["amount"]
        return balance

    def get_tenant_entries(self, tenant_id: str) -> list[dict]:
        return [e for e in self._entries if e["tenant_id"] == tenant_id]

    def ledger_summary(self) -> dict:
        by_tenant = {}
        for e in self._entries:
            t = e["tenant_id"]
            if t not in by_tenant:
                by_tenant[t] = {"credits": 0.0, "debits": 0.0, "net": 0.0, "entries": 0}
            by_tenant[t]["entries"] += 1
            if e["type"] == "CREDIT":
                by_tenant[t]["credits"] += e["amount"]
            elif e["type"] == "DEBIT":
                by_tenant[t]["debits"] += e["amount"]
        for t in by_tenant:
            by_tenant[t]["net"] = by_tenant[t]["credits"] - by_tenant[t]["debits"]
        return by_tenant
    # ─── Revenue-Share Extension ─────────────────────────────────────────────
    def record_revenue_share(self, tenant_id: str, amount_cents: int,
                            source_invoice: str, rate: float) -> None:
        now = int(time.time())
        period = time.strftime("%Y-%m")
        self._cur.execute("""
            INSERT OR IGNORE INTO revenue_share
                (tenant_id, amount_cents, source_invoice, rate, period_month, created_at, paid_out)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (tenant_id, amount_cents, source_invoice, rate, period, now))
        self._conn.commit()
    def get_monthly_revenue(self, tenant_id: str, month: Optional[str] = None) -> float:
        if month is None:
            month = time.strftime("%Y-%m")
        self._cur.execute("""
            SELECT COALESCE(SUM(amount_cents), 0)
            FROM billing_ledger
            WHERE tenant_id = ? AND strftime('%%Y-%%m', datetime(timestamp, 'unixepoch')) = ?
        """, (tenant_id, month))
        return self._cur.fetchone()[0] / 100.0
    def get_pending_revenue_share(self, tenant_id: str) -> int:
        self._cur.execute("""
            SELECT COALESCE(SUM(amount_cents), 0)
            FROM revenue_share WHERE tenant_id = ? AND paid_out = 0
        """, (tenant_id,))
        return self._cur.fetchone()[0]


def simulate_ledger() -> None:
    ledger = BillingLedger()
    ledger.credit("tenant-abc", 100.0, metadata={"source": "subscription", "plan": "PRO"})
    ledger.credit("tenant-abc", 10.0, metadata={"source": "credit_topup"})
    ledger.debit("tenant-abc", 3.20, metadata={"description": "GPU usage 2h @ $0.0016/sec"})
    ledger.debit("tenant-abc", 0.60, metadata={"description": "plugin execution 1 unit"})
    ledger.debit("tenant-xyz", 1.00, metadata={"description": "FREE tier GPU usage"})
    log.info("Tenant ABC balance:", f"${ledger.get_tenant_balance('tenant-abc'):.2f}")
    log.info("Tenant XYZ balance:", f"${ledger.get_tenant_balance('tenant-xyz'):.2f}")
    summary = ledger.ledger_summary()
    log.info("Summary:", json.dumps(summary, indent=2))

if __name__ == "__main__":
    simulate_ledger()

# Revenue-share extension (dev helper only)
# NOTE: record_revenue_share, get_monthly_revenue, get_pending_revenue_share
# are already added as class methods above in the class definition

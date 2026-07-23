"""ROMA SaaS - Stripe Billing Integration."""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class BillingEvent(str, Enum):
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    USAGE_RECORDED = "usage_recorded"
    INVOICE_PAID = "invoice_paid"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    TRIALING = "trialing"


@dataclass
class StripeCustomer:
    id: str
    org_id: str
    email: str
    stripe_customer_id: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass
class Subscription:
    id: str
    org_id: str
    tier: str
    status: SubscriptionStatus
    current_period_start: float
    current_period_end: float
    cancel_at_period_end: bool = False


@dataclass
class UsageRecord:
    id: str
    org_id: str
    key_id: str
    gpu_seconds: float
    cost: float
    job_id: str = ""
    plugin: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class Invoice:
    id: str
    org_id: str
    items: list[dict]
    total: float
    status: str
    currency: str = "USD"
    due_date: float = 0
    paid_at: float = 0
    created_at: float = field(default_factory=time.time)


GPU_RATES = {
    "RTX3060": 0.000055,
    "RTX4090": 0.000139,
    "A100": 0.000555,
    "H100": 0.001389,
}
TIER_MULT = {"free": 0.0, "pro": 1.0, "enterprise": 2.5}


class StripeIntegration:
    def __init__(self):
        self._customers: dict[str, StripeCustomer] = {}
        self._subscriptions: dict[str, Subscription] = {}
        self._usage: list[UsageRecord] = []
        self._invoices: dict[str, Invoice] = {}
        self._balance: dict[str, float] = {}

    def create_customer(self, org_id: str, email: str) -> StripeCustomer:
        c = StripeCustomer(
            id=f"cus_{uuid.uuid4().hex[:14]}",
            org_id=org_id,
            email=email,
            stripe_customer_id=f"cus_stripe_{uuid.uuid4().hex[:8]}",
        )
        self._customers[org_id] = c
        self._balance[org_id] = 0
        return c

    def create_subscription(self, org_id: str, tier: str) -> Subscription:
        now = time.time()
        s = Subscription(
            id=f"sub_{uuid.uuid4().hex[:12]}",
            org_id=org_id,
            tier=tier,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=now + 30 * 24 * 3600,
        )
        self._subscriptions[org_id] = s
        return s

    def cancel_subscription(self, org_id: str) -> bool:
        if org_id in self._subscriptions:
            self._subscriptions[org_id].status = SubscriptionStatus.CANCELLED
            return True
        return False

    def get_subscription(self, org_id: str) -> Subscription | None:
        return self._subscriptions.get(org_id)

    def record_usage(
        self,
        org_id: str,
        key_id: str,
        gpu_seconds: float,
        cost: float,
        job_id: str = "",
        plugin: str = "",
    ) -> UsageRecord:
        rec = UsageRecord(
            id=f"usr_{uuid.uuid4().hex[:12]}",
            org_id=org_id,
            key_id=key_id,
            gpu_seconds=gpu_seconds,
            cost=cost,
            job_id=job_id,
            plugin=plugin,
        )
        self._usage.append(rec)
        self._balance[org_id] = self._balance.get(org_id, 0) + cost
        return rec

    def get_usage(self, org_id: str) -> list[UsageRecord]:
        return [r for r in self._usage if r.org_id == org_id]

    def get_usage_summary(self, org_id: str) -> dict[str, Any]:
        records = self.get_usage(org_id)
        return {
            "total_gpu_seconds": sum(r.gpu_seconds for r in records),
            "total_cost": round(sum(r.cost for r in records), 6),
            "record_count": len(records),
            "jobs": len({r.job_id for r in records if r.job_id}),
        }

    def generate_invoice(self, org_id: str) -> Invoice:
        usage = self.get_usage(org_id)
        inv = Invoice(
            id=f"INV_{uuid.uuid4().hex[:8].upper()}",
            org_id=org_id,
            items=[
                {
                    "desc": r.plugin or "GPU compute",
                    "gpu_s": r.gpu_seconds,
                    "cost": r.cost,
                }
                for r in usage
            ],
            total=round(sum(r.cost for r in usage), 4),
            status="open",
        )
        self._invoices[f"{org_id}:{inv.id}"] = inv
        return inv

    def pay_invoice(self, invoice_id: str, org_id: str) -> bool:
        inv = self._invoices.get(f"{org_id}:{invoice_id}")
        if not inv or inv.status == "paid":
            return False
        inv.status = "paid"
        inv.paid_at = time.time()
        return True

    def estimate_job_cost(self, gpu_seconds: float, gpu_model: str = "A100", tier: str = "pro") -> float:
        rate = GPU_RATES.get(gpu_model, GPU_RATES["A100"])
        mult = TIER_MULT.get(tier, 1.0)
        if mult == 0:
            return 0.0
        return gpu_seconds * rate * mult

    def get_balance(self, org_id: str) -> float:
        return self._balance.get(org_id, 0)


class WebhookSimulator:
    def __init__(self, stripe: StripeIntegration):
        self.stripe = stripe
        self._events: list[dict] = []

    def simulate_payment_success(self, org_id: str, invoice_id: str, amount_cents: int):
        e = {
            "type": "payment_intent.succeeded",
            "org_id": org_id,
            "invoice_id": invoice_id,
            "amount_cents": amount_cents,
        }
        self._events.append(e)
        self.stripe.pay_invoice(invoice_id, org_id)
        return e

    def simulate_subscription_created(self, org_id: str, tier: str):
        s = self.stripe.create_subscription(org_id, tier)
        e = {
            "type": "customer.subscription.created",
            "org_id": org_id,
            "sub_id": s.id,
            "tier": tier,
        }
        self._events.append(e)
        return e

    def get_events(self, org_id: str = "") -> list[dict]:
        if org_id:
            return [e for e in self._events if e.get("org_id") == "" or e["org_id"] == org_id]
        return self._events


if __name__ == "__main__":
    s = StripeIntegration()
    w = WebhookSimulator(s)

    print("=== ROMA SaaS Stripe Demo ===\n")

    c = s.create_customer("org_acme", "billing@acme.com")
    print(f"[1] Customer: {c.id}")

    sub = s.create_subscription("org_acme", "pro")
    print(f"[2] Subscription: {sub.id} | {sub.status.value} | tier={sub.tier}")

    job_specs = [
        (3600, "ml_training", "job-yolo-1"),
        (7200, "inference", "job-inf-1"),
        (18000, "ml_training", "job-llm-1"),
    ]
    for gpu_s, plugin, job in job_specs:
        cost = s.estimate_job_cost(gpu_s, "A100", "pro")
        s.record_usage("org_acme", c.id[:12], gpu_s, cost, job, plugin)
    print(f"[3] Usage: {len(s.get_usage('org_acme'))} records")

    u = s.get_usage_summary("org_acme")
    print(f"[4] Summary: {u['total_gpu_seconds']:.0f}s | ${u['total_cost']:.4f} | {u['jobs']} jobs")

    inv = s.generate_invoice("org_acme")
    print(f"[5] Invoice: {inv.id} | ${inv.total:.4f} | {len(inv.items)} items")

    evt = w.simulate_payment_success("org_acme", inv.id, int(inv.total * 100))
    print(f"[6] Payment: {evt['type']} | ${evt['amount_cents']/100:.4f}")

    print(f"\n[7] Balance: ${s.get_balance('org_acme'):.4f}")
    est = s.estimate_job_cost(36000, "A100", "pro")
    print(f"[8] Estimate 10hr A100 PRO: ${est:.4f}")
    print(f"\nTotal revenue: ${sum(r.cost for r in s.get_usage('org_acme')):.4f}")
    print(f"Active subs: {sum(1 for x in s._subscriptions.values() if x.status==SubscriptionStatus.ACTIVE)}")

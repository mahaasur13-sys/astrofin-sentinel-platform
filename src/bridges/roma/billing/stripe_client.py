#!/usr/bin/env python3
"""
ROMA Stripe Client — Metered billing integration.
Maps: ROMA billing events → Stripe usage records → invoice finalization.
"""

from dataclasses import dataclass
from typing import Callable
import time
import hashlib
import hmac


@dataclass
class StripeConfig:
    api_key: str
    webhook_secret: str
    mode: str = "test"  # test | live


@dataclass
class StripeUsageRecord:
    customer_id: str
    quantity: float
    unit: str  # "gpu_second" | "request" | etc
    timestamp: float
    idempotency_key: str


class StripeBillingClient:
    def __init__(self, config: StripeConfig):
        self._config = config
        self._customers: dict[str, str] = {}  # tenant_id → stripe_customer_id
        self._subscriptions: dict[str, str] = {}  # tenant_id → stripe_sub_id
        self._usage_records: list[StripeUsageRecord] = []

    def create_customer(self, tenant_id: str, email: str, name: str) -> str:
        cid = f"cus_{hashlib.md5(tenant_id.encode()).hexdigest()[:14]}"
        self._customers[tenant_id] = cid
        print(f"  [Stripe] Customer created: {cid} for tenant {tenant_id}")
        return cid

    def create_subscription(self, tenant_id: str, plan: str) -> str:
        sid = f"sub_{hashlib.md5((tenant_id + plan).encode()).hexdigest()[:14]}"
        self._subscriptions[tenant_id] = sid
        print(f"  [Stripe] Subscription: {sid} (plan={plan})")
        return sid

    def submit_usage_record(self, record: StripeUsageRecord) -> dict:
        self._usage_records.append(record)
        return {
            "id": f"usr_{len(self._usage_records):06d}",
            "status": "recorded",
            "quantity": record.quantity,
            "customer": record.customer_id,
        }

    def finalize_invoice(self, customer_id: str, usage_total: float) -> str:
        invoice_id = f"in_{int(time.time())}"
        print(f"  [Stripe] Invoice {invoice_id} finalized for customer {customer_id} | total=${usage_total:.4f}")
        return invoice_id

    def verify_webhook_signature(self, payload: bytes, sig: str) -> bool:
        if not self._config.webhook_secret:
            return True
        expected = hmac.new(self._config.webhook_secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)


@dataclass
class WebhookEvent:
    event_type: str
    data: dict


class StripeWebhookHandler:
    """Handles Stripe webhook events → ROMA billing state updates."""

    def __init__(self, stripe: StripeBillingClient, ledger_callback: Callable):
        self._stripe = stripe
        self._lc = ledger_callback

    def handle(self, payload: bytes, signature: str) -> dict:
        if not self._stripe.verify_webhook_signature(payload, signature):
            return {"status": "signature_failed"}

        import json

        raw = json.loads(payload)
        event = WebhookEvent(event_type=raw.get("type", ""), data=raw.get("data", {}).get("object", {}))
        print(f"  [Webhook] Processing: {event.event_type}")

        if event.event_type == "invoice.paid":
            tenant_id = event.data.get("metadata", {}).get("tenant_id", "unknown")
            amount = float(event.data.get("amount_paid", 0)) / 100.0
            self._lc.credit(tenant_id, amount, source="stripe_invoice_paid")
            return {"status": "processed", "action": "credit_applied"}

        elif event.event_type == "invoice.payment_failed":
            tenant_id = event.data.get("metadata", {}).get("tenant_id", "unknown")
            self._lc.debit(tenant_id, 0, source="stripe_payment_failed")
            return {"status": "processed", "action": "payment_failed_recorded"}

        elif event.event_type == "customer.subscription.updated":
            tenant_id = event.data.get("metadata", {}).get("tenant_id", "unknown")
            plan = event.data.get("items", {}).get("data", [{}])[0].get("price", {}).get("nickname", "unknown")
            self._lc.debit(tenant_id, 0, source=f"subscription_update_to_{plan}")
            return {"status": "processed", "action": "plan_updated"}

        return {"status": "ignored", "event": event.event_type}


if __name__ == "__main__":
    config = StripeConfig(api_key="sk_test_placeholder", webhook_secret="whsec_placeholder")
    stripe = StripeBillingClient(config)

    # Customer + subscription flow
    stripe.create_customer("tenant-abc", "billing@acme.com", "Acme Corp")
    stripe.create_subscription("tenant-abc", "PRO")

    # Usage record
    record = StripeUsageRecord(
        customer_id="cus_abc123",
        quantity=7200.0,  # 2 hours GPU
        unit="gpu_second",
        timestamp=time.time(),
        idempotency_key="usage-001",
    )
    result = stripe.submit_usage_record(record)
    print(f"  [Stripe] Usage record: {result}")

    # Invoice
    inv = stripe.finalize_invoice("cus_abc123", 12.50)
    print(f"  [Stripe] Invoice: {inv}")

    # Webhook handler
    from billing.ledger import BillingLedger

    ledger = BillingLedger()
    wh = StripeWebhookHandler(stripe, ledger)

    import json

    test_payload = json.dumps({"type": "invoice.paid", "data": {"object": {"id": "in_123", "amount_paid": 1250, "metadata": {"tenant_id": "tenant-abc"}}}}).encode()
    result = wh.handle(test_payload, "sig_test")
    print(f"  [Webhook] Result: {result}")
    print(f"  [Ledger] ABC balance after webhook: ${ledger.get_tenant_balance('tenant-abc'):.2f}")

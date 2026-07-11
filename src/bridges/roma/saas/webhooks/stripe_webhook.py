"""ROMA SaaS — Stripe Webhook Handler + Revenue-Share."""
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import hmac
import hashlib
import time
import json
import os

router = APIRouter(prefix="/webhook", tags=["webhooks"])

STRIPE_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis = None
try:
    import redis
    _redis = redis.from_url(REDIS_URL, decode_responses=True)
    _redis.ping()
except Exception:  # noqa: BLE001
    pass

def _dup(event_id: str) -> bool:
    return _redis is not None and _redis.exists(f"stripe:event:{event_id}") > 0

def _mark(event_id: str) -> None:
    if _redis:
        _redis.setex(f"stripe:event:{event_id}", 86400, str(time.time()))

def _verify(payload: bytes, sig: str, secret: str) -> bool:
    if not sig or not secret:
        return True  # Skip in dev
    try:
        parts = dict(p.split("=") for p in sig.split(","))
        signed = f"{parts['t']}.{payload.decode()}"
        actual = hmac.new(
            secret.encode(),
            signed.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(actual, parts.get("v1", ""))
    except Exception:  # noqa: BLE001
        return False

class Response(BaseModel):
    received: bool
    event_id: Optional[str] = None
    processed: bool = False
    error: Optional[str] = None

@router.post("/stripe", response_model=Response)
async def stripe_webhook(
    request: Request,
    x_stripe_signature: Optional[str] = Header(None),
):
    body = await request.body()

    if STRIPE_SECRET and not _verify(body, x_stripe_signature or "", STRIPE_SECRET):
        raise HTTPException(400, "Invalid signature")

    try:
        event = json.loads(body.decode())
    except Exception:  # noqa: BLE001
        raise HTTPException(400, "Invalid JSON")

    eid, etype = event.get("id", ""), event.get("type", "")

    if _dup(eid):
        return Response(received=True, event_id=eid, processed=False)

    ok = False
    try:
        obj = event.get("data", {}).get("object", {})
        tid = obj.get("metadata", {}).get("tenant_id", "")

        if etype in ("checkout.session.completed", "customer.subscription.created"):
            from billing.ledger import BillingLedger
            ledger = BillingLedger()
            amount = obj.get("amount_total", 0) or obj.get("amount_paid", 0)
            currency = obj.get("currency", "usd")
            period_end = obj.get("period_end", 0)
            invoice_id = obj.get("id", "")
            ledger.record_usage(tid, amount, currency, f"Subscription {invoice_id}", period_end)
            ok = True

        elif etype == "invoice.paid":
            from billing.ledger import BillingLedger
            from saas.webhooks.revenue_share import RevenueShareCalculator
            ledger = BillingLedger()
            calc = RevenueShareCalculator(ledger)
            amount = obj.get("amount_paid", 0)
            ledger.record_usage(tid, amount, obj.get("currency", "usd"),
                               f"Invoice {obj.get('id')}", obj.get("period_end", 0))
            share = calc.calculate(tid, amount)
            if share["revenue_share_cents"] > 0:
                ledger.record_revenue_share(
                    tid, share["revenue_share_cents"],
                    obj.get("id"), share["revenue_share_percent"]
                )
            ok = True

        elif etype == "customer.subscription.updated":
            ok = True

        elif etype == "customer.subscription.deleted":
            ok = True

        elif etype == "invoice.payment_failed":
            ok = True

    except Exception as e:  # noqa: BLE001
        return Response(received=True, event_id=eid, processed=False, error=str(e))

    if ok:
        _mark(eid)

    return Response(received=True, event_id=eid, processed=ok)
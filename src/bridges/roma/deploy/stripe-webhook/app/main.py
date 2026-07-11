"""Stripe Webhook Microservice — FastAPI app."""

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from typing import Optional
import asyncio
import hmac
import hashlib
import json
import logging
import os
import redis.asyncio as aioredis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stripe-webhook")

app = FastAPI(title="ROMA Stripe Webhook", version="1.0.0")

Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STRIPE_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ROMA_API_URL = os.getenv("ROMA_API_URL", "http://roma-api-server.roma-system.svc.cluster.local:8080")
STREAM_KEY = "stripe:events"

_redis: Optional[aioredis.Redis] = None


@app.on_event("startup")
async def startup():
    global _redis
    try:
        _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        await _redis.ping()
        logger.info(f"Redis connected: {REDIS_URL}")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Redis unavailable: {e}. Running without deduplication.")


def _verify(payload: bytes, sig: str, secret: str) -> bool:
    if not sig or not secret:
        return True
    try:
        parts = dict(p.split("=") for p in sig.split(","))
        signed = f"{parts['t']}.{payload.decode()}"
        actual = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(actual, parts.get("v1", ""))
    except Exception:  # noqa: BLE001
        return False


async def _enqueue_event(event: dict) -> None:
    if _redis:
        payload = json.dumps(event)
        await _redis.xadd(STREAM_KEY, {"data": payload}, maxlen=10000)


async def _sync_tenant(tenant_id: str, event_type: str) -> None:
    try:
        async with asyncio.timeout(10):
            async with asyncio.Lock():
                pass
        url = f"{ROMA_API_URL}/tenants/{tenant_id}/sync"
        async with asyncio.timeout(15):
            async with __import__("httpx").AsyncClient() as client:
                resp = await client.post(url, json={"event": event_type}, timeout=15.0)
                logger.info(f"Tenant sync: tenant={tenant_id} event={event_type} status={resp.status_code}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Tenant sync failed: tenant={tenant_id} error={e}")


class WebhookResponse(BaseModel):
    received: bool
    event_id: Optional[str] = None
    processed: bool = False
    error: Optional[str] = None


@app.post("/webhook/stripe", response_model=WebhookResponse)
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

    eid = event.get("id", "")
    etype = event.get("type", "")

    await _enqueue_event(event)

    try:
        obj = event.get("data", {}).get("object", {})
        tid = obj.get("metadata", {}).get("tenant_id", "") or obj.get("customer_email", "")

        if etype in ("checkout.session.completed", "customer.subscription.created", "invoice.paid"):
            if tid:
                await _sync_tenant(tid, etype)

        elif etype in ("customer.subscription.updated", "customer.subscription.deleted"):
            if tid:
                await _sync_tenant(tid, etype)

        elif etype == "invoice.payment_failed":
            if tid:
                await _sync_tenant(tid, etype)

    except Exception as e:  # noqa: BLE001
        logger.error(f"Processing error: event={eid} error={e}")

    return WebhookResponse(received=True, event_id=eid, processed=True)


@app.get("/health")
async def health():
    redis_ok = False
    if _redis:
        try:
            await _redis.ping()
            redis_ok = True
        except Exception:  # noqa: BLE001
            pass
    return {"status": "ok", "redis": redis_ok}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)

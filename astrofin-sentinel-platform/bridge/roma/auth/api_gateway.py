#!/usr/bin/env python3
"""ROMA API Gateway — Rate limiting, key validation middleware, quota headers."""
from functools import wraps
from typing import Dict, Callable, Optional, Tuple
import time

# ── In-Memory Rate Limiter (Token Bucket) ────────────────────────────────────
class RateLimiter:
    def __init__(self):
        self.buckets: Dict[str, dict] = {}  # tenant_id → {tokens, last_refill}

    def check(self, tenant_id: str, rate_limit: int, window: int) -> Tuple[bool, dict]:
        """
        Token bucket: returns (allowed, info_dict).
        rate_limit = max tokens per window seconds.
        """
        now = time.time()
        if tenant_id not in self.buckets:
            self.buckets[tenant_id] = {"tokens": rate_limit, "last_refill": now, "cost": 0}
        b = self.buckets[tenant_id]
        elapsed = now - b["last_refill"]
        refill = elapsed * rate_limit / window
        b["tokens"] = min(rate_limit, b["tokens"] + refill)
        b["last_refill"] = now
        allowed = b["tokens"] >= 1
        if allowed:
            b["tokens"] -= 1
        return allowed, {
            "tenant_id": tenant_id,
            "tokens": round(b["tokens"], 2),
            "limit": rate_limit,
            "remaining": int(b["tokens"]),
            "reset_in_sec": round((1 - b["tokens"]) * window / rate_limit, 1) if b["tokens"] < 1 else 0
        }

# ── API Gateway ─────────────────────────────────────────────────────────────
class APIGateway:
    """
    Middleware layer: validates keys, enforces quotas, rate limits,
    attaches usage headers.
    """
    # Plan rate limits (req/min)
    PLAN_LIMITS = {
        "FREE":    (60,  60),    # (rate_limit, window_sec)
        "PRO":     (600, 60),
        "ENTERPRISE": (6000, 60),
    }
    # Plan quotas (GPU-seconds / month)
    PLAN_QUOTAS = {
        "FREE":       360_000,   # 100h GPU
        "PRO":        3_600_000,  # 1000h GPU
        "ENTERPRISE": 36_000_000, # 10000h GPU
    }

    def __init__(self, auth_engine, quota_engine):
        self.auth = auth_engine
        self.quotas = quota_engine
        self.rate_limiter = RateLimiter()
        self._middleware: list[Callable] = []

    def extract_key(self, request: dict) -> Optional[str]:
        """Extract API key from request dict. Checks header first, then query."""
        auth_header = request.get("headers", {}).get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return request.get("query", {}).get("api_key") or request.get("headers", {}).get("x-api-key")

    def extract_tenant(self, request: dict) -> Optional[str]:
        return request.get("headers", {}).get("x-tenant-id") or request.get("tenant_id")

    def middleware(self, func):
        """Decorator: apply gateway to handler."""
        @wraps(func)
        def wrapper(request: dict):
            # 1. Extract and validate key
            secret = self.extract_key(request)
            if not secret:
                return {"error": {"code": "API_KEY_REQUIRED",
                                  "message": "API key missing"}, "status": 401}
            key = self.auth.validate_key(secret)
            if not key:
                return {"error": {"code": "AUTH_FAILED",
                                  "message": "Invalid or expired API key"}, "status": 401}

            tenant_id = key.tenant_id

            # 2. Rate limit
            plan = self.auth.tenants.get(tenant_id, None)
            plan_name = plan.plan if plan else "FREE"
            rate, window = self.PLAN_LIMITS.get(plan_name, (60, 60))
            allowed, rl_info = self.rate_limiter.check(tenant_id, rate, window)
            if not allowed:
                return {"error": {"code": "RATE_LIMITED",
                                  "message": f"Rate limit: {rate} req/min"},
                        "status": 429, "headers": self._rate_headers(rl_info)}

            # 3. Quota check
            quota_limit = self.PLAN_QUOTAS.get(plan_name, 0)
            quota_used = self.quotas.get_usage(tenant_id)
            if quota_used >= quota_limit:
                return {"error": {"code": "QUOTA_EXCEEDED",
                                  "message": f"Monthly quota exceeded ({quota_limit} GPU-s)"},
                        "status": 402, "headers": self._quota_headers(quota_used, quota_limit)}

            # 4. Cost estimate header
            cost_estimate = self.quotas.estimate_cost(60, plan_name)

            # 5. Attach context
            request["_auth"] = {"key": key, "tenant_id": tenant_id,
                                "plan": plan_name, "quota_used": quota_used}
            response = func(request)
            if isinstance(response, dict):
                if "headers" not in response:
                    response["headers"] = {}
                response["headers"].update(self._rate_headers(rl_info))
                response["headers"].update(self._quota_headers(quota_used, quota_limit))
                response["headers"]["X-ROMA-Cost-Estimate"] = f"{cost_estimate:.4f}"
            return response
        return wrapper

    def _rate_headers(self, info: dict) -> dict:
        return {
            "X-ROMA-Rate-Limit-Remaining": str(info["remaining"]),
            "X-ROMA-Rate-Limit-Limit": str(info["limit"]),
            "X-ROMA-Rate-Limit-Reset": str(int(info["reset_in_sec"])),
        }

    def _quota_headers(self, used: float, limit: float) -> dict:
        return {
            "X-ROMA-Quota-Used": str(int(used)),
            "X-ROMA-Quota-Limit": str(int(limit)),
            "X-ROMA-Quota-Remaining": str(int(max(0, limit - used))),
        }


if __name__ == "__main__":
    from auth.engine import AuthEngine, KeyType
    from auth.quota_engine import QuotaEngine
    from billing.metering import MeteringEngine
    auth = AuthEngine()
    auth.create_tenant("tenant-test", "Test Tenant", "PRO")
    kid, sec = auth.create_key("tenant-test", "p1", KeyType.SERVER, "test", scopes=["submit"])
    auth.attach_key_to_tenant("tenant-test", kid)
    meter = MeteringEngine()
    quota = QuotaEngine(meter)
    gw = APIGateway(auth, quota)

    # Test: valid request
    req = {"headers": {"authorization": f"Bearer {sec}", "x-tenant-id": "tenant-test"}}
    def handler(req): return {"data": "ok"}
    resp = gw.middleware(handler)(req)
    print(f"Valid key → status={resp.get('status', 200)}, headers={list(resp.get('headers', {}).keys())}")

    # Test: missing key
    req2 = {"headers": {}}
    resp2 = gw.middleware(handler)(req2)
    print(f"Missing key → status={resp2.get('status')}")

    # Test: bad key
    req3 = {"headers": {"authorization": "Bearer sk_broken"}}
    resp3 = gw.middleware(handler)(req3)
    print(f"Bad key → status={resp3.get('status')}")

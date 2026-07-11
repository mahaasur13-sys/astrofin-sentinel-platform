"""ROMA SaaS API — Middleware (auth + logging)"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from saas_api.auth import verify_api_key, QuotaExceeded, RateLimitExceeded
import time


class LogRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        print(f"[ROMA] {request.method} {request.url.path} → {response.status_code} ({duration_ms:.1f}ms)")
        return response


def log_request(app):
    app.middleware("http")(LogRequestMiddleware)


def auth_middleware(request: Request) -> dict:
    """Extract and verify API key from Authorization header. Returns tenant context."""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, {"error": {"code": "UNAUTHORIZED", "message": "Missing Authorization header"}})
    token = auth[7:]
    try:
        ctx = verify_api_key(token)
        return ctx
    except QuotaExceeded as e:
        raise HTTPException(429, {"error": {"code": "QUOTA_EXCEEDED", "message": str(e)}})
    except RateLimitExceeded as e:
        raise HTTPException(429, {"error": {"code": "RATE_LIMITED", "message": str(e)}})
    except Exception:  # noqa: BLE001
        raise HTTPException(401, {"error": {"code": "INVALID_KEY", "message": "Invalid API key"}})

"""Security headers middleware (P1-13, originally drafted in P1-05).

Applies a baseline set of HTTP response headers to every request:

  * Strict-Transport-Security: max-age=63072000; includeSubDomains
  * X-Content-Type-Options: nosniff
  * X-Frame-Options: DENY
  * Referrer-Policy: no-referrer
  * Content-Security-Policy: default-src 'self'
  * Permissions-Policy: geolocation=(), microphone=(), camera=()
  * Cross-Origin-Opener-Policy: same-origin

HSTS is only emitted on HTTPS requests (either ``request.url.scheme == "https"``
or an ``X-Forwarded-Proto``/``X-Forwarded-Ssl`` header set to ``https``), so
local plain-HTTP development is not broken.

Attach to a FastAPI app via ``app.add_middleware(SecurityHeadersMiddleware)``.
The middleware composes cleanly with :class:`slowapi`\'s
:class:`SlowAPIMiddleware` — install SecurityHeaders first.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'self'",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

_HSTS_VALUE = "max-age=63072000; includeSubDomains"


def _is_https(request: Request) -> bool:
    if request.url.scheme == "https":
        return True
    fwd_proto = request.headers.get("x-forwarded-proto", "").strip().lower()
    if fwd_proto == "https":
        return True
    fwd_ssl = request.headers.get("x-forwarded-ssl", "").strip().lower()
    return fwd_ssl == "on"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline security headers to every response."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response: Response = await call_next(request)
        for name, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        if _is_https(request):
            response.headers.setdefault("Strict-Transport-Security", _HSTS_VALUE)
        return response


__all__ = ["SecurityHeadersMiddleware"]

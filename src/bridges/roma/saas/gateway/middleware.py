"""Gateway middleware assembly."""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from saas.gateway.tenant_middleware import TenantMiddleware
from saas.gateway.auth_middleware import AuthMiddleware
from saas.gateway.branding_injector import BrandingInjectorMiddleware
from saas.gateway.rate_limiter import check_rate_limit, rate_limit_dependency


def setup_gateway_middleware(
    app: FastAPI,
    tenant_config: dict = None,
    redis_url: str = None,
    jwt_secret: str = None,
    allowed_origins: list[str] = None,
) -> None:
    """
    Wire all gateway middleware into a FastAPI app.

    Starlette BaseHTTPMiddleware uses FIFO order:
    First add_middleware() = first in the request chain.

    Correct order (FIFO):
    1. TenantMiddleware    — MUST be added FIRST so it resolves tenant FIRST
    2. AuthMiddleware       — uses tenant_id set by TenantMiddleware
    3. BrandingInjector    — injects headers at response time
    4. CORS                 — outermost, handles preflight

    If CORS were added last (outermost), it would run first and reject
    OPTIONS requests before TenantMiddleware could set tenant context.
    """
    if allowed_origins is None:
        allowed_origins = ["*"]

    # Tenant resolution — MUST be added FIRST (runs first in chain)
    app.add_middleware(
        TenantMiddleware,
        tenant_config=tenant_config or {},
    )

    # Auth — runs AFTER tenant resolution (tenant_id already in request.state)
    app.add_middleware(
        AuthMiddleware,
        jwt_secret=jwt_secret,
        allowed_origins=allowed_origins,
        tenant_config=tenant_config or {},
    )

    # Branding injection — innermost in request chain
    app.add_middleware(
        BrandingInjectorMiddleware,
        tenant_config=tenant_config or {},
    )

    # CORS (outermost — added last so it wraps everything)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


__all__ = [
    "setup_gateway_middleware",
    "check_rate_limit",
    "rate_limit_dependency",
]

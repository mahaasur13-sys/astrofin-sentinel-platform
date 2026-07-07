"""Gateway router — mounts tenant-aware API routes."""
from fastapi import APIRouter, Request
from saas.gateway.models import GatewayConfig, TenantGatewayConfig
from saas.gateway.rate_limiter import rate_limit_dependency


gateway_router = APIRouter(prefix="/gateway", tags=["gateway"])


@gateway_router.get("/health")
async def gateway_health(request: Request):
    """Health check with tenant context."""
    return {
        "status": "ok",
        "gateway": "roma-execution-bridge",
        "version": "1.0.0",
        "tenant_id": getattr(request.state, "tenant_id", "unknown"),
    }


@gateway_router.get("/config")
async def gateway_config(request: Request):
    """Expose non-sensitive gateway config for the current tenant."""
    tenant_id = getattr(request.state, "tenant_id", "default")
    cfg: TenantGatewayConfig = getattr(request.state, "tenant_config", {})

    return {
        "tenant_id": tenant_id,
        "rate_limit": {
            "requests_per_minute": cfg.rate_limit.requests_per_minute if cfg.rate_limit else 60,
            "strategy": cfg.rate_limit.strategy.value if cfg.rate_limit else "in_memory",
        },
        "branding": {
            "enabled": cfg.branding.enabled if cfg.branding else False,
            "logo_url": cfg.branding.logo_url if cfg.branding else None,
        },
    }


@gateway_router.get("/tenant-info")
async def tenant_info(request: Request):
    """Public tenant metadata (safe to expose)."""
    tenant_id = getattr(request.state, "tenant_id", "unknown")
    cfg: TenantGatewayConfig = getattr(request.state, "tenant_config", {})

    return {
        "tenant_id": tenant_id,
        "display_name": cfg.display_name if cfg else "ROMA",
        "support_email": cfg.branding.support_email if cfg and cfg.branding else None,
    }


def mount_gateway_routes(app, gateway_config: GatewayConfig = None):
    """Mount gateway router and wire per-tenant configs."""
    if gateway_config:
        app.state.gateway_config = gateway_config

        for tenant_id, tenant_cfg in gateway_config.tenants.items():
            rate_limit_dependency(
                requests_per_minute=tenant_cfg.rate_limit.requests_per_minute,
                burst_size=tenant_cfg.rate_limit.burst_size,
                use_redis=tenant_cfg.rate_limit.use_redis,
            )

    app.include_router(gateway_router)

"""Integration tests for the full gateway stack."""

import pytest
from fastapi import FastAPI
from saas.gateway.middleware import setup_gateway_middleware
from saas.gateway.router import mount_gateway_routes
from saas.gateway.models import (
    GatewayConfig,
    TenantGatewayConfig,
    RateLimitConfig,
    BrandingConfig,
    AuthConfig,
)
from starlette.testclient import TestClient


@pytest.fixture
def full_gateway_app():
    tenant_configs = {
        "acme": TenantGatewayConfig(
            tenant_id="acme",
            display_name="ACME Corp",
            rate_limit=RateLimitConfig(requests_per_minute=120, burst_size=20),
            branding=BrandingConfig(inject_headers=True, logo_url="https://acme.com/logo.png"),
            auth=AuthConfig(require_api_key=True),
        ),
        "free": TenantGatewayConfig(
            tenant_id="free",
            display_name="Free Tier",
            rate_limit=RateLimitConfig(requests_per_minute=30, burst_size=5),
            branding=BrandingConfig(inject_headers=False),
            auth=AuthConfig(require_api_key=False),
        ),
    }

    app = FastAPI()
    gateway_cfg = GatewayConfig(tenants=tenant_configs)

    setup_gateway_middleware(
        app,
        tenant_config=tenant_configs,
        jwt_secret="test-secret",
        allowed_origins=["*"],
    )
    mount_gateway_routes(app, gateway_cfg)

    @app.get("/api/hello")
    async def hello():
        return {"message": "hello"}

    return app


class TestGatewayIntegration:
    def test_gateway_health(self, full_gateway_app):
        client = TestClient(full_gateway_app, raise_server_exceptions=False)
        resp = client.get("/gateway/health", headers={"X-Tenant-ID": "acme"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["tenant_id"] == "acme"

    def test_gateway_health_default_tenant(self, full_gateway_app):
        client = TestClient(full_gateway_app, raise_server_exceptions=False)
        resp = client.get("/gateway/health")
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == "default"

    def test_tenant_headers_injected(self, full_gateway_app):
        client = TestClient(full_gateway_app, raise_server_exceptions=False)
        resp = client.get("/gateway/health", headers={"X-Tenant-ID": "acme"})
        assert "x-tenant-id" in resp.headers
        assert resp.headers["x-tenant-id"] == "acme"

    def test_gateway_config_endpoint(self, full_gateway_app):
        client = TestClient(full_gateway_app, raise_server_exceptions=False)
        resp = client.get("/gateway/config", headers={"X-Tenant-ID": "acme"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == "acme"
        assert data["rate_limit"]["requests_per_minute"] == 120

    def test_tenant_info(self, full_gateway_app):
        client = TestClient(full_gateway_app, raise_server_exceptions=False)
        resp = client.get("/gateway/tenant-info", headers={"X-Tenant-ID": "acme"})
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "ACME Corp"

    def test_protected_route_without_api_key_returns_401(self, full_gateway_app):
        """ACME tenant requires API key — no key = 401."""
        client = TestClient(full_gateway_app, raise_server_exceptions=False)
        resp = client.get("/api/hello", headers={"X-Tenant-ID": "acme"})
        assert resp.status_code == 401

    def test_protected_route_with_short_api_key_returns_401(self, full_gateway_app):
        """ACME tenant requires API key — short key rejected (len < 16)."""
        client = TestClient(full_gateway_app, raise_server_exceptions=False)
        resp = client.get(
            "/api/hello",
            headers={"X-Tenant-ID": "acme", "X-API-Key": "short"},
        )
        assert resp.status_code == 401

    def test_protected_route_with_valid_api_key_succeeds(self, full_gateway_app):
        """ACME tenant accepts a valid-length API key (>= 16 chars)."""
        client = TestClient(full_gateway_app, raise_server_exceptions=False)
        resp = client.get(
            "/api/hello",
            headers={"X-Tenant-ID": "acme", "X-API-Key": "a-valid-api-key-here123"},
        )
        assert resp.status_code == 200

    def test_free_tier_allows_no_auth(self, full_gateway_app):
        """Free tier has require_api_key=False, so no key = OK."""
        client = TestClient(full_gateway_app, raise_server_exceptions=False)
        resp = client.get("/api/hello", headers={"X-Tenant-ID": "free"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "hello"

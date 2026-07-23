"""Tests for tenant_middleware.py."""
import pytest
from saas.gateway.tenant_middleware import TenantMiddleware
from saas.gateway.models import TenantGatewayConfig, BrandingConfig
from fastapi import FastAPI, Request
from starlette.testclient import TestClient


@pytest.fixture
def tenant_config():
    return {
        "acme": TenantGatewayConfig(
            tenant_id="acme",
            display_name="ACME Corp",
            branding=BrandingConfig(inject_headers=True, logo_url="https://acme.com/logo.png"),
        ),
        "beta": TenantGatewayConfig(
            tenant_id="beta",
            display_name="Beta Inc",
            branding=BrandingConfig(inject_headers=False),
        ),
    }


@pytest.fixture
def app(tenant_config):
    app = FastAPI()
    app.add_middleware(TenantMiddleware, tenant_config=tenant_config)
    
    @app.get("/test")
    async def test_route(request: Request):
        return {
            "tenant_id": request.state.tenant_id,
            "path": request.url.path,
        }
    
    return app


class TestTenantMiddleware:
    def test_resolves_tenant_from_header(self, app):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test", headers={"X-Tenant-ID": "acme"})
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == "acme"

    def test_resolves_tenant_from_subdomain(self, app):
        client = TestClient(app, base_url="http://acme.example.com", raise_server_exceptions=False)
        resp = client.get("/test")
        assert resp.status_code == 200

    def test_injects_tenant_headers(self, app, tenant_config):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test", headers={"X-Tenant-ID": "acme"})
        assert resp.status_code == 200
        assert "x-tenant-id" in resp.headers
        assert resp.headers["x-tenant-id"] == "acme"

    def test_default_tenant_when_none_resolved(self, app):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == "default"

    def test_require_tenant_raises_error(self, tenant_config):
        app = FastAPI()
        app.add_middleware(
            TenantMiddleware,
            tenant_config=tenant_config,
            require_tenant=True,
        )
        
        @app.get("/test")
        async def test_route(request: Request):
            return {"tenant_id": request.state.tenant_id}
        
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test")
        assert resp.status_code == 400

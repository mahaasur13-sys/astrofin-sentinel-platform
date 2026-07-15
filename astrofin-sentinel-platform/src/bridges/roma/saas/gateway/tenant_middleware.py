"""Tenant detection + routing middleware."""

from typing import Optional, Callable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import re


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Resolves tenant from:
    1. X-Tenant-ID header
    2. Subdomain (tenant.roma.ai)
    3. Path prefix (/t/{tenant_id}/...)
    4. API Key (looked up async)

    Injects tenant config into request.state.
    """

    DEFAULT_TENANT = "default"

    def __init__(
        self,
        app,
        tenant_config: dict = None,
        tenant_resolver: Callable = None,
        require_tenant: bool = False,
    ):
        super().__init__(app)
        self.tenant_config = tenant_config or {}
        self.tenant_resolver = tenant_resolver or self._default_resolver
        self.require_tenant = require_tenant

    async def dispatch(self, request: Request, call_next):
        try:
            tenant_id = await self._resolve_tenant(request)

            if not tenant_id and self.require_tenant:
                from starlette.responses import JSONResponse

                return JSONResponse({"detail": "Tenant ID required"}, status_code=400)

            request.state.tenant_id = tenant_id or self.DEFAULT_TENANT
            request.state.tenant_config = self.tenant_config.get(
                request.state.tenant_id, {}
            )

            response = await call_next(request)

            response.headers["X-Tenant-ID"] = request.state.tenant_id
            if tenant_config := self.tenant_config.get(request.state.tenant_id):
                if branding := getattr(tenant_config, "branding", None):
                    if branding.enabled and branding.inject_headers:
                        response.headers["X-Branding-Version"] = "1.0"
                        if branding.logo_url:
                            response.headers["X-Logo-URL"] = branding.logo_url

            return response
        except HTTPException:
            raise
        except Exception:
            raise

    async def _resolve_tenant(self, request: Request) -> Optional[str]:
        # 1. Header
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            return tenant_header

        # 2. Subdomain
        host = request.headers.get("host", "")
        subdomain = self._extract_subdomain(host)
        if subdomain and subdomain in self.tenant_config:
            return subdomain

        # 3. Path prefix /t/{tenant}/
        path = request.url.path
        match = re.match(r"^/t/([^/]+)(/.*)?$", path)
        if match:
            return match.group(1)

        # 4. API Key (async lookup)
        api_key = self._extract_api_key(request)
        if api_key:
            resolved = await self.tenant_resolver(api_key)
            if resolved:
                return resolved

        return None

    def _extract_subdomain(self, host: str) -> Optional[str]:
        # host = "acme.roma.ai" → "acme"
        if "." in host:
            parts = host.split(".")
            if len(parts) >= 3:
                return parts[0]
        return None

    def _extract_api_key(self, request: Request) -> Optional[str]:
        for header in ["X-API-KEY", "X-API-KEY", "API_KEY"]:
            if header in request.headers:
                return request.headers[header]
        return None

    async def _default_resolver(self, api_key: str) -> Optional[str]:
        """Override this for custom tenant resolution via DB/Redis/etc."""
        return None

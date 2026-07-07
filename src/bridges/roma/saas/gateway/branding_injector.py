"""Response branding injection — headers + optional HTML."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class BrandingInjectorMiddleware(BaseHTTPMiddleware):
    """
    Injects branding into responses:
    - Headers: X-Tenant-ID, X-Branding-Version, X-Logo-URL, X-Support-Email
    - HTML: optional injected meta tags / styles for HTML responses
    """

    def __init__(self, app, tenant_config: dict = None):
        super().__init__(app)
        self.tenant_config = tenant_config or {}

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        tenant_id = getattr(request.state, "tenant_id", "default")
        cfg = self.tenant_config.get(tenant_id)

        if not cfg:
            return response

        branding = getattr(cfg, "branding", None)
        if not branding or not branding.enabled:
            return response

        # Headers injection
        if branding.inject_headers:
            response.headers["X-Tenant-ID"] = tenant_id
            response.headers["X-Branding-Version"] = "1.0"
            if branding.logo_url:
                response.headers["X-Logo-URL"] = branding.logo_url
            if branding.support_email:
                response.headers["X-Support-Email"] = branding.support_email
            if branding.custom_css_url:
                response.headers["X-Custom-CSS-URL"] = branding.custom_css_url

        # HTML injection (only for text/html responses)
        if branding.inject_html_prefix:
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type and hasattr(response, "body"):
                body = response.body.decode("utf-8", errors="ignore")
                injected = self._inject_html(request, tenant_id, body, branding)
                response.body = injected.encode("utf-8")
                response.headers["content-length"] = str(len(response.body))

        return response

    def _inject_html(
        self, request: Request, tenant_id: str, body: str, branding
    ) -> str:
        meta_tags = f"""
        <meta name="tenant-id" content="{tenant_id}">
        <meta name="generated-by" content="ROMA Gateway">
        """
        if branding.logo_url:
            meta_tags += f'<link rel="icon" href="{branding.logo_url}">'
        if branding.custom_css_url:
            meta_tags += f'<link rel="stylesheet" href="{branding.custom_css_url}">'

        # Inject after <head>
        if "<head>" in body:
            body = body.replace("<head>", f"<head>{meta_tags}", 1)

        return body

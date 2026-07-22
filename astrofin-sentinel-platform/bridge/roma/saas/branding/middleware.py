"""
saas/branding/middleware.py
"""
from fastapi import Request, HTTPException, status
from .service import BrandingService
from .models import TenantBranding


async def get_current_branding(request: Request) -> TenantBranding:
    """Dependency for all routers — injects TenantBranding per request."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        # For public endpoints, return default branding
        return BrandingService.get_for_request(None)
    return BrandingService.get_for_request(api_key)


async def require_branded_request(request: Request) -> TenantBranding:
    """Dependency that requires valid API key and returns branded context."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
        )
    return BrandingService.get_for_request(api_key)

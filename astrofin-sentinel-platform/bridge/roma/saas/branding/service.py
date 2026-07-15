"""
saas/branding/service.py
"""
from .loader import load_by_tenant_id, load_by_api_key, load_default
from .models import TenantBranding


class BrandingService:
    @staticmethod
    def get_for_request(api_key: str | None = None) -> TenantBranding:
        if not api_key:
            return load_default()
        return load_by_api_key(api_key)

    @staticmethod
    def get_for_tenant(tenant_id: str) -> TenantBranding:
        return load_by_tenant_id(tenant_id)

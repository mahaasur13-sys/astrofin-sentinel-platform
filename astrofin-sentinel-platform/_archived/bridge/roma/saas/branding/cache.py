"""
saas/branding/cache.py
"""
from datetime import datetime, timedelta
from typing import Optional

from .models import TenantBranding


class BrandingCache:
    def __init__(self):
        self._cache: dict[str, dict] = {}

    def set(self, tenant_id: str, branding: TenantBranding, ttl_seconds: int = 300):
        self._cache[tenant_id] = {
            "branding": branding.model_dump(),
            "expires": datetime.utcnow() + timedelta(seconds=ttl_seconds),
        }

    def get(self, tenant_id: str) -> Optional[TenantBranding]:
        data = self._cache.get(tenant_id)
        if not data:
            return None
        if datetime.utcnow() > data["expires"]:
            del self._cache[tenant_id]
            return None
        return TenantBranding(**data["branding"])

    def clear(self, tenant_id: str | None = None):
        if tenant_id:
            self._cache.pop(tenant_id, None)
        else:
            self._cache.clear()


branding_cache = BrandingCache()

"""
saas/branding/loader.py
"""

import json
from pathlib import Path

from .cache import branding_cache
from .models import TenantBranding

BRANDING_DIR = Path(__file__).parent


def load_default() -> TenantBranding:
    """Default ROMA VEGA brand."""
    with open(BRANDING_DIR / "defaults.json") as f:
        data = json.load(f)
    return TenantBranding(**data)


def load_by_tenant_id(tenant_id: str) -> TenantBranding:
    """Main entry point for branding lookup."""
    cached = branding_cache.get(tenant_id)
    if cached:
        return cached

    # Per-tenant JSON override: saas/branding/tenants/{tenant_id}.json
    custom_path = BRANDING_DIR / "tenants" / f"{tenant_id}.json"
    if custom_path.exists():
        with open(custom_path) as f:
            data = json.load(f)
        branding = TenantBranding(**data)
    else:
        branding = load_default()
        branding.tenant_id = tenant_id  # Override per-tenant

    branding_cache.set(tenant_id, branding)
    return branding


def load_by_api_key(api_key: str) -> TenantBranding:
    """Shortcut: API key → branding."""
    from auth.api_keys import APIKeyManager

    mgr = APIKeyManager()
    result = mgr.validate_key(api_key)
    if result:
        tenant_id = result.get("tenant_id", "unknown")
    else:
        tenant_id = "unknown"
    return load_by_tenant_id(tenant_id)

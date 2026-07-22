"""
saas/branding/stripe_integration.py — Stripe metadata + invoice branding
"""
from typing import Optional
from .models import TenantBranding


def build_stripe_metadata(branding: TenantBranding, extra: Optional[dict] = None) -> dict:
    """Merge branding metadata into Stripe invoice/charge metadata."""
    base = {
        "brand": branding.metadata.get("brand", branding.tenant_id),
        "app_name": branding.app_name,
        "primary_color": branding.primary_color,
        "powered_by": branding.metadata.get("powered_by", ""),
    }
    if extra:
        base.update(extra)
    return base


def build_stripe_invoice_settings(
    branding: TenantBranding,
) -> dict:
    """Stripe Invoice settings for white-label billing."""
    return {
        "custom_fields": [
            {"name": "Cloud Platform", "value": branding.app_name},
            {"name": "Support", "value": branding.support_email},
        ],
        "metadata": build_stripe_metadata(branding),
        "footer": f"Powered by {branding.metadata.get('powered_by', 'ROMA')}",
    }

# WHITE-LABEL QUICKSTART

## Overview

ROM A supports white-label partners. Each partner gets their own brand (name, logo, colors, domain, email templates) while sharing the same infrastructure and codebase.

## Architecture

```
API Request (X-API-Key) 
  → APIKeyManager.validate_key()
  → BrandingService.get_for_request(api_key)
  → load_by_tenant_id(tenant_id)
      → check in-memory cache (TTL 5min)
      → load saas/branding/tenants/{tenant_id}.json
      → fallback: saas/branding/defaults.json
```

## Priority Chain

1. **White-label partner JSON** (`saas/branding/tenants/{tenant_id}.json`) — per-tenant full override
2. **Default ROMA branding** (`saas/branding/defaults.json`) — fallback

## Adding a New Partner

### Step 1: Create partner JSON

Create `saas/branding/tenants/{partner-slug}.json`:

```json
{
  "tenant_id": "partner-slug",
  "app_name": "PartnerName GPU Cloud",
  "logo_url": "https://partner.com/logo.png",
  "primary_color": "#10b981",
  "secondary_color": "#064e3b",
  "accent_color": "#f59e0b",
  "support_email": "support@partner.com",
  "from_name": "PartnerName GPU Cloud",
  "custom_domain": "gpu.partner.com",
  "metadata": {
    "brand": "partner-slug",
    "powered_by": "mahaasur13-sys"
  }
}
```

### Step 2: Verify it loads

```python
from saas.branding import BrandingService
b = BrandingService.get_for_tenant("partner-slug")
print(b.app_name, b.primary_color)
```

### Step 3: Stripe branding (optional)

Add partner Stripe credentials in `billing/stripe_connect.py`. The `build_stripe_metadata()` function automatically adds brand info to all invoices.

## Branding in API Responses

Use the `get_current_branding` dependency in any router:

```python
from fastapi import Depends
from saas.branding import TenantBranding, get_current_branding

@router.get("/info")
async def get_info(branding: TenantBranding = Depends(get_current_branding)):
    return {
        "app_name": branding.app_name,
        "logo": branding.logo_url,
        "support": branding.support_email,
    }
```

## Email Templates

Templates are in `saas/branding/templates/`. They use Jinja2 and receive a `branding: TenantBranding` object.

To send a branded invoice email:

```python
from jinja2 import Environment, FileSystemLoader
from saas.branding import load_by_tenant_id

env = Environment(loader=FileSystemLoader("saas/branding/templates"))
template = env.get_template("invoice_email.html.j2")
html = template.render(
    branding=load_by_tenant_id("acme-ai"),
    invoice_id="INV-001",
    customer_name="John Doe",
    gpu_hours=10,
    rate=3.0,
    gpu_cost=30.0,
    platform_fee=1.50,
    total=31.50,
    invoice_date="2026-04-01",
    due_date="2026-04-15",
)
```

## Stripe Integration

`branding/stripe_integration.py` provides:

- `build_stripe_metadata()` — adds brand info to invoice/charge metadata
- `build_stripe_invoice_settings()` — adds custom fields, footer, metadata to Stripe invoices

## Caching

- **In-memory** with 5-minute TTL
- Cache key: `tenant_id`
- No external Redis required
- To clear cache for a tenant:

```python
from saas.branding import branding_cache
branding_cache.clear("acme-ai")  # single tenant
branding_cache.clear()             # all tenants
```

## Example Partners

| Partner | File | Brand Color |
|---------|------|-------------|
| ROMA Default | `defaults.json` | #3b82f6 (blue) |
| AcmeAI | `tenants/acme-ai.json` | #10b981 (green) |

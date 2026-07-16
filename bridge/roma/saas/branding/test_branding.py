#!/usr/bin/env python
"""
saas/branding/test_branding.py
"""
import sys

sys.path.insert(0, ".")

from saas.branding import (
    BrandingService,
    branding_cache,
    load_by_tenant_id,
    load_default,
)
from saas.branding.stripe_integration import (
    build_stripe_invoice_settings,
    build_stripe_metadata,
)

passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}")
        failed += 1


print("\n=== Branding: Defaults & Cache ===")
b = load_default()
check("app_name contains VEGA", "VEGA" in b.app_name)
check("primary_color ROMA blue", b.primary_color == "#3b82f6")
check("support_email set", bool(b.support_email))
check("metadata powered_by", b.metadata.get("powered_by") == "mahaasur13-sys")

branding_cache.clear()
branding_cache.set("test", b)
cached = branding_cache.get("test")
check("cache set/get", cached is not None and cached.app_name == b.app_name)
branding_cache.clear()
check("cache clear", branding_cache.get("test") is None)

print("\n=== Branding: White-label ACME ===")
b2 = load_by_tenant_id("acme-ai")
check("ACME name", b2.app_name == "AcmeAI GPU Cloud")
check("ACME color green", b2.primary_color == "#10b981")
check("ACME domain", b2.custom_domain == "gpu.acme-ai.com")
check("ACME from_name", b2.from_name == "AcmeAI GPU Cloud")

print("\n=== Branding: Service ===")
b3 = BrandingService.get_for_request(None)
check("get_for_request(None) = default", "VEGA" in b3.app_name)
b4 = BrandingService.get_for_request("roma_sk_test")
check("get_for_request(api_key) = default", "VEGA" in b4.app_name)
b5 = BrandingService.get_for_tenant("acme-ai")
check("get_for_tenant(acme-ai)", b5.app_name == "AcmeAI GPU Cloud")
b6 = BrandingService.get_for_tenant("unknown")
check("unknown tenant → default", "VEGA" in b6.app_name)

print("\n=== Branding: Stripe Integration ===")
meta = build_stripe_metadata(b2)
check("stripe_meta brand", meta["brand"] == "acme-ai")
check("stripe_meta app_name", meta["app_name"] == "AcmeAI GPU Cloud")
check("stripe_meta powered_by", meta["powered_by"] == "mahaasur13-sys")

inv = build_stripe_invoice_settings(b2)
check("invoice custom_fields[0].name", inv["custom_fields"][0]["name"] == "Cloud Platform")
check("invoice footer", "mahaasur13-sys" in inv["footer"])

print(f"\n{'='*40}")
print(f"RESULTS: {passed} passed, {failed} failed")
if failed:
    sys.exit(1)

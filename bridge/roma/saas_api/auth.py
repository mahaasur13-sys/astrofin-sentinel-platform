"""ROMA SaaS API — Auth (API key + quota + rate limit)"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import time

from auth.api_keys import APIKeyManager
from billing.ledger import BillingLedger
from billing.pricing_engine import PricingEngine
from tenancy.manager import TenantManager


class QuotaExceeded(Exception):
    pass


class RateLimitExceeded(Exception):
    pass


_akm = APIKeyManager()
_tenant_mgr = TenantManager()
_usage = BillingLedger()
_pricing = PricingEngine()
_last_call = {}


def verify_api_key(token: str) -> dict:
    key_record = _akm.validate_key(token)
    if not key_record:
        raise ValueError("Invalid API key")
    org_id = key_record["org_id"]
    project_id = key_record.get("project_id", "default")
    tenant = _tenant_mgr.get_tenant(org_id)
    if not tenant:
        raise ValueError(f"Unknown org: {org_id}")
    gpu_seconds_used = _usage.get_usage(org_id)
    tier = tenant.get("plan", "pro")
    tier_gpu_hours = {"free": 10, "pro": 1000, "enterprise": 864000}
    limit = tier_gpu_hours.get(tier, 1000) * 3600
    if gpu_seconds_used >= limit:
        raise QuotaExceeded(f"GPU quota exceeded: {gpu_seconds_used/3600:.1f}hr used / {limit/3600:.0f}hr limit")
    window = {"free": 60, "pro": 10, "enterprise": 1}[tier]
    now = time.time()
    last = _last_call.get(org_id, 0)
    if now - last < window:
        raise RateLimitExceeded(f"Rate limited: {window}s between calls for {tier}")
    _last_call[org_id] = now
    return {"org_id": org_id, "project_id": project_id, "tier": tier}

#!/usr/bin/env python3
"""ROMA Quota Engine — Per-tenant quota tracking and enforcement."""

from typing import Dict


class QuotaEngine:
    """
    Tracks per-tenant quota usage against plan limits.
    Enforces GPU-second quotas per billing cycle.
    """

    PLAN_QUOTAS = {
        "FREE": 360_000,  # GPU-seconds / month
        "PRO": 3_600_000,
        "ENTERPRISE": 36_000_000,
    }
    PLAN_PRIORITY = {
        "FREE": 1,
        "PRO": 2,
        "ENTERPRISE": 3,
    }

    def __init__(self, metering_engine=None):
        self.metering = metering_engine
        self.usage: dict[str, float] = {}  # tenant_id → GPU-sec used
        self.cycle_start: dict[str, float] = {}  # tenant_id → cycle start

    def get_usage(self, tenant_id: str) -> float:
        return self.usage.get(tenant_id, 0.0)

    def get_limit(self, tenant_id: str, plan: str = "FREE") -> float:
        return self.PLAN_QUOTAS.get(plan, 0.0)

    def check_quota(self, tenant_id: str, requested: float, plan: str = "FREE") -> tuple[bool, str]:
        used = self.get_usage(tenant_id)
        limit = self.get_limit(tenant_id, plan)
        if used + requested > limit:
            return False, f"Quota exceeded: {used:.0f}/{limit:.0f} GPU-s"
        return True, "OK"

    def record_usage(self, tenant_id: str, gpu_seconds: float, plan: str = "FREE"):
        self.usage[tenant_id] = self.usage.get(tenant_id, 0.0) + gpu_seconds

    def estimate_cost(self, gpu_seconds: float, plan: str = "FREE") -> float:
        base_rate = 0.000222  # $ / GPU-second (from pricing_engine.py)
        plan_modifier = {"FREE": 1.0, "PRO": 0.9, "ENTERPRISE": 0.75}.get(plan, 1.0)
        return gpu_seconds * base_rate * plan_modifier

    def quota_headers(self, tenant_id: str, plan: str = "FREE") -> dict:
        used = self.get_usage(tenant_id)
        limit = self.get_limit(tenant_id, plan)
        return {
            "X-ROMA-Quota-Used": str(int(used)),
            "X-ROMA-Quota-Limit": str(int(limit)),
            "X-ROMA-Quota-Remaining": str(int(max(0, limit - used))),
        }

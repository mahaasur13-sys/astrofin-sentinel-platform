#!/usr/bin/env python3
"""ROMA Billing — Metering Engine, Usage Tracking, Cost Attribution."""

import time
from dataclasses import dataclass, field
from typing import Dict, List

# ── Unit Rates (USD per second) ────────────────────────────────────────────
GPU_RATE = 0.00001  # $0.00001 per GPU-second
CPU_RATE = 0.000001  # $0.000001 per CPU-second
RAM_RATE = 0.0000001  # $0.0000001 per GB-second


@dataclass
class UsageEvent:
    tenant_id: str
    event_type: str  # gpu_usage | cpu_usage | storage_usage | plugin_exec
    value: float  # gpu_seconds | cpu_seconds | gb_seconds | exec_count
    job_id: str
    timestamp: float = field(default_factory=time.time)
    cost_usd: float = 0.0

    def __post_init__(self):
        if self.event_type == "gpu_usage":
            self.cost_usd = self.value * GPU_RATE
        elif self.event_type == "cpu_usage":
            self.cost_usd = self.value * CPU_RATE
        elif self.event_type == "storage_usage":
            self.cost_usd = self.value * RAM_RATE
        elif self.event_type == "plugin_exec":
            self.cost_usd = self.value * 0.001


class MeteringEngine:
    def __init__(self):
        self.events: List[UsageEvent] = []
        self.tenant_totals: Dict[str, Dict[str, float]] = {}

    def record(
        self,
        event_type: str,
        tenant: str,
        job_id: str = "manual",
        gpu_seconds: float = 0,
        cpu_seconds: float = 0,
        gb_seconds: float = 0,
        plugin_count: int = 0,
    ) -> UsageEvent:
        val = gpu_seconds or cpu_seconds or gb_seconds or plugin_count
        ev = UsageEvent(
            tenant_id=tenant, event_type=event_type, value=val, job_id=job_id
        )
        self.events.append(ev)
        t = self.tenant_totals.setdefault(
            tenant, {"gpu_s": 0, "cpu_s": 0, "gb_s": 0, "cost": 0.0, "jobs": 0}
        )
        if event_type == "gpu_usage":
            t["gpu_s"] += gpu_seconds
        if event_type == "cpu_usage":
            t["cpu_s"] += cpu_seconds
        if event_type == "storage_usage":
            t["gb_s"] += gb_seconds
        if event_type == "job_completed":
            t["jobs"] += 1
        t["cost"] += ev.cost_usd
        return ev

    def snapshot(self, tenant: str = None) -> Dict:
        if tenant:
            return self.tenant_totals.get(tenant, {})
        return {
            "tenants": self.tenant_totals,
            "total_events": len(self.events),
            "total_cost": sum(t["cost"] for t in self.tenant_totals.values()),
        }


if __name__ == "__main__":
    m = MeteringEngine()
    m.record("gpu_usage", tenant="tenant-abc", gpu_seconds=120.0, job_id="roma-job-1")
    m.record("cpu_usage", tenant="tenant-abc", cpu_seconds=3600.0, job_id="roma-job-1")
    m.record(
        "storage_usage", tenant="tenant-abc", gb_seconds=86400.0, job_id="roma-job-1"
    )
    m.record("job_completed", tenant="tenant-xyz", job_id="roma-job-2")
    m.record("plugin_exec", tenant="tenant-abc", plugin_count=5, job_id="roma-job-1")
    s = m.snapshot()
    print(f"Total cost: ${s['total_cost']:.4f} across {s['total_events']} events")
    print(f"Tenant abc: ${s['tenants']['tenant-abc']['cost']:.4f}")
    print(f"Tenant xyz: ${s['tenants']['tenant-xyz']['cost']:.4f}")

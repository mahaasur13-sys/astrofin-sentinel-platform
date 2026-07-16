#!/usr/bin/env python3
"""ROMA Pricing Engine — Dynamic pricing, tier management, cost models."""
from enum import Enum


class PricingTier(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PricingEngine:
    def __init__(self):
        self.utilization = 0.5
        self.multiplier = 1.0

    def set_utilization(self, util: float):
        self.utilization = util
        self.multiplier = 1.0 + (util * 0.5)

    def calculate(self, tier: PricingTier, gpu_s: float = 0, cpu_s: float = 0, gb_s: float = 0) -> dict:
        rates = {
            PricingTier.FREE: (0.0, 0.0, 0.0),
            PricingTier.PRO: (0.005, 0.001, 0.00001),
            PricingTier.ENTERPRISE: (0.004, 0.0005, 0.000005),
        }
        gpu_rate, cpu_rate, gb_rate = rates.get(tier, rates[PricingTier.FREE])
        gpu_cost = (gpu_s / 3600) * gpu_rate * self.multiplier
        cpu_cost = (cpu_s / 3600) * cpu_rate
        gb_cost = (gb_s / 3600) * gb_rate
        return {
            "tier": tier.value,
            "gpu_cost": round(gpu_cost, 6),
            "cpu_cost": round(cpu_cost, 6),
            "storage_cost": round(gb_cost, 6),
            "total": round(gpu_cost + cpu_cost + gb_cost, 6),
            "currency": "USD",
        }

    def estimate_duration(self, task: str, gpu_type: str) -> int:
        base_map = {"RTX3060": 1800, "RTX4090": 900, "A100": 300, "H100": 150}
        base = base_map.get(gpu_type, 900)
        if any(kw in task.lower() for kw in ["yolo", "detection", "train", "fine-tune"]):
            return base * 4
        if any(kw in task.lower() for kw in ["llm", "gpt", "bert", "transformer"]):
            return base * 8
        if any(kw in task.lower() for kw in ["stable", "diffusion", "image gen"]):
            return base * 6
        return base


def estimate_cost(tenant_id: str, gpu_seconds: float, cpu_seconds: float, gb_seconds: float) -> float:
    pe = PricingEngine()
    result = pe.calculate(PricingTier.PRO, gpu_s=gpu_seconds, cpu_s=cpu_seconds, gb_s=gb_seconds)
    return result["total"]

#!/usr/bin/env python3
"""ROMA Cost Predictor — Pre-execution cost estimation engine."""
import sys

sys.path.insert(0, '/home/workspace/roma-execution-bridge')

from billing.pricing_engine import PricingEngine, PricingTier


class CostPredictor:
    """Predicts execution cost BEFORE running task."""

    def __init__(self):
        self.pricing = PricingEngine()
        self.tier_map = {"FREE": PricingTier.FREE, "PRO": PricingTier.PRO, "ENTERPRISE": PricingTier.ENTERPRISE}

    def predict(self, task: str, gpu_required: bool, plugin_type: str = "default",
                tenant_tier: str = "FREE", custom_duration: int = None) -> dict:
        tier_enum = self.tier_map.get(tenant_tier, PricingTier.FREE)

        # Оцениваем длительность (в секундах)
        if custom_duration:
            duration_sec = custom_duration
        else:
            duration_sec = self._estimate_runtime(task, plugin_type, gpu_required)

        # Расчёт стоимости через движок (gpu_s — длительность в секундах, если GPU нужен)
        gpu_seconds = duration_sec if gpu_required else 0
        cpu_seconds = duration_sec if not gpu_required else 0
        storage_sec = 0  # storage пока не учитываем, но можно передать 0

        cost = self.pricing.calculate(tier_enum, gpu_s=gpu_seconds, cpu_s=cpu_seconds, gb_s=storage_sec)
        total_cost = cost["total"]

        risk_flags = self._assess_risk(duration_sec, tenant_tier, task)

        # Определяем уровень риска для CLI
        if risk_flags:
            risk_level = "MEDIUM" if "HIGH_COMPUTE_TASK" in risk_flags else "LOW"
        else:
            risk_level = "LOW"

        # Оцениваем GPU узел и количество (заглушки)
        gpu_node = "gpu-node-1" if gpu_required else "cpu-cluster"
        gpu_count = 1 if gpu_required else 0

        return {
            "estimated_cost": round(total_cost, 4),
            "estimated_duration_minutes": round(duration_sec / 60, 1),
            "gpu_node": gpu_node,
            "gpu_count": gpu_count,
            "risk_level": risk_level,
            "currency": "USD",
            "confidence": self._confidence_score(plugin_type, duration_sec),
            "breakdown": {
                "duration_sec": duration_sec,
                "gpu_seconds": gpu_seconds,
                "cpu_seconds": cpu_seconds,
                "gpu_cost": cost["gpu_cost"],
                "cpu_cost": cost["cpu_cost"],
                "storage_cost": cost["storage_cost"],
                "tier": tier_enum.value,
                "multiplier": self.pricing.multiplier,
                "total": round(total_cost, 4),
                "plugin_type": plugin_type,
                "gpu_required": gpu_required
            },
            "risk_flags": risk_flags,
            "decision": self._decision(total_cost, tenant_tier, risk_flags)
        }

    def _estimate_runtime(self, task: str, plugin_type: str, gpu_required: bool) -> int:
        benchmarks = {"ml_training": 7200, "inference": 1800, "simulation": 3600, "data_processing": 5400, "default": 3600}
        base = benchmarks.get(plugin_type, 3600)
        if gpu_required:
            base = int(base * 1.1)
        return base

    def _assess_risk(self, duration_sec: int, tier: str, task: str) -> list:
        flags = []
        if duration_sec > 36000:
            flags.append("LONG_RUNNING_TASK")
        if tier == "FREE" and duration_sec > 3600:
            flags.append("FREE_TIER_LIMIT_RISK")
        if "yolov8" in task.lower() or "llm" in task.lower():
            flags.append("HIGH_COMPUTE_TASK")
        return flags

    def _confidence_score(self, plugin_type: str, duration_sec: int) -> float:
        base = 0.75
        if plugin_type in {"ml_training", "inference", "simulation"}:
            base += 0.15
        if 1800 <= duration_sec <= 14400:
            base += 0.10
        return min(base, 0.98)

    def _decision(self, cost: float, tier: str, risk_flags: list) -> str:
        limits = {"FREE": 1.0, "PRO": 50.0, "ENTERPRISE": 500.0}
        limit = limits.get(tier, 10.0)
        if cost > limit:
            return "REQUIRES_CONFIRMATION"
        if risk_flags and tier == "FREE":
            return "REQUIRES_CONFIRMATION"
        if cost > limit * 0.8:
            return "REQUIRES_CONFIRMATION"
        return "APPROVED"

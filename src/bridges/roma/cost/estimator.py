#!/usr/bin/env python3
"""ROMA Runtime Estimator — Plugin-aware runtime estimation based on historical data."""

import sys

sys.path.insert(0, "/home/workspace/roma-execution-bridge")


class RuntimeEstimator:
    """Predicts runtime duration for a task based on plugin type and historical events."""

    def __init__(self):
        self.benchmarks = {
            "ml_training": {"gpu_base_seconds": 7200, "variance": 0.3, "gpu_class_factor": {"RTX3060": 1.0, "A100": 0.5, "T4": 1.3}},
            "inference": {"gpu_base_seconds": 1800, "variance": 0.15, "gpu_class_factor": {"RTX3060": 1.0, "A100": 0.4, "T4": 1.2}},
            "simulation": {"gpu_base_seconds": 3600, "variance": 0.4, "gpu_class_factor": {"RTX3060": 1.0, "A100": 0.6, "T4": 1.1}},
            "data_processing": {"gpu_base_seconds": 5400, "variance": 0.25, "gpu_class_factor": {"RTX3060": 1.0, "A100": 0.5, "T4": 1.3}},
            "default": {"gpu_base_seconds": 3600, "variance": 0.5, "gpu_class_factor": {"RTX3060": 1.0, "A100": 0.5, "T4": 1.3}},
        }
        self.historical_events = self._load_historical_events()

    def _load_historical_events(self) -> list:
        try:
            from durability.event_store import EventStore

            store = EventStore()
            return store.get_all_events()
        except Exception:
            return []

    def estimate(self, plugin_type: str, gpu_class: str = "RTX3060", batch_size: int = 1, **kwargs) -> dict:
        benchmark = self.benchmarks.get(plugin_type, self.benchmarks["default"])

        # Base runtime
        base = benchmark["gpu_base_seconds"]

        # GPU class adjustment
        gpu_factor = benchmark["gpu_class_factor"].get(gpu_class, 1.0)

        # Batch size scaling (logarithmic, not linear — training batches scale differently than inference)
        batch_factor = 1.0 + (batch_size > 1) * (0.05 * (batch_size**0.5 - 1))

        # Model-specific adjustments
        model_size = kwargs.get("model_size", "medium")
        model_factor = {"small": 0.6, "medium": 1.0, "large": 2.0, "xlarge": 4.0}.get(model_size, 1.0)

        # Data size adjustment
        data_scale = kwargs.get("data_scale_gb", 10) / 10.0

        estimated_seconds = int(base * gpu_factor * batch_factor * model_factor * data_scale)

        # Historical adjustment
        if self.historical_events:
            avg = self._hist_avg(plugin_type)
            if avg:
                estimated_seconds = int(estimated_seconds * 0.7 + avg * 0.3)

        return {
            "estimated_seconds": estimated_seconds,
            "estimated_hours": round(estimated_seconds / 3600, 2),
            "variance": benchmark["variance"],
            "confidence_range": {"min_seconds": int(estimated_seconds * (1 - benchmark["variance"])), "max_seconds": int(estimated_seconds * (1 + benchmark["variance"]))},
            "factors": {"base": base, "gpu_factor": gpu_factor, "batch_factor": round(batch_factor, 3), "model_factor": model_factor, "data_scale": data_scale},
        }

    def _hist_avg(self, plugin_type: str) -> float:
        relevant = [e for e in self.historical_events if e.get("type", "").endswith(plugin_type)]
        if not relevant:
            return 0.0
        return sum(e.get("duration", 0) for e in relevant) / len(relevant)


if __name__ == "__main__":
    est = RuntimeEstimator()
    r = est.estimate("ml_training", gpu_class="RTX3060", batch_size=4, model_size="large", data_scale_gb=50)
    print(f"ML Training estimate: {r['estimated_seconds']}s ({r['estimated_hours']}h)")
    print(f"  Confidence range: {r['confidence_range']['min_seconds']}s - {r['confidence_range']['max_seconds']}s")
    print(f"  Factors: {r['factors']}")

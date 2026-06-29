"""In-process metrics for Data Room access.

Replace with prometheus_client in production.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any


class MetricsStore:
    """Thread-safe singleton. Track resolver usage + quality."""

    _instance: "MetricsStore | None" = None
    _lock = threading.Lock()

    def __init__(self):
        self.access_count: dict[str, int] = defaultdict(int)
        self.error_count: dict[str, int] = defaultdict(int)
        self.latency_sum: dict[str, float] = defaultdict(float)
        self.last_quality: dict[str, float] = {}
        self.source_breakdown: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    @classmethod
    def instance(cls) -> "MetricsStore":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def record_access(self, resolver_id: str, symbol: str) -> None:
        self.access_count[resolver_id] += 1
        self.source_breakdown[resolver_id][symbol] += 1

    def record_error(self, resolver_id: str) -> None:
        self.error_count[resolver_id] += 1

    def record_latency(self, resolver_id: str, seconds: float) -> None:
        self.latency_sum[resolver_id] += seconds

    def record_quality(self, resolver_id: str, quality: float) -> None:
        self.last_quality[resolver_id] = quality

    def record(self, resolver: str, *, latency: float = 0.0, success: bool = True, quality: float = 1.0) -> None:
        """Convenience:
        if success=True, increment access_count and source_breakdown.
        if success=False, increment error_count.
        always record latency and quality.
        """
        self.access_count[resolver] += 1
        self.source_breakdown[resolver][""] += 1
        self.error_count[resolver] += 0 if success else 1
        self.latency_sum[resolver] += latency
        self.last_quality[resolver] = quality

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_count": dict(self.access_count),
            "error_count": dict(self.error_count),
            "latency_sum": dict(self.latency_sum),
            "latency_sum_ms": {k: v * 1000 for k, v in self.latency_sum.items()},
            "last_quality": dict(self.last_quality),
            "source_breakdown": {k: dict(v) for k, v in self.source_breakdown.items()},
        }

    def reset(self) -> None:
        self.access_count.clear()
        self.error_count.clear()
        self.latency_sum.clear()
        self.last_quality.clear()
        self.source_breakdown.clear()

    def health_check(self) -> dict[str, dict]:
        """Return per-resolver health summary.

        Rule: if error_rate > 0.5 OR last_quality < 0.3, status is "degraded".
              otherwise "healthy".
        """
        out: dict[str, dict] = {}
        for resolver in set(self.access_count) | set(self.error_count):
            accesses = self.access_count.get(resolver, 0)
            errors = self.error_count.get(resolver, 0)
            total = accesses + errors
            error_rate = (errors / total) if total > 0 else 0.0
            quality = self.last_quality.get(resolver, 1.0)
            status = "degraded" if (error_rate > 0.5 or quality < 0.3) else "healthy"
            out[resolver] = {
                "accesses": accesses,
                "errors": errors,
                "error_rate": error_rate,
                "last_quality": quality,
                "status": status,
            }
        return out


__all__ = ["MetricsStore"]

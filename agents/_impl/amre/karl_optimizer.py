"""amre/karl_optimizer.py - ATOM-021: KARL Optimization & Parallelism"""

from __future__ import annotations

"""Optimizations for KARL loop: parallel processing, TTC depth, reduced overhead."""

import asyncio
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class KARLPerfProfile:
    """Performance profile for KARL operations."""

    uncertainty_ms: float = 0.0
    grounding_ms: float = 0.0
    reward_ms: float = 0.0
    oap_ms: float = 0.0
    audit_ms: float = 0.0
    total_ms: float = 0.0

    @property
    def overhead_pct(self) -> float:
        base = self.total_ms - self.overhead_ms
        return (self.overhead_ms / base * 100) if base > 0 else 0

    @property
    def overhead_ms(self) -> float:
        return self.uncertainty_ms + self.grounding_ms + self.reward_ms + self.oap_ms + self.audit_ms


class AsyncPipeline:
    """Async pipeline for parallel KARL operations."""

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[Any, float]] = {}  # key -> (result, timestamp)
        self._cache_ttl = 60.0  # seconds

    def _get_cached(self, key: str) -> Any | None:
        with self._lock:
            if key in self._cache:
                result, ts = self._cache[key]
                if time.time() - ts < self._cache_ttl:
                    return result
                del self._cache[key]
        return None

    def _set_cached(self, key: str, result: Any):
        with self._lock:
            self._cache[key] = (result, time.time())

    async def run_parallel(
        self,
        uncertainty_fn: Callable,
        grounding_fn: Callable,
        reward_fn: Callable,
        cache_key: str | None = None,
    ) -> dict[str, Any]:
        """Run uncertainty, grounding, reward in parallel."""
        # Check cache
        if cache_key:
            cached = self._get_cached(cache_key)
            if cached:
                return cached

        t0 = time.perf_counter()

        # Run in parallel
        results = await asyncio.gather(
            asyncio.to_thread(uncertainty_fn),
            asyncio.to_thread(grounding_fn),
            asyncio.to_thread(reward_fn),
        )

        elapsed = (time.perf_counter() - t0) * 1000

        result = {
            "uncertainty": results[0],
            "grounding": results[1],
            "reward": results[2],
            "elapsed_ms": elapsed,
        }

        if cache_key:
            self._set_cached(cache_key, result)

        return result

    def clear_cache(self):
        with self._lock:
            self._cache.clear()


# Global optimizer instance
_KARL_OPTIMIZER: Optional["KARLOptimizer"] = None


class KARLOptimizer:
    """Main optimizer for KARL loop performance."""

    def __init__(self):
        self.pipeline = AsyncPipeline()
        self.ttc_depth = 3
        self.exploration_rate = 0.1
        self._perf_history: list[KARLPerfProfile] = []

    def adjust_ttc_depth(self, entropy: float, oos_fail_rate: float) -> int:
        """Dynamically adjust TTC (Time To Commit) depth based on conditions."""
        base_depth = 3

        # Increase depth when uncertain (explore more)
        if entropy > 0.6:
            base_depth += 1
        elif entropy < 0.3:
            base_depth = max(1, base_depth - 1)

        # Decrease depth when failing often (cut losses)
        if oos_fail_rate > 0.4:
            base_depth = max(1, base_depth - 1)

        # Decrease depth when very confident
        # (don't overthink when sure)

        self.ttc_depth = base_depth
        return base_depth

    def adjust_exploration(self, reward_trend: float) -> float:
        """Adjust exploration rate based on reward trend."""
        base_rate = 0.1

        # Increase exploration when reward is declining
        if reward_trend < -0.05:
            base_rate = min(0.25, base_rate * 1.5)
        elif reward_trend > 0.05:
            # Exploit more when winning
            base_rate = max(0.02, base_rate * 0.8)

        self.exploration_rate = base_rate
        return base_rate

    def record_perf(self, profile: KARLPerfProfile):
        """Record performance profile for analysis."""
        self._perf_history.append(profile)
        if len(self._perf_history) > 100:
            self._perf_history.pop(0)

    def get_avg_overhead(self) -> float:
        """Get average overhead percentage."""
        if not self._perf_history:
            return 0.0
        return sum(p.overhead_pct for p in self._perf_history) / len(self._perf_history)

    def get_optimization_report(self) -> dict[str, Any]:
        """Get current optimization report."""
        if not self._perf_history:
            return {"status": "no_data"}

        recent = self._perf_history[-10:]
        return {
            "ttc_depth": self.ttc_depth,
            "exploration_rate": self.exploration_rate,
            "avg_overhead_pct": sum(p.overhead_pct for p in recent) / len(recent),
            "avg_total_ms": sum(p.total_ms for p in recent) / len(recent),
            "samples": len(recent),
        }


def get_karl_optimizer() -> KARLOptimizer:
    """Get or create global KARLOptimizer instance."""
    global _KARL_OPTIMIZER
    if _KARL_OPTIMIZER is None:
        _KARL_OPTIMIZER = KARLOptimizer()
    return _KARL_OPTIMIZER

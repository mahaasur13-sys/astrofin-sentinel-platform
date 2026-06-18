from __future__ import annotations

from mas_factory.registry import get_agent_runner  # F821 fix

"""mas_factory/engine.py — ATOM-R-033: Production Optimized MAS Factory Engine
Optimizations:
- LRU cache for Architect.build()
- Parallel agent execution
- Robust error handling with fallback
- Meta-questioning as topology change driver
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any

from mas_factory.architect import MASFactoryArchitect
from mas_factory.registry import AgentRegistry, get_registry
from mas_factory.topology import Role, Topology

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    duration_ms: float
    nodes_executed: int
    errors: int
    cache_hit: bool


@dataclass
class MASFactoryConfig:
    enable_caching: bool = True
    max_workers: int = 4
    timeout_seconds: float = 30.0
    fallback_on_error: bool = True
    enable_meta_questioning: bool = True


class ProductionMASEngine:
    def __init__(
        self,
        config: MASFactoryConfig | None = None,
        registry: AgentRegistry | None = None,
    ):
        self.config = config or MASFactoryConfig()
        self.registry = registry or get_registry()
        self._architect = MASFactoryArchitect()
        self._topology_cache: dict[str, Topology] = {}
        self._metrics: list[ExecutionMetrics] = []
        self._meta_questions_asked: int = 0

    def _compute_cache_key(self, context: dict[str, Any]) -> str:
        intention = context.get("intention", context.get("query_type", "ANALYZE"))
        symbol = context.get("symbol", "BTCUSDT")
        timeframe = context.get("timeframe", "SWING")
        data = f"{intention}:{symbol}:{timeframe}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    @lru_cache(maxsize=32)
    def _build_cached(self, cache_key: str, intention: str, symbol: str, timeframe: str) -> Topology | None:
        try:
            return self._architect.build(intention=intention, symbol=symbol, timeframe=timeframe)
        except Exception as e:
            logger.warning(f"Architect.build failed: {e}")
            return None

    def build_topology(self, context: dict[str, Any]) -> Topology | None:
        if not self.config.enable_caching:
            return self._architect.build(
                intention=context.get("intention", context.get("query_type", "ANALYZE")),
                symbol=context.get("symbol", "BTCUSDT"),
                timeframe=context.get("timeframe", "SWING"),
            )

        cache_key = self._compute_cache_key(context)
        if cache_key in self._topology_cache:
            return self._topology_cache[cache_key]

        topology = self._build_cached(
            cache_key,
            context.get("intention", context.get("query_type", "ANALYZE")),
            context.get("symbol", "BTCUSDT"),
            context.get("timeframe", "SWING"),
        )

        if topology:
            self._topology_cache[cache_key] = topology
        return topology

    async def execute_async(self, context: dict[str, Any]) -> dict[str, Any]:
        t0 = time.time()
        errors = 0
        cache_hit = False

        try:
            topology = self.build_topology(context)
            if not topology:
                return self._error_response("Topology build failed", t0, 0, 1)

            cache_key = self._compute_cache_key(context)
            cache_hit = cache_key in self._topology_cache

            if self.config.enable_meta_questioning:
                context = await self._apply_meta_questioning(context, topology)

            result = await self._execute_topology_async(topology, context)

            duration_ms = (time.time() - t0) * 1000
            metrics = ExecutionMetrics(
                duration_ms=duration_ms,
                nodes_executed=len(topology.roles),
                errors=errors,
                cache_hit=cache_hit,
            )
            self._metrics.append(metrics)

            return {
                "status": "success",
                "topology_hash": topology.hash[:8] if hasattr(topology, "hash") else "unknown",
                "result": result,
                "metrics": {
                    "duration_ms": round(duration_ms, 2),
                    "nodes_executed": metrics.nodes_executed,
                    "cache_hit": cache_hit,
                    "errors": errors,
                },
            }

        except Exception as e:
            logger.error(f"Execute failed: {e}")
            if self.config.fallback_on_error:
                return await self._execute_fallback(context)
            return self._error_response(str(e), t0, 0, 1)

    async def _execute_topology_async(self, topology: Topology, context: dict[str, Any]) -> dict[str, Any]:
        results = {}

        errors = 0  # F821 fix

        async def run_role(role: Role) -> tuple:
            try:
                runner = get_agent_runner(role.agent_type)
                if asyncio.iscoroutinefunction(runner.run):
                    r = await runner.run(context)
                else:
                    r = runner.run(context)
                return role.name, r, None
            except Exception as e:
                return role.name, None, str(e)

        tasks = [run_role(r) for r in topology.roles]
        role_results = await asyncio.gather(*tasks, return_exceptions=True)

        for item in role_results:
            if isinstance(item, tuple):
                name, result, error = item
                results[name] = result
                if error:
                    logger.warning(f"Role {name} error: {error}")
            else:
                errors += 1

        return {
            "signals": results,
            "signal_count": len([r for r in results.values() if r]),
            "timestamp": datetime.now().isoformat(),
        }

    async def _apply_meta_questioning(self, context: dict[str, Any], topology: Topology) -> dict[str, Any]:
        try:
            from agents._impl.meta_questioning import MetaQuestioningEngine

            meta = MetaQuestioningEngine()

            signals = context.get("signals", {})
            context.get("uncertainty", {})

            analysis = meta.analyze(signals=signals, context=context)

            if analysis.get("bias_detected"):
                self._meta_questions_asked += 1
                context["_meta_warning"] = analysis.get("top_question", "")

            return context
        except Exception as e:
            logger.debug(f"Meta-questioning skipped: {e}")
            return context

    async def _execute_fallback(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "fallback",
            "reason": "MAS engine error, using simple synthesis",
            "result": {
                "signal": "NEUTRAL",
                "confidence": 50,
                "reasoning": "MAS Factory fallback - enable detailed logging for diagnosis",
            },
            "metrics": {"duration_ms": 0, "cache_hit": False, "errors": 1},
        }

    def _error_response(self, error: str, t0: float, nodes: int, errs: int) -> dict[str, Any]:
        return {
            "status": "error",
            "error": error,
            "metrics": {
                "duration_ms": round((time.time() - t0) * 1000, 2),
                "nodes_executed": nodes,
                "cache_hit": False,
                "errors": errs,
            },
        }

    def run_sync(self, context: dict[str, Any]) -> dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.execute_async(context))

    def get_metrics_summary(self) -> dict[str, Any]:
        if not self._metrics:
            return {"total_runs": 0, "avg_duration_ms": 0, "cache_hit_rate": 0}

        total = len(self._metrics)
        avg_ms = sum(m.duration_ms for m in self._metrics) / total
        cache_hits = sum(1 for m in self._metrics if m.cache_hit)

        return {
            "total_runs": total,
            "avg_duration_ms": round(avg_ms, 2),
            "cache_hit_rate": round(cache_hits / total, 3),
            "total_errors": sum(m.errors for m in self._metrics),
            "meta_questions_asked": self._meta_questions_asked,
        }

    def clear_cache(self):
        self._topology_cache.clear()
        try:
            self._build_cached.cache_clear()
        except Exception:
            pass


def get_production_engine() -> ProductionMASEngine:
    return ProductionMASEngine()


# Alias for backward compatibility
TopologyExecutor = ProductionMASEngine

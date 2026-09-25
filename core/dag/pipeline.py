"""DAG pipeline — topological execution engine with observability."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

from core.dag.context import DAGContext, NodeResult
from core.dag.node import DAGNode
from core.dag.observability import (
    observe_pipeline,
    record_pipeline_run,
)
from core.dag.alternate_routes import (
    RouteCatalog,
    RouteStrategy,
    TriggerReason,
    get_route_catalog,
)

logger = logging.getLogger(__name__)


@dataclass
class _NodeMeta:
    node: DAGNode
    depends_on: list[str]
    level: int = 0


def _apply_alternate_route_if_needed(
    pipeline: "DAGPipeline",
    result: NodeResult,
    meta: _NodeMeta,
    ctx: DAGContext,
    level_idx: int,
) -> None:
    """
    Проверить, нужно ли активировать альтернативный маршрут при сбое узла.

    Если NodeResult.error != None, ищем в RouteCatalog подходящий маршрут
    и применяем: skip (добавить None-результат), delegate (запустить делегата),
    cache_fallback (подставить кэшированный результат).
    """
    if result.ok:
        return

    error_str = result.error or ""
    nid = meta.node.node_id

    # Map error string to TriggerReason
    if "timeout" in error_str.lower():
        trigger = TriggerReason.TIMEOUT
    elif "circuit" in error_str.lower():
        trigger = TriggerReason.CIRCUIT_OPEN
    elif "429" in error_str:
        trigger = TriggerReason.EXTERNAL_429
    elif "5" in error_str and "5" in error_str.split(":")[0][-3:]:
        trigger = TriggerReason.EXTERNAL_5XX
    elif "provider" in error_str.lower() or "connect" in error_str.lower():
        trigger = TriggerReason.PROVIDER_ERROR
    elif "max retries" in error_str.lower():
        trigger = TriggerReason.MAX_RETRIES
    else:
        trigger = TriggerReason.MAX_RETRIES

    route = pipeline._route_catalog.resolve(nid, trigger)
    if route is None:
        return

    if route.strategy == RouteStrategy.SKIP:
        result.error = f"[ALT_ROUTE:skip] {error_str}"
        result.output = {"skipped": True, "reason": str(trigger.value)}
        logger.info(
            "[AltRoute] %s: SKIP (trigger=%s) — DAG continues",
            nid, trigger.value,
        )

    elif route.strategy == RouteStrategy.DELEGATE and route.delegate_to:
        if route.delegate_to in pipeline._nodes:
            logger.info(
                "[AltRoute] %s: DELEGATE → %s (trigger=%s)",
                nid, route.delegate_to, trigger.value,
            )
            from core.dag.node import DAGNode
            import asyncio as _asyncio
            try:
                delegate_node = pipeline._nodes[route.delegate_to].node
                delegate_result = _asyncio.get_event_loop().run_until_complete(
                    delegate_node.execute(ctx)
                ) if not _asyncio.get_event_loop().is_running() else None
                if delegate_result is not None:
                    result.output = delegate_result.output
                    result.duration_ms += delegate_result.duration_ms
                    result.error = None
                    pipeline._route_catalog._routes.setdefault(nid, []).clear()
            except Exception:
                pass

    elif route.strategy == RouteStrategy.CACHE_FALLBACK:
        cached_key = f"_cache_{nid}"
        cached = ctx.state.get(cached_key)
        if cached:
            result.output = cached
            result.error = f"[ALT_ROUTE:cache] {error_str}"
            logger.info(
                "[AltRoute] %s: CACHE_FALLBACK — using previous result",
                nid,
            )

    elif route.strategy == RouteStrategy.RETRY_PARAMS:
        alt_provider = route.retry_kwargs.get("provider", "")
        if alt_provider:
            logger.info(
                "[AltRoute] %s: RETRY_PARAMS provider=%s (trigger=%s)",
                nid, alt_provider, trigger.value,
            )
            result.error = f"[ALT_ROUTE:retry_{alt_provider}] {error_str}"


class DAGPipeline:
    """
    DAG-пайплайн, исполняющий узлы параллельно по уровням.

    Узлы группируются в уровни (level = max(dep.level) + 1), затем
    каждый уровень исполняется через asyncio.gather.
    Автоматически инструментирован OTEL + Prometheus.
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self._nodes: dict[str, _NodeMeta] = {}
        self._run_count: int = 0
        self._route_catalog: RouteCatalog = get_route_catalog()

    def add_node(
        self,
        node: DAGNode,
        depends_on: Optional[list[str]] = None,
    ) -> "DAGPipeline":
        """
        Добавить узел в пайплайн.

        Args:
            node: экземпляр DAGNode
            depends_on: список node_id узлов, от которых зависит этот

        Returns:
            self (fluent interface)
        """
        self._nodes[node.node_id] = _NodeMeta(
            node=node,
            depends_on=list(depends_on or []),
        )
        return self

    def _compute_levels(self) -> None:
        """Вычислить уровни для всех узлов (topological sort)."""
        visited: set[str] = set()
        resolving: set[str] = set()

        def _dfs(nid: str) -> int:
            if nid in resolving:
                raise RuntimeError(
                    f"Cycle detected in DAG pipeline '{self.name}': "
                    f"node '{nid}' depends on itself transitively"
                )
            if nid in visited:
                return self._nodes[nid].level
            resolving.add(nid)
            meta = self._nodes[nid]
            if not meta.depends_on:
                meta.level = 0
            else:
                max_dep = 0
                for dep_id in meta.depends_on:
                    if dep_id not in self._nodes:
                        raise RuntimeError(
                            f"Node '{nid}' depends on unknown node '{dep_id}'"
                        )
                    dep_level = _dfs(dep_id)
                    max_dep = max(max_dep, dep_level)
                meta.level = max_dep + 1
            visited.add(nid)
            resolving.discard(nid)
            return meta.level

        for nid in self._nodes:
            _dfs(nid)

    def _nodes_by_level(self) -> dict[int, list[_NodeMeta]]:
        """Сгруппировать узлы по уровням."""
        levels: dict[int, list[_NodeMeta]] = {}
        for meta in self._nodes.values():
            levels.setdefault(meta.level, []).append(meta)
        return levels

    async def run(self, **initial_state: Any) -> DAGContext:
        """
        Выполнить весь DAG-пайплайн с OTEL-трассировкой и Prometheus-метриками.

        Args:
            **initial_state: начальные значения для ctx.state

        Returns:
            DAGContext с результатами всех узлов
        """
        self._compute_levels()
        levels = self._nodes_by_level()
        max_level = max(levels.keys())

        node_level_map = {meta.node.node_id: meta.level for meta in self._nodes.values()}
        run_t0 = time.time()

        async with observe_pipeline(
            self.name,
            node_count=len(self._nodes),
            max_level=max_level,
            run_number=self._run_count + 1,
        ) as obs:
            trace_id = obs.get("trace_id", "")

            ctx = DAGContext(state={
                **dict(initial_state),
                "_pipeline_name": self.name,
                "_trace_id": trace_id,
                "_node_levels": node_level_map,
            })
            self._run_count += 1

            logger.info(
                "DAG '%s' starting run #%d (%d nodes, %d levels, trace=%s)",
                self.name,
                self._run_count,
                len(self._nodes),
                max_level + 1,
                trace_id,
            )

            for level_idx in range(max_level + 1):
                level_nodes = levels.get(level_idx, [])
                if not level_nodes:
                    continue

                logger.debug(
                    "DAG '%s' level %d: %d nodes",
                    self.name,
                    level_idx,
                    len(level_nodes),
                )

                tasks = []
                for meta in level_nodes:
                    if meta.node.fallback_node_id and meta.depends_on:
                        dep_failed = any(
                            ctx.get(dep_id) and not ctx.get(dep_id).ok
                            for dep_id in meta.depends_on
                        )
                        if dep_failed:
                            fallback_id = meta.node.fallback_node_id
                            if fallback_id in self._nodes:
                                logger.info(
                                    "Node '%s': dependents failed, delegating to fallback '%s'",
                                    meta.node.node_id,
                                    fallback_id,
                                )
                                tasks.append(
                                    self._nodes[fallback_id].node.execute(ctx)
                                )
                                continue

                    tasks.append(meta.node.execute(ctx))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for meta, result in zip(level_nodes, results):
                    if isinstance(result, NodeResult):
                        _apply_alternate_route_if_needed(
                            self, result, meta, ctx, level_idx,
                        )
                        ctx.set(meta.node.node_id, result)
                    elif isinstance(result, BaseException):
                        nr = NodeResult(
                            node_id=meta.node.node_id,
                            output=None,
                            duration_ms=0,
                            error=f"{type(result).__name__}: {result}",
                        )
                        _apply_alternate_route_if_needed(
                            self, nr, meta, ctx, level_idx,
                        )
                        ctx.set(meta.node.node_id, nr)
                        logger.error(
                            "DAG node '%s' unhandled exception: %s",
                            meta.node.node_id,
                            result,
                        )

        elapsed = ctx.elapsed_ms
        ok_count = sum(1 for r in ctx.results.values() if r.ok)
        fail_count = len(ctx.results) - ok_count
        status = "success" if fail_count == 0 else "partial_failure"
        record_pipeline_run(self.name, status, elapsed / 1000)

        logger.info(
            "DAG '%s' run #%d completed in %.0fms: %d/%d nodes OK",
            self.name,
            self._run_count,
            elapsed,
            ok_count,
            len(ctx.results),
        )

        return ctx

    def get_node(self, node_id: str) -> Optional[DAGNode]:
        meta = self._nodes.get(node_id)
        return meta.node if meta else None

    def node_ids(self) -> list[str]:
        return list(self._nodes.keys())

    def describe(self) -> str:
        """Человекочитаемое описание топологии пайплайна."""
        self._compute_levels()
        levels = self._nodes_by_level()
        lines = [f"DAG '{self.name}' — {len(self._nodes)} nodes:"]
        for level in sorted(levels):
            nids = [m.node.node_id for m in levels[level]]
            deps = {m.node.node_id: m.depends_on for m in levels[level]}
            lines.append(f"  Level {level}: {', '.join(nids)}")
            for nid in nids:
                if deps[nid]:
                    lines.append(
                        f"    {nid} ← depends on: {', '.join(deps[nid])}"
                    )
        return "\n".join(lines)

    @property
    def execution_plan(self) -> dict[str, list[str]]:
        """Вернуть план исполнения: {level: [node_ids]}."""
        self._compute_levels()
        levels = self._nodes_by_level()
        return {
            f"level_{lvl}": [m.node.node_id for m in nodes]
            for lvl, nodes in sorted(levels.items())
        }

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

logger = logging.getLogger(__name__)


@dataclass
class _NodeMeta:
    node: DAGNode
    depends_on: list[str]
    level: int = 0


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
                        ctx.set(meta.node.node_id, result)
                    elif isinstance(result, BaseException):
                        nr = NodeResult(
                            node_id=meta.node.node_id,
                            output=None,
                            duration_ms=0,
                            error=f"{type(result).__name__}: {result}",
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

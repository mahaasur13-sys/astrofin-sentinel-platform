"""
AstroFin Sentinel V5 — Topology Registry (P2: Sprint G)

Версионированный реестр DAG-топологий для разных стратегий и версий.
Каждая топология — замороженный граф со списком узлов и зависимостями.

Топологии:
  - swing_v1    — полный 11-узловой, 5-уровневый (текущая production)
  - intraday_v1 — 8-узловой, с акцентом на Technical + Macro
  - scalp_v1    — 6-узловой, минимальный (только Price + Technical + RAG)
  - light_v1    — облегчённый 6-узловой (текущий --light)

Usage:
    from core.dag.topology_registry import TopologyRegistry, get_topology_registry

    reg = get_topology_registry()
    topo = reg.load("swing_v1")
    dag = topo.build_pipeline()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from prometheus_client import Counter

logger = logging.getLogger(__name__)

_TOPO_LOAD_TOTAL = Counter(
    "dag_topology_load_total",
    "Total topology loads",
    ["topology_id"],
)


@dataclass
class NodeSpec:
    """Спецификация одного узла в топологии."""

    node_id: str
    class_name: str
    depends_on: list[str] = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)


@dataclass
class TopologyDefinition:
    """
    Версионированное определение DAG-топологии.

    Attributes:
        topology_id: уникальный идентификатор (напр. "swing_v1")
        strategy: торговая стратегия (SWING, INTRADAY, SCALP)
        version: семантическая версия
        nodes: список NodeSpec в порядке регистрации
    """

    topology_id: str
    strategy: str
    version: str = "1.0.0"
    description: str = ""
    nodes: list[NodeSpec] = field(default_factory=list)

    def build_pipeline(self) -> "DAGPipeline":  # type: ignore[valid-type]
        """
        Собрать DAGPipeline из спецификации узлов.

        Returns:
            DAGPipeline с зарегистрированными узлами
        """
        from core.dag.pipeline import DAGPipeline
        from orchestration.dag_nodes import NODE_CLASS_MAP

        dag = DAGPipeline(self.topology_id)
        _TOPO_LOAD_TOTAL.labels(topology_id=self.topology_id).inc()

        for spec in self.nodes:
            node_cls = NODE_CLASS_MAP.get(spec.class_name)
            if node_cls is None:
                logger.error(
                    "[TopologyRegistry] unknown class '%s' in topology '%s'",
                    spec.class_name, self.topology_id,
                )
                continue
            node = node_cls(**spec.kwargs) if spec.kwargs else node_cls()
            dag.add_node(node, depends_on=spec.depends_on if spec.depends_on else None)

        logger.info(
            "[TopologyRegistry] built pipeline '%s': %d nodes, strategy=%s",
            self.topology_id, len(dag.node_ids()), self.strategy,
        )
        return dag


# ── Topology Definitions ──────────────────────────────────────────────

TOPOLOGIES: list[TopologyDefinition] = [
    TopologyDefinition(
        topology_id="swing_v1",
        strategy="SWING",
        version="1.0.0",
        description="Полный 11-узловой DAG (production)",
        nodes=[
            NodeSpec("RouterNode", "RouterNode", depends_on=[]),
            NodeSpec("PriceNode", "PriceNode", depends_on=[]),
            NodeSpec("RAGNode", "RAGNode", depends_on=[]),
            NodeSpec("TechnicalFlowNode", "TechnicalFlowNode", depends_on=["RouterNode", "PriceNode"]),
            NodeSpec("MacroFlowNode", "MacroFlowNode", depends_on=["RouterNode", "PriceNode"]),
            NodeSpec("AstroFlowNode", "AstroFlowNode", depends_on=["RouterNode", "PriceNode"]),
            NodeSpec("ElectoralFlowNode", "ElectoralFlowNode", depends_on=["RouterNode", "PriceNode"]),
            NodeSpec("SynthesisNode", "SynthesisNode", depends_on=[
                "TechnicalFlowNode", "MacroFlowNode", "AstroFlowNode", "ElectoralFlowNode", "RAGNode",
            ]),
            NodeSpec("KARLPostProcessNode", "KARLPostProcessNode", depends_on=["SynthesisNode"]),
            NodeSpec("PersistNode", "PersistNode", depends_on=["KARLPostProcessNode"]),
            NodeSpec("AlertNode", "AlertNode", depends_on=["PersistNode"]),
        ],
    ),
    TopologyDefinition(
        topology_id="intraday_v1",
        strategy="INTRADAY",
        version="1.0.0",
        description="8-узловой DAG для внутридневной торговли (Technical + Macro focus)",
        nodes=[
            NodeSpec("RouterNode", "RouterNode", depends_on=[]),
            NodeSpec("PriceNode", "PriceNode", depends_on=[]),
            NodeSpec("RAGNode", "RAGNode", depends_on=[]),
            NodeSpec("TechnicalFlowNode", "TechnicalFlowNode", depends_on=["RouterNode", "PriceNode"]),
            NodeSpec("MacroFlowNode", "MacroFlowNode", depends_on=["RouterNode", "PriceNode"]),
            NodeSpec("SynthesisNode", "SynthesisNode", depends_on=[
                "TechnicalFlowNode", "MacroFlowNode", "RAGNode",
            ]),
            NodeSpec("PersistNode", "PersistNode", depends_on=["SynthesisNode"]),
            NodeSpec("AlertNode", "AlertNode", depends_on=["PersistNode"]),
        ],
    ),
    TopologyDefinition(
        topology_id="scalp_v1",
        strategy="SCALP",
        version="1.0.0",
        description="6-узловой минимальный DAG для скальпинга (Price + Technical + RAG only)",
        nodes=[
            NodeSpec("RouterNode", "RouterNode", depends_on=[]),
            NodeSpec("PriceNode", "PriceNode", depends_on=[]),
            NodeSpec("RAGNode", "RAGNode", depends_on=[]),
            NodeSpec("TechnicalFlowNode", "TechnicalFlowNode", depends_on=["RouterNode", "PriceNode"]),
            NodeSpec("SynthesisNode", "SynthesisNode", depends_on=["TechnicalFlowNode", "RAGNode"]),
            NodeSpec("PersistNode", "PersistNode", depends_on=["SynthesisNode"]),
        ],
    ),
    TopologyDefinition(
        topology_id="light_v1",
        strategy="LIGHT",
        version="1.0.0",
        description="Облегчённый 6-узловой (аналог --light)",
        nodes=[
            NodeSpec("RouterNode", "RouterNode", depends_on=[]),
            NodeSpec("PriceNode", "PriceNode", depends_on=[]),
            NodeSpec("RAGNode", "RAGNode", depends_on=[]),
            NodeSpec("MacroFlowNode", "MacroFlowNode", depends_on=["RouterNode", "PriceNode"]),
            NodeSpec("SynthesisNode", "SynthesisNode", depends_on=["MacroFlowNode", "RAGNode"]),
            NodeSpec("PersistNode", "PersistNode", depends_on=["SynthesisNode"]),
        ],
    ),
]


class TopologyRegistry:
    """Реестр версионированных DAG-топологий."""

    def __init__(self) -> None:
        self._topologies: dict[str, TopologyDefinition] = {}
        for t in TOPOLOGIES:
            self._topologies[t.topology_id] = t

    def register(self, topology: TopologyDefinition) -> None:
        """Зарегистрировать новую топологию."""
        self._topologies[topology.topology_id] = topology
        logger.info(
            "[TopologyRegistry] registered '%s' (v%s, strategy=%s)",
            topology.topology_id, topology.version, topology.strategy,
        )

    def load(self, topology_id: str) -> TopologyDefinition:
        """
        Загрузить топологию по идентификатору.

        Raises:
            KeyError: если топология не найдена
        """
        if topology_id not in self._topologies:
            available = ", ".join(self._topologies.keys())
            raise KeyError(
                f"Topology '{topology_id}' not found. Available: {available}"
            )
        return self._topologies[topology_id]

    def list_by_strategy(self, strategy: str) -> list[TopologyDefinition]:
        """Получить все топологии для заданной стратегии."""
        return [
            t for t in self._topologies.values()
            if t.strategy.upper() == strategy.upper()
        ]

    def latest(self, strategy: str) -> Optional[TopologyDefinition]:
        """Получить последнюю версию топологии для стратегии."""
        matches = self.list_by_strategy(strategy)
        if not matches:
            return None
        return sorted(matches, key=lambda t: t.version, reverse=True)[0]

    @property
    def list_all(self) -> list[str]:
        """Список всех зарегистрированных topology_id."""
        return sorted(self._topologies.keys())

    @property
    def stats(self) -> dict:
        return {
            "total_topologies": len(self._topologies),
            "per_strategy": {
                s: len(self.list_by_strategy(s))
                for s in {"SWING", "INTRADAY", "SCALP", "LIGHT"}
            },
        }


_global_registry: Optional[TopologyRegistry] = None


def get_topology_registry() -> TopologyRegistry:
    """Получить глобальный singleton реестра топологий."""
    global _global_registry
    if _global_registry is None:
        _global_registry = TopologyRegistry()
    return _global_registry

"""
AstroFin Sentinel V5 — Dynamic Routing (P2: Sprint G)

Заменяет фиксированные depends_on на relevance-based связывание узлов DAG.
Использует SharedEmbeddingSpace для определения того, какие агенты релевантны
данному запросу, а не жёстко закодированный список.

Modes:
  - FIXED:      текущее поведение (depends_on из build_analysis_dag)
  - RELEVANCE:  выбирает узлы по cosine similarity > threshold
  - ENSEMBLE:   комбинация FIXED + RELEVANCE (базовые узлы всегда, flow-ы по релевантности)

Usage:
    from core.dag.dynamic_routing import DynamicRoutingPolicy, RouteMode

    policy = DynamicRoutingPolicy(mode=RouteMode.RELEVANCE, threshold=0.6)
    active_nodes = policy.resolve(query, available_nodes)
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

from prometheus_client import Counter

logger = logging.getLogger(__name__)

_DYN_ROUTE_DECISIONS = Counter(
    "dag_dynamic_routing_decisions_total",
    "Total dynamic routing decisions",
    ["mode", "decision"],
)


class RouteMode(str, Enum):
    """Режим динамического связывания."""

    FIXED = "fixed"           # Жёсткая топология (depends_on)
    RELEVANCE = "relevance"   # Только по релевантности (shared embedding)
    ENSEMBLE = "ensemble"     # Гибрид: обязательные узлы всегда + flow-ы по релевантности


# Обязательные узлы, которые ВСЕГДА исполняются (независимо от режима)
CORE_NODES = {"RouterNode", "PriceNode", "RAGNode", "SynthesisNode", "PersistNode", "AlertNode"}

# Flow-узлы, которые могут быть опциональными в RELEVANCE/ENSEMBLE
FLOW_NODES = {
    "TechnicalFlowNode",
    "MacroFlowNode",
    "AstroFlowNode",
    "ElectoralFlowNode",
    "KARLPostProcessNode",
}


class DynamicRoutingPolicy:
    """
    Политика динамического связывания узлов DAG.

    Определяет, какие flow-узлы активны для данного запроса.
    """

    def __init__(
        self,
        mode: RouteMode = RouteMode.FIXED,
        threshold: float = 0.6,
        min_active_flows: int = 1,
        max_active_flows: int = 4,
    ) -> None:
        self.mode = mode
        self.threshold = threshold
        self.min_active_flows = min_active_flows
        self.max_active_flows = max_active_flows

    def resolve(
        self,
        query: str,
        available_nodes: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Определить список активных flow-узлов для запроса.

        Args:
            query: пользовательский запрос
            available_nodes: полный список доступных узлов (если None — все FLOW_NODES)

        Returns:
            Список node_id активных flow-узлов
        """
        if self.mode == RouteMode.FIXED:
            _DYN_ROUTE_DECISIONS.labels(mode="fixed", decision="all_flows").inc()
            return sorted(available_nodes or FLOW_NODES)

        flows = list(available_nodes) if available_nodes else sorted(FLOW_NODES)

        if self.mode == RouteMode.RELEVANCE:
            relevant = self._relevance_filter(query, flows)
            _DYN_ROUTE_DECISIONS.labels(
                mode="relevance",
                decision=f"{len(relevant)}_of_{len(flows)}",
            ).inc()
            return relevant

        if self.mode == RouteMode.ENSEMBLE:
            relevant = set(self._relevance_filter(query, flows, threshold=self.threshold * 0.8))
            relevant.update(flows[: self.min_active_flows])
            result = sorted(relevant)[: self.max_active_flows]
            _DYN_ROUTE_DECISIONS.labels(
                mode="ensemble",
                decision=f"{len(result)}_of_{len(flows)}",
            ).inc()
            return result

        _DYN_ROUTE_DECISIONS.labels(mode="unknown", decision="fallback_all").inc()
        return sorted(flows)

    def _relevance_filter(
        self,
        query: str,
        candidates: list[str],
        threshold: Optional[float] = None,
    ) -> list[str]:
        """
        Фильтрация flow-узлов по релевантности запросу.

        Использует SharedEmbeddingSpace.query() для поиска наиболее
        близких агентов.
        """
        thresh = threshold if threshold is not None else self.threshold
        if thresh <= 0.0 or not candidates:
            return sorted(candidates)

        try:
            from core.dag.shared_embedding import get_shared_embedding

            ses = get_shared_embedding()
            if ses is None or ses.size == 0:
                logger.debug("[DynamicRoute] shared embedding empty — activating all flows")
                return sorted(candidates)

            results = ses.query(query, k=min(len(candidates), 5), min_confidence=thresh)

            active = []
            for agent_id, score in results:
                if score >= thresh and agent_id in candidates:
                    active.append(agent_id)

            logger.info(
                "[DynamicRoute] relevance filter: query='%s' → %d/%d flows active (threshold=%.2f)",
                query[:60], len(active), len(candidates), thresh,
            )
            return active[: self.max_active_flows]

        except Exception as e:
            logger.warning("[DynamicRoute] relevance filter failed: %s — falling back to all", e)
            return sorted(candidates)

    @classmethod
    def from_strategy(cls, strategy: str) -> DynamicRoutingPolicy:
        """
        Создать политику на основе торговой стратегии.

        SWING     → ENSEMBLE (базовые узлы + релевантные flow-ы)
        INTRADAY  → RELEVANCE (только релевантные flow-ы, выше порог)
        SCALP     → FIXED (минимальный набор — только TechnicalFlow)
        """
        strategy_upper = strategy.upper()
        if strategy_upper == "SWING":
            return cls(mode=RouteMode.ENSEMBLE, threshold=0.55, min_active_flows=2)
        if strategy_upper == "INTRADAY":
            return cls(mode=RouteMode.RELEVANCE, threshold=0.70, min_active_flows=1, max_active_flows=3)
        if strategy_upper == "SCALP":
            return cls(mode=RouteMode.FIXED, min_active_flows=0, max_active_flows=1)
        return cls(mode=RouteMode.FIXED)

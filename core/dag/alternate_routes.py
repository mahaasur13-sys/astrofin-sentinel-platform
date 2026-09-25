"""
AstroFin Sentinel V5 — Alternate Routes (P3: Sprint G)

Определяет альтернативные пути исполнения при сбое узлов DAG.
Заменяет жёсткий fallback_node_id на многоуровневые стратегии обхода.

Strategies:
  - skip:         пропустить узел и продолжить (деградация без остановки DAG)
  - delegate:     передать работу другому узлу того же уровня
  - retry_params: повторить с другими параметрами (др. провайдер, др. таймфрейм)
  - cache_fallback: использовать кэшированный результат предыдущего прогона
  - escalate:     поднять на уровень выше (напр. при отказе PriceNode → RouterNode)

Usage:
    from core.dag.alternate_routes import RouteCatalog, RouteStrategy

    catalog = RouteCatalog()
    catalog.register("PriceNode", RouteStrategy.SKIP, priority=10)
    strategy = catalog.resolve("PriceNode")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Any

try:
    from prometheus_client import Counter
    _ROUTE_ACTIVATIONS = Counter(
        "dag_alternate_route_activations_total",
        "Total alternate route activations",
        ["node_id", "strategy", "trigger"],
    )
    _METRICS_ENABLED = True
except ImportError:
    _METRICS_ENABLED = False

logger = logging.getLogger(__name__)


class RouteStrategy(str, Enum):
    """Стратегия альтернативного маршрута при сбое узла."""

    SKIP = "skip"
    """Пропустить узел. DAG продолжается без его выхода."""

    DELEGATE = "delegate"
    """Передать работу другому узлу того же уровня."""

    RETRY_PARAMS = "retry_params"
    """Повторить с другими параметрами (альтернативный провайдер, символ)."""

    CACHE_FALLBACK = "cache_fallback"
    """Использовать кэшированный результат предыдущего прогона."""

    ESCALATE = "escalate"
    """Поднять ошибку на уровень выше (родительский узел обрабатывает)."""


class TriggerReason(str, Enum):
    """Что вызвало активацию альтернативного маршрута."""

    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    CIRCUIT_OPEN = "circuit_open"
    VALIDATION_FAILED = "validation_failed"
    MAX_RETRIES = "max_retries"
    EXTERNAL_429 = "external_429"
    EXTERNAL_5XX = "external_5xx"


@dataclass
class AlternateRoute:
    """
    Один альтернативный маршрут для конкретного сценария сбоя.

    Attributes:
        node_id: узел, к которому применяется маршрут
        strategy: тип стратегии (skip/delegate/retry_params/...)
        priority: приоритет (меньше = раньше пробуется, 0-99)
        delegate_to: node_id узла-делегата (только для DELEGATE)
        trigger_reasons: список триггеров, при которых активируется
        retry_kwargs: дополнительные параметры для RETRY_PARAMS
        description: человекочитаемое описание
    """

    node_id: str
    strategy: RouteStrategy
    priority: int = 50
    delegate_to: Optional[str] = None
    trigger_reasons: list[TriggerReason] = field(default_factory=list)
    retry_kwargs: dict[str, Any] = field(default_factory=dict)
    description: str = ""


class RouteCatalog:
    """
    Каталог альтернативных маршрутов для DAG-узлов.

    Маршруты регистрируются по node_id и активируются автоматически
    при сбое узла (в pipeline.py).
    """

    def __init__(self) -> None:
        self._routes: dict[str, list[AlternateRoute]] = {}

    def register(
        self,
        node_id: str,
        strategy: RouteStrategy,
        priority: int = 50,
        delegate_to: Optional[str] = None,
        trigger_reasons: Optional[list[TriggerReason]] = None,
        retry_kwargs: Optional[dict[str, Any]] = None,
        description: str = "",
    ) -> None:
        """
        Зарегистрировать альтернативный маршрут для узла.

        Пример:
            catalog.register(
                "PriceNode",
                RouteStrategy.RETRY_PARAMS,
                priority=10,
                trigger_reasons=[TriggerReason.PROVIDER_ERROR],
                retry_kwargs={"provider": "binance"},
                description="Fallback to Binance if CoinGecko fails",
            )
        """
        route = AlternateRoute(
            node_id=node_id,
            strategy=strategy,
            priority=priority,
            delegate_to=delegate_to,
            trigger_reasons=trigger_reasons or [],
            retry_kwargs=retry_kwargs or {},
            description=description,
        )
        self._routes.setdefault(node_id, []).append(route)
        self._routes[node_id].sort(key=lambda r: r.priority)
        logger.debug(
            "[AlternateRoute] registered %s → %s (priority=%d, triggers=%s)",
            node_id, strategy.value, priority,
            [t.value for t in route.trigger_reasons],
        )

    def resolve(
        self,
        node_id: str,
        trigger: TriggerReason,
    ) -> Optional[AlternateRoute]:
        """
        Найти лучший альтернативный маршрут для узла по триггеру.

        Args:
            node_id: идентификатор узла
            trigger: причина сбоя

        Returns:
            AlternateRoute или None, если маршрутов нет
        """
        candidates = self._routes.get(node_id, [])
        for route in candidates:
            if not route.trigger_reasons or trigger in route.trigger_reasons:
                _record_activation(node_id, route.strategy.value, trigger.value)
                logger.warning(
                    "[AlternateRoute] activated: %s → %s (trigger=%s, priority=%d)",
                    node_id, route.strategy.value, trigger.value, route.priority,
                )
                return route
        return None

    def list_for_node(self, node_id: str) -> list[AlternateRoute]:
        """Все маршруты для узла, отсортированные по приоритету."""
        return list(self._routes.get(node_id, []))

    def node_ids(self) -> list[str]:
        """Все node_id с зарегистрированными маршрутами."""
        return list(self._routes.keys())

    def clear(self) -> None:
        self._routes.clear()

    def stats(self) -> dict:
        return {
            "nodes_with_routes": len(self._routes),
            "total_routes": sum(len(v) for v in self._routes.values()),
            "strategies": {
                sid: sum(1 for routes in self._routes.values()
                         for r in routes if r.strategy.value == sid)
                for sid in [s.value for s in RouteStrategy]
            },
        }


def _record_activation(node_id: str, strategy: str, trigger: str) -> None:
    if _METRICS_ENABLED:
        _ROUTE_ACTIVATIONS.labels(
            node_id=node_id, strategy=strategy, trigger=trigger,
        ).inc()


# ── Factory: Default Route Catalog для AstroFin Sentinel ──────────────────

def build_default_route_catalog() -> RouteCatalog:
    """
    Построить каталог альтернативных маршрутов с production-безопасными
    значениями по умолчанию.

    Стратегия:
      - PriceNode:     retry с Binance, затем skip с cache_fallback
      - RAGNode:       skip (пропустить RAG — синтез без контекста)
      - Flow-узлы:     skip (деградация без одного flow-а допустима)
      - KARL:          delegate → SynthesisNode (уже через fallback_node_id)
      - PersistNode:   skip (некритично — алерт всё равно уйдёт)
      - AlertNode:     skip (некритично — данные сохранены)
    """
    catalog = RouteCatalog()

    # PriceNode: CoinGecko → Binance → skip (cache)
    for trigger in [TriggerReason.PROVIDER_ERROR, TriggerReason.EXTERNAL_429,
                    TriggerReason.EXTERNAL_5XX, TriggerReason.TIMEOUT,
                    TriggerReason.CIRCUIT_OPEN]:
        catalog.register(
            "PriceNode",
            RouteStrategy.RETRY_PARAMS,
            priority=10,
            trigger_reasons=[trigger],
            retry_kwargs={"provider": "binance"},
            description="Fallback to Binance when CoinGecko fails",
        )
    catalog.register(
        "PriceNode",
        RouteStrategy.CACHE_FALLBACK,
        priority=20,
        trigger_reasons=[TriggerReason.MAX_RETRIES],
        description="Use cached price from previous DAG run",
    )
    catalog.register(
        "PriceNode",
        RouteStrategy.SKIP,
        priority=30,
        trigger_reasons=[TriggerReason.MAX_RETRIES],
        description="Skip entirely — synthesis works without price",
    )

    # RAGNode: skip (синтез без контекста RAG допустим)
    catalog.register(
        "RAGNode",
        RouteStrategy.SKIP,
        priority=50,
        trigger_reasons=[TriggerReason.MAX_RETRIES, TriggerReason.TIMEOUT],
        description="Skip RAG — synthesis works without context",
    )

    # Flow-узлы: skip (один flow может отсутствовать)
    for flow_id in ["TechnicalFlowNode", "MacroFlowNode", "AstroFlowNode",
                     "ElectoralFlowNode"]:
        catalog.register(
            flow_id,
            RouteStrategy.SKIP,
            priority=40,
            trigger_reasons=[TriggerReason.MAX_RETRIES, TriggerReason.TIMEOUT],
            description=f"Skip {flow_id} — DAG degrades gracefully",
        )

    # KARLPostProcessNode: delegate → SynthesisNode
    catalog.register(
        "KARLPostProcessNode",
        RouteStrategy.DELEGATE,
        priority=10,
        delegate_to="SynthesisNode",
        trigger_reasons=[TriggerReason.MAX_RETRIES, TriggerReason.TIMEOUT],
        description="Delegate to SynthesisNode when KARL fails",
    )

    # PersistNode: skip (данные не записаны в БД, но алерт отработает)
    catalog.register(
        "PersistNode",
        RouteStrategy.SKIP,
        priority=50,
        trigger_reasons=[TriggerReason.MAX_RETRIES, TriggerReason.TIMEOUT],
        description="Skip DB persistence — alert still fires from live data",
    )

    # AlertNode: skip (некритично)
    catalog.register(
        "AlertNode",
        RouteStrategy.SKIP,
        priority=50,
        trigger_reasons=[TriggerReason.MAX_RETRIES, TriggerReason.TIMEOUT],
        description="Skip Telegram alert — non-critical",
    )

    return catalog


# ── Global singleton ──────────────────────────────────────────────────────

_default_catalog: Optional[RouteCatalog] = None


def get_route_catalog() -> RouteCatalog:
    global _default_catalog
    if _default_catalog is None:
        _default_catalog = build_default_route_catalog()
    return _default_catalog

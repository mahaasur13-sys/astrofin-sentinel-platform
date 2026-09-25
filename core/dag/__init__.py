"""AstroFin DAG Orchestration Engine.

Легковесный DAG-движок для графовой мультиагентной архитектуры.
Узлы исполняются параллельно по уровням, зависимости разрешаются автоматически.

Observability:
    OTEL-трейсинг и Prometheus-метрики встроены через core/dag/observability.py.
    При недоступности OTEL — graceful no-op (логирование продолжает работать).

Usage:
    from core.dag import DAGNode, DAGPipeline, DAGContext, NodeResult

    dag = DAGPipeline("BTCUSDT_analysis")
    dag.add_node(RouterNode(), depends_on=[])
    dag.add_node(MacroFlowNode(), depends_on=["RouterNode"])
    result = await dag.run(user_query="Analyze BTC", symbol="BTCUSDT")
"""

from core.dag.context import DAGContext, NodeResult
from core.dag.metrics import DAGRunSummary, summarize_run
from core.dag.node import DAGNode
from core.dag.observability import (
    observe_node,
    observe_pipeline,
    record_cache_hit,
    record_node_duration,
    record_node_error,
    record_pipeline_run,
)
from core.dag.pipeline import DAGPipeline

__all__ = [
    "DAGNode",
    "DAGPipeline",
    "DAGContext",
    "NodeResult",
    "DAGRunSummary",
    "summarize_run",
    "observe_node",
    "observe_pipeline",
    "record_cache_hit",
    "record_node_duration",
    "record_node_error",
    "record_pipeline_run",
]

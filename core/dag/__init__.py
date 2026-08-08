"""AstroFin DAG Orchestration Engine.

Легковесный DAG-движок для графовой мультиагентной архитектуры.
Узлы исполняются параллельно по уровням, зависимости разрешаются автоматически.

Usage:
    from core.dag import DAGNode, DAGPipeline, DAGContext, NodeResult

    dag = DAGPipeline("BTCUSDT_analysis")
    dag.add_node(RouterNode(), depends_on=[])
    dag.add_node(MacroFlowNode(), depends_on=["RouterNode"])
    result = await dag.run(user_query="Analyze BTC", symbol="BTCUSDT")
"""

from core.dag.context import DAGContext, NodeResult
from core.dag.node import DAGNode
from core.dag.pipeline import DAGPipeline
from core.dag.metrics import DAGRunSummary, summarize_run

__all__ = [
    "DAGNode",
    "DAGPipeline",
    "DAGContext",
    "NodeResult",
    "DAGRunSummary",
    "summarize_run",
]

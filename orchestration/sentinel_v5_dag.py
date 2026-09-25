"""
AstroFin Sentinel v5 — DAG-Based Orchestrator

Заменяет монолитный run_karl_sentinel_v5() на графовую модель:
  Level 0: Router + Price + RAG (параллельно)
  Level 1: TechnicalFlow + MacroFlow + AstroFlow + ElectoralFlow (параллельно)
  Level 2: Synthesis (агрегация)
  Level 3: KARL Post-Process (AMRE calibration)
  Level 4: Persist + Alert (выходные узлы, параллельно)

Спринт G (2026-08-08) — DAG-пилот, 10 узлов.

Usage:
    python -m orchestration.sentinel_v5_dag "Analyze BTC" BTCUSDT SWING
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time

from core.dag import DAGPipeline
from core.dag.metrics import summarize_run

from orchestration.dag_nodes import (
    AlertNode,
    AstroFlowNode,
    ElectoralFlowNode,
    KARLPostProcessNode,
    MacroFlowNode,
    PersistNode,
    PriceNode,
    RAGNode,
    RouterNode,
    SynthesisNode,
    TechnicalFlowNode,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# DAG Pipeline Builder
# ═══════════════════════════════════════════════════════════════════════


def build_analysis_dag(name: str = "BTCUSDT_analysis") -> DAGPipeline:
    """
    Построить DAG-пайплайн полного анализа.

    Топология:
        Level 0: RouterNode, PriceNode, RAGNode        (параллельно)
        Level 1: TechnicalFlowNode, MacroFlowNode,       (параллельно)
                  AstroFlowNode, ElectoralFlowNode
        Level 2: SynthesisNode                           (ждёт все flow-ы)
        Level 3: KARLPostProcessNode                     (ждёт Synthesis)
        Level 4: PersistNode, AlertNode                  (параллельно)
    """

    pipeline = DAGPipeline(name)

    # Level 0 — независимые pre-flow узлы
    pipeline.add_node(RouterNode())
    pipeline.add_node(PriceNode())
    pipeline.add_node(RAGNode())

    # Level 1 — flow-ы агентов (зависят от Router, но не друг от друга)
    pipeline.add_node(TechnicalFlowNode(),
                      depends_on=["RouterNode", "PriceNode", "RAGNode"])
    pipeline.add_node(MacroFlowNode(),
                      depends_on=["RouterNode", "PriceNode", "RAGNode"])
    pipeline.add_node(AstroFlowNode(),
                      depends_on=["RouterNode", "PriceNode", "RAGNode"])
    pipeline.add_node(ElectoralFlowNode(),
                      depends_on=["RouterNode", "PriceNode", "RAGNode"])

    # Level 2 — синтез (ждёт все flow-ы)
    pipeline.add_node(SynthesisNode(),
                      depends_on=["TechnicalFlowNode", "MacroFlowNode",
                                  "AstroFlowNode", "ElectoralFlowNode"])

    # Level 3 — KARL пост-обработка (ждёт Synthesis)
    pipeline.add_node(KARLPostProcessNode(),
                      depends_on=["SynthesisNode"])

    # Level 4 — выходные узлы (параллельно)
    pipeline.add_node(PersistNode(),
                      depends_on=["KARLPostProcessNode"])
    pipeline.add_node(AlertNode(),
                      depends_on=["PersistNode"])

    return pipeline


def build_light_dag(name: str = "BTCUSDT_light") -> DAGPipeline:
    """
    Облегчённый DAG без KARL и без Electoral (быстрый анализ, ~5-8 сек).

    Узлы: Router → Price → RAG → MacroFlow → Synthesis → Persist
    """

    pipeline = DAGPipeline(name)

    pipeline.add_node(RouterNode())
    pipeline.add_node(PriceNode())
    pipeline.add_node(RAGNode())
    pipeline.add_node(MacroFlowNode(),
                      depends_on=["RouterNode", "PriceNode", "RAGNode"])
    pipeline.add_node(SynthesisNode(),
                      depends_on=["MacroFlowNode"])
    pipeline.add_node(PersistNode(),
                      depends_on=["SynthesisNode"])

    return pipeline


# ═══════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════


async def run_dag_analysis(
    user_query: str = "Analyze BTC",
    symbol: str = "BTCUSDT",
    timeframe: str = "SWING",
    light: bool = False,
) -> dict:
    """
    Выполнить полный DAG-анализ.

    Args:
        user_query: пользовательский запрос
        symbol: торговый символ
        timeframe: таймфрейм (SWING, INTRADAY, POSITIONAL, MONTHLY)
        light: использовать облегчённый DAG (без KARL/Electoral)

    Returns:
        dict с direction, confidence, risk_pct, summary
    """
    t0 = time.time()

    pipeline = build_light_dag(f"{symbol}_light") if light else build_analysis_dag(f"{symbol}_full")

    logger.info("DAG analysis starting: query=%r symbol=%s timeframe=%s light=%s",
                user_query, symbol, timeframe, light)

    ctx = await pipeline.run(
        user_query=user_query,
        symbol=symbol,
        timeframe=timeframe,
    )

    summary = summarize_run(ctx, name=pipeline.name)
    elapsed = time.time() - t0

    # Извлечь финальный сигнал
    persist = ctx.get("PersistNode")
    signal = {}
    if persist and persist.ok and isinstance(persist.output, dict):
        signal = persist.output

    result = {
        "direction": signal.get("direction", "NEUTRAL"),
        "confidence": signal.get("confidence", 0),
        "risk_pct": signal.get("risk_pct", 0.0),
        "session_id": signal.get("session_id", ""),
        "karl_applied": signal.get("karl_applied", False),
        "elapsed_s": round(elapsed, 2),
        "dag_summary": summary.as_dict(),
    }

    logger.info("DAG analysis completed: direction=%s confidence=%s elapsed=%.2fs",
                result["direction"], result["confidence"], elapsed)

    return result


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════


def main():
    """CLI entry point: python -m orchestration.sentinel_v5_dag [query] [symbol] [timeframe] [--light]"""
    query = sys.argv[1] if len(sys.argv) > 1 else "Analyze BTC"
    symbol = sys.argv[2] if len(sys.argv) > 2 else "BTCUSDT"
    timeframe = sys.argv[3] if len(sys.argv) > 3 else "SWING"
    light = "--light" in sys.argv

    result = asyncio.run(run_dag_analysis(
        user_query=query,
        symbol=symbol,
        timeframe=timeframe,
        light=light,
    ))

    print(f"\n{'='*60}")
    print(f"  DAG Analysis Result")
    print(f"{'='*60}")
    print(f"  Direction:    {result['direction']}")
    print(f"  Confidence:   {result['confidence']}%")
    print(f"  Risk:         {result['risk_pct']}%")
    print(f"  KARL applied: {result['karl_applied']}")
    print(f"  Session:      {result['session_id']}")
    print(f"  Elapsed:      {result['elapsed_s']}s")
    print(f"  Nodes OK:     {result['dag_summary']['ok_count']}/{result['dag_summary']['ok_count'] + result['dag_summary']['fail_count']}")
    print(f"  Bottleneck:   {result['dag_summary']['bottleneck_node']} ({result['dag_summary']['bottleneck_ms']}ms)")
    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    main()

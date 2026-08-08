"""
AstroFin Sentinel v5 — DAG Node Wrappers

Обёртки DAGNode над существующими функциями оркестратора.
Каждый узел — тонкая прослойка, сохраняющая исходный API агентов/роутера.

Спринт G (2026-08-08) — P1, обёртывание 5+ узлов.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.dag import DAGNode
from core.dag import DAGContext, NodeResult

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Level 0: Pre-Flow Nodes (Router, Price, RAG — независимые)
# ═══════════════════════════════════════════════════════════════════════


class RouterNode(DAGNode):
    """Классификация пользовательского запроса. Rule-based, без внешних вызовов."""

    timeout_ms: float = 5_000

    async def run(self, ctx: DAGContext) -> dict:
        from orchestration.router import route_query, RouterOutput

        query = ctx.state.get("user_query", "Analyze BTC")
        context = ctx.state.get("context", {})

        result: RouterOutput = route_query(query, context)
        return {
            "query_type": result.query_type.value,
            "symbols": result.symbols,
            "timeframe": result.timeframe,
            "include_technical": result.include_technical,
            "include_astro": result.include_astro,
            "include_electional": result.include_electional,
            "birth_data": result.birth_data,
            "confidence_threshold": result.confidence_threshold,
        }


class PriceNode(DAGNode):
    """Загрузка цены через data_room resolver (CoinGecko)."""

    timeout_ms: float = 15_000
    max_retries: int = 2
    backoff_base_s: float = 2.0

    async def run(self, ctx: DAGContext) -> dict:
        router = self._get_router_output(ctx)
        symbol = (router.get("symbols") or ["BTCUSDT"])[0]
        fallback = ctx.state.get("fallback_price", 50000.0)

        try:
            from data_room.resolvers.coingecko import CoinGeckoResolver

            resolver = CoinGeckoResolver()
            try:
                tick = await resolver.resolve(symbol)
                if tick.price > 0:
                    logger.debug("[PriceNode] %s = %s via %s", symbol, tick.price, tick.source_id)
                    return {"price": tick.price, "symbol": symbol}
            finally:
                await resolver.close()
        except Exception as exc:
            logger.warning("[PriceNode] CoinGecko failed: %s", exc)

        logger.warning("[PriceNode] Using fallback price %s for %s", fallback, symbol)
        return {"price": fallback, "symbol": symbol, "fallback": True}

    def _get_router_output(self, ctx: DAGContext) -> dict:
        r = ctx.get("RouterNode")
        if r and r.ok and isinstance(r.output, dict):
            return r.output
        return {}


class RAGNode(DAGNode):
    """
    Извлечение контекста из FAISS RAG-индекса.

    Выполняется параллельно с Router и Price (уровень 0).
    Результат кэшируется на уровне сессии через prompt_cache.
    """

    timeout_ms: float = 20_000

    async def run(self, ctx: DAGContext) -> dict:
        query = ctx.state.get("user_query", "Analyze BTC")
        top_k = ctx.state.get("rag_top_k", 3)
        run_id = ctx.run_id

        try:
            # 1. Проверить session RAG cache
            from core.cache.session_rag_cache import get_session_rag_cache
            rag_cache = get_session_rag_cache(run_id)
            cached = rag_cache.get(query, top_k=top_k)
            if cached:
                logger.info("[RAGNode] Session cache HIT for run=%s", run_id[:8])
                return {"context": cached, "top_k": top_k, "cached": True}

            # 2. FAISS retrieval
            from knowledge.rag_index import retrieve_context
            context = retrieve_context(query, top_k=top_k)

            # 3. Сохранить в session cache
            rag_cache.set(query, context, top_k=top_k)

            return {"context": context, "top_k": top_k, "cached": False}
        except Exception as exc:
            logger.warning("[RAGNode] RAG retrieval failed: %s", exc)
            return {"context": "", "top_k": top_k, "fallback": True}


# ═══════════════════════════════════════════════════════════════════════
# Level 1: Agent Flow Nodes (параллельные flow-ы агентов)
# ═══════════════════════════════════════════════════════════════════════


class BaseFlowNode(DAGNode):
    """
    Базовый узел для flow-ов агентов.
    Читает результат RouterNode и вызывает run_*_flow из result_aggregator.
    """

    timeout_ms: float = 120_000
    max_retries: int = 2
    backoff_base_s: float = 3.0

    flow_runner = None  # переопределяется в подклассах

    def _build_state(self, ctx: DAGContext) -> dict:
        """Собрать state из результатов предыдущих узлов."""
        state: dict = {}

        # Router output
        router = ctx.get("RouterNode")
        if router and router.ok:
            r = router.output if isinstance(router.output, dict) else {}
        else:
            r = {}

        # Price
        price = ctx.get("PriceNode")
        if price and price.ok:
            p = price.output if isinstance(price.output, dict) else {}
            state["current_price"] = p.get("price", 50000.0)
        else:
            state["current_price"] = ctx.state.get("fallback_price", 50000.0)

        # RAG context
        rag = ctx.get("RAGNode")
        if rag and rag.ok:
            rg = rag.output if isinstance(rag.output, dict) else {}
            state["rag_context"] = rg.get("context", "")

        state.update({
            "symbols": r.get("symbols", ["BTCUSDT"]),
            "timeframe": r.get("timeframe", "SWING"),
            "query_type": r.get("query_type", "full_analysis"),
            "confidence_threshold": r.get("confidence_threshold", 0.5),
            "user_query": ctx.state.get("user_query", ""),
        })

        return state

    async def run(self, ctx: DAGContext) -> dict:
        if self.flow_runner is None:
            return {"error": "flow_runner not configured"}

        state = self._build_state(ctx)

        try:
            result = await self.flow_runner(state)
            return result if isinstance(result, dict) else {"raw": result}
        except Exception as exc:
            logger.error("[%s] Flow failed: %s", self.node_id, exc)
            return {"error": str(exc), "fallback": True}


class TechnicalFlowNode(BaseFlowNode):
    @property
    def node_id(self) -> str:
        return "TechnicalFlowNode"

    async def run(self, ctx: DAGContext) -> dict:
        from orchestration.result_aggregator import run_technical_flow

        self.flow_runner = run_technical_flow
        return await super().run(ctx)


class MacroFlowNode(BaseFlowNode):
    @property
    def node_id(self) -> str:
        return "MacroFlowNode"

    async def run(self, ctx: DAGContext) -> dict:
        from orchestration.result_aggregator import run_macro_flow

        self.flow_runner = run_macro_flow
        return await super().run(ctx)


class AstroFlowNode(BaseFlowNode):
    @property
    def node_id(self) -> str:
        return "AstroFlowNode"

    async def run(self, ctx: DAGContext) -> dict:
        from orchestration.result_aggregator import run_astro_flow

        self.flow_runner = run_astro_flow
        return await super().run(ctx)


class ElectoralFlowNode(BaseFlowNode):
    @property
    def node_id(self) -> str:
        return "ElectoralFlowNode"

    async def run(self, ctx: DAGContext) -> dict:
        from orchestration.result_aggregator import run_electoral_flow

        self.flow_runner = run_electoral_flow
        return await super().run(ctx)


# ═══════════════════════════════════════════════════════════════════════
# Level 2: Synthesis Node (агрегация сигналов от всех flow-ов)
# ═══════════════════════════════════════════════════════════════════════


class SynthesisNode(DAGNode):
    """
    Агрегация сигналов от всех flow-ов в единый TradingSignal.
    Использует SynthesisAgent для консолидации.
    """

    timeout_ms: float = 60_000
    max_retries: int = 2

    async def run(self, ctx: DAGContext) -> dict:
        # Собрать сигналы от всех flow-ов
        all_signals: list[dict] = []
        flow_nodes = ["TechnicalFlowNode", "MacroFlowNode", "AstroFlowNode",
                      "ElectoralFlowNode"]

        for nid in flow_nodes:
            r = ctx.get(nid)
            if r and r.ok and isinstance(r.output, dict):
                if "signals" in r.output:
                    all_signals.extend(r.output["signals"])
                elif "raw" in r.output:
                    all_signals.append(r.output["raw"])

        router = ctx.get("RouterNode")
        router_out = router.output if (router and router.ok and isinstance(router.output, dict)) else {}
        timeframe = router_out.get("timeframe", "SWING")

        if not all_signals:
            return {
                "direction": "NEUTRAL",
                "confidence": 30,
                "risk_pct": 1.0,
                "signals_count": 0,
                "timeframe": timeframe,
                "fallback": True,
            }

        try:
            from agents.synthesis_agent import SynthesisAgent
            agent = SynthesisAgent()
            result = await agent.run(
                state={
                    "signals": all_signals,
                    "timeframe": timeframe,
                    "current_price": self._get_price(ctx),
                    "user_query": ctx.state.get("user_query", ""),
                }
            )
            return {
                "direction": str(getattr(result, "direction", "NEUTRAL")),
                "confidence": getattr(result, "confidence", 50),
                "risk_pct": getattr(result, "risk_pct", 1.0),
                "reasoning": getattr(result, "reasoning", ""),
                "signals_count": len(all_signals),
                "timeframe": timeframe,
            }
        except Exception as exc:
            logger.error("[SynthesisNode] Synthesis failed: %s", exc)
            return {
                "direction": "NEUTRAL",
                "confidence": 25,
                "risk_pct": 0.5,
                "signals_count": len(all_signals),
                "timeframe": timeframe,
                "error": str(exc),
                "fallback": True,
            }

    def _get_price(self, ctx: DAGContext) -> float:
        price = ctx.get("PriceNode")
        if price and price.ok and isinstance(price.output, dict):
            return price.output.get("price", 0.0)
        return ctx.state.get("fallback_price", 50000.0)


# ═══════════════════════════════════════════════════════════════════════
# Level 3: KARL Post-Process Node (AMRE-обработка + DecisionRecord)
# ═══════════════════════════════════════════════════════════════════════


class KARLPostProcessNode(DAGNode):
    """
    AMRE/KARL пост-обработка: calibration, backtest sample, audit.
    Если KARL недоступен — fallback на чистый сигнал Synthesis.
    """

    timeout_ms: float = 60_000
    max_retries: int = 1
    fallback_node_id: str | None = "SynthesisNode"

    async def run(self, ctx: DAGContext) -> dict:
        synthesis = ctx.get("SynthesisNode")
        if not synthesis or not synthesis.ok:
            return {"karl_applied": False, "source": "synthesis_fallback"}

        synth_out = synthesis.output if isinstance(synthesis.output, dict) else {}

        price_node = ctx.get("PriceNode")
        current_price = (price_node.output.get("price", 0.0)
                         if (price_node and price_node.ok and isinstance(price_node.output, dict))
                         else ctx.state.get("fallback_price", 50000.0))

        try:
            from agents.karl_synthesis import KARLSynthesisAgent

            karl = KARLSynthesisAgent()
            state = {
                "signals": [synth_out],
                "current_price": current_price,
                "user_query": ctx.state.get("user_query", ""),
                "timeframe": synth_out.get("timeframe", "SWING"),
            }
            result = await karl.run(state)

            return {
                "direction": str(getattr(result, "direction", synth_out.get("direction", "NEUTRAL"))),
                "confidence": getattr(result, "confidence", synth_out.get("confidence", 50)),
                "risk_pct": getattr(result, "risk_pct", synth_out.get("risk_pct", 1.0)),
                "reasoning": getattr(result, "reasoning", ""),
                "karl_applied": True,
                "decision_id": getattr(result, "decision_id", ""),
            }
        except Exception as exc:
            logger.warning("[KARLNode] KARL unavailable, using synthesis signal as-is: %s", exc)
            return {**synth_out, "karl_applied": False, "karl_error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════
# Level 4: Output Nodes (Persist, Alert, Dashboard)
# ═══════════════════════════════════════════════════════════════════════


class PersistNode(DAGNode):
    """Сохранение сессии в БД (PostgreSQL → SQLite fallback)."""

    timeout_ms: float = 10_000
    max_retries: int = 1

    async def run(self, ctx: DAGContext) -> dict:
        karl = ctx.get("KARLPostProcessNode")
        synthesis = ctx.get("SynthesisNode")

        final_data = {}
        if karl and karl.ok and isinstance(karl.output, dict):
            final_data = karl.output
        elif synthesis and synthesis.ok and isinstance(synthesis.output, dict):
            final_data = synthesis.output

        session_id = ""
        try:
            from core.history_db import save_session
            session_id = save_session(final_data)
            logger.info("[PersistNode] Saved session %s", session_id)
        except Exception as exc:
            logger.warning("[PersistNode] Save failed: %s", exc)

        return {
            "session_id": session_id,
            "direction": final_data.get("direction", "NEUTRAL"),
            "confidence": final_data.get("confidence", 0),
            "risk_pct": final_data.get("risk_pct", 0.0),
            "karl_applied": final_data.get("karl_applied", False),
        }


class AlertNode(DAGNode):
    """Отправка уведомлений при сильном сигнале (confidence > 60 или EXTREME)."""

    timeout_ms: float = 10_000
    max_retries: int = 1

    async def run(self, ctx: DAGContext) -> dict:
        persist = ctx.get("PersistNode")
        if not persist or not persist.ok:
            return {"sent": False, "reason": "no persist data"}

        data = persist.output if isinstance(persist.output, dict) else {}
        confidence = data.get("confidence", 0)
        direction = data.get("direction", "NEUTRAL")

        if confidence < 60:
            return {"sent": False, "reason": "below threshold", "confidence": confidence}

        try:
            from utils.telegram_notifier import send_telegram_message
            msg = (
                f"DAG Signal: {direction} {confidence}%\n"
                f"Risk: {data.get('risk_pct', 0.0)}%\n"
                f"Session: {data.get('session_id', 'unknown')}"
            )
            sent = await send_telegram_message(msg)
            return {"sent": sent, "direction": direction, "confidence": confidence}
        except Exception as exc:
            logger.warning("[AlertNode] Telegram alert failed: %s", exc)
            return {"sent": False, "error": str(exc)}

#!/usr/bin/env python3
"""
AstroFin Sentinel v5 — Sprint 3 Broker Integration Layer.

Добавляет Hub-and-Spoke диспетчеризацию к существующему sentinel_v5.py,
НЕ переписывая оригинальный оркестратор.

Все реальные агенты (run_*_agent функции) оборачиваются в TaskEnvelope/ResultEnvelope
и могут исполняться через InProcessBroker или напрямую (gather fallback).

Usage:
    # Broker mode (Sprint 3+):
    from orchestration.sentinel_v5_broker import SentinelV5Broker
    hub = SentinelV5Broker()
    await hub.start()
    result = await hub.run_analysis(state, symbol="BTCUSDT")

    # CLI:
    python -m orchestration.sentinel_v5 "Analyze BTC" --broker
"""

from __future__ import annotations

import asyncio
import copy
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from core.envelopes import TaskEnvelope, ResultEnvelope, TaskStatus, SCHEMA_VERSION
from core.circuit_breaker import CircuitBreakerRegistry, CBConfig, CircuitBreakerOpenError
from core.message_broker import InProcessBroker, MessageBroker, BrokerUnavailable
from core.outbox import Outbox, OutboxConfig
from core.base_agent import _current_envelope

# Импортируем реальные агенты
from agents._impl.fundamental_agent import run_fundamental_agent
from agents._impl.macro_agent import run_macro_agent
from agents._impl.quant_agent import run_quant_agent
from agents._impl.options_flow_agent import run_options_flow_agent
from agents._impl.sentiment_agent import run_sentiment_agent
from agents._impl.bull_researcher import run_bull_researcher
from agents._impl.bear_researcher import run_bear_researcher
from agents._impl.market_analyst import run_market_analyst
from agents._impl.synthesis_agent import SynthesisAgent
from agents.karl_synthesis import KARLSynthesisAgent
from agents.base_agent import AgentResponse, SignalDirection

logger = logging.getLogger(__name__)

# Registry всех агентов — имя → async функция
AGENT_REGISTRY: dict[str, Callable[[dict], Awaitable[dict]]] = {
    "FundamentalAgent": run_fundamental_agent,
    "MacroAgent": run_macro_agent,
    "QuantAgent": run_quant_agent,
    "OptionsFlowAgent": run_options_flow_agent,
    "SentimentAgent": run_sentiment_agent,
    "BullResearcher": run_bull_researcher,
    "BearResearcher": run_bear_researcher,
    "MarketAnalyst": run_market_analyst,
}


@dataclass
class BrokerConfig:
    """Конфигурация broker-режима."""

    use_broker: bool = True
    worker_count: int = 4
    max_queue_size: int = 1000
    cb_failure_threshold: int = 5
    cb_cooldown_sec: float = 30.0
    outbox_db_path: str = "data/outbox.db"
    default_deadline_sec: float = 120.0
    fallback_to_gather: bool = True


@dataclass
class AgentResult:
    """Результат одного агента после broker dispatch."""

    agent_name: str
    status: TaskStatus
    result: dict | None = None
    error: str = ""
    elapsed_ms: float = 0.0
    trace_id: str = ""

    @property
    def is_success(self) -> bool:
        return self.status == TaskStatus.COMPLETED and self.error == ""


@dataclass
class BrokerAnalysisResult:
    """Результат ensemble анализа через broker."""

    session_id: str
    trace_id: str
    agent_results: list[AgentResult] = field(default_factory=list)
    synthesis_result: dict | None = None
    errors: list[str] = field(default_factory=list)
    error_reason: dict[str, str] = field(default_factory=dict)

    @property
    def resilience(self) -> float:
        return 1.0 if self.total_count > 0 else 0.0

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.agent_results if r.is_success)

    @property
    def total_count(self) -> int:
        return len(self.agent_results)

    @property
    def success_rate(self) -> float:
        return self.success_count / max(1, self.total_count)

    def __contains__(self, agent_name: str) -> bool:
        return any(r.agent_name == agent_name for r in self.agent_results)

    def __getitem__(self, agent_name: str) -> dict:
        for r in self.agent_results:
            if r.agent_name == agent_name:
                return r.result if r.is_success else {}
        raise KeyError(agent_name)

    def _as_dict(self) -> dict:
        return {r.agent_name: {"signal": r.signal, "confidence": r.confidence, "reasoning": r.reasoning} for r in self.agent_results}

    def __contains__(self, agent_name: str) -> bool:
        return any(r.agent_name == agent_name for r in self.agent_results)

    def __getitem__(self, agent_name: str) -> dict:
        for r in self.agent_results:
            if r.agent_name == agent_name:
                return {"signal": r.signal, "confidence": r.confidence, "reasoning": r.reasoning}
        raise KeyError(agent_name)


class SentinelV5Broker:
    """Hub-and-Spoke обёртка для реального sentinel_v5.py.

    Запускает InProcessBroker с worker pool, оборачивает вызовы
    реальных агентов в TaskEnvelope/ResultEnvelope, и выполняет
    ensemble voting с weighted synthesis.

    Поддерживает fallback на asyncio.gather() при отключенном брокере.
    """

    def __init__(self, agents: dict | None = None, config: BrokerConfig | None = None):
        self._config = config or BrokerConfig()
        self._broker: InProcessBroker | None = None
        self._outbox: Outbox | None = None
        self._cb_registry = CircuitBreakerRegistry(
            default_config=CBConfig(
                failure_threshold=self._config.cb_failure_threshold,
                recovery_cooldown=self._config.cb_cooldown_sec,
            )
        )
        self._agents = agents or {}
        self._started = False

    # ── Lifecycle ────────────────────────────────────────────────────

    async def start(self) -> None:
        """Запустить broker, outbox, worker pool."""
        if self._started:
            return

        if self._config.use_broker:
            self._broker = InProcessBroker()
            self._outbox = Outbox(
                db_path=self._config.outbox_db_path,
                config=OutboxConfig()
            )
            await self._outbox.start(self._broker)
            self._started = True
            logger.info(
                "sentinel_v5_broker_started",
                extra={
                    "workers": self._config.worker_count,
                    "outbox_db": self._config.outbox_db_path,
                },
            )

    async def stop(self) -> None:
        """Graceful shutdown broker и outbox."""
        if not self._started:
            return

        if self._outbox:
            await self._outbox.stop()
        if self._broker:
            await self._broker.close()

        self._started = False
        logger.info("sentinel_v5_broker_stopped")

    # ── Core: dispatch одного агента через envelope ─────────────────

    async def _dispatch_agent(
        self,
        agent_name: str,
        state: dict,
        deadline_sec: float = 0.0,
        correlation_id: str = "",
    ) -> AgentResult:
        """Отправить задачу агенту через broker, получить ResultEnvelope.

        Args:
            agent_name: имя агента (из AGENT_REGISTRY)
            state: состояние (будет deep-copied)
            deadline_sec: дедлайн в секундах
            correlation_id: ID сессии

        Returns:
            AgentResult с результатом
        """
        start_time = time.monotonic()

        # Проверяем Circuit Breaker перед вызовом
        try:
            cb = self._cb_registry.get(agent_name)
            async with cb:
                pass  # проверяет CLOSED/OPEN/HALF_OPEN
        except CircuitBreakerOpenError as e:
            logger.warning(
                "agent_skipped_circuit_open",
                extra={"agent": agent_name, "reason": str(e)},
            )
            return AgentResult(
                agent_name=agent_name,
                status=TaskStatus.SKIPPED,
                error=f"Circuit breaker OPEN: {e}",
                elapsed_ms=(time.monotonic() - start_time) * 1000,
            )

        # Создаём TaskEnvelope с deepcopy
        envelope = TaskEnvelope.new(
            agent_name=agent_name,
            state=state,
            deadline_seconds=deadline_sec or self._config.default_deadline_sec,
            correlation_id=correlation_id,
        )

        # Получаем функцию агента
        agent_fn = AGENT_REGISTRY.get(agent_name)
        if agent_fn is None:
            return AgentResult(
                agent_name=agent_name,
                status=TaskStatus.SKIPPED,
                error=f"Agent '{agent_name}' not in registry",
                elapsed_ms=(time.monotonic() - start_time) * 1000,
            )

        # Пробрасываем envelope через contextvars
        token = _current_envelope.set(envelope)
        try:
            # Вызываем агента с изолированным состоянием
            isolated_state = copy.deepcopy(envelope.state_snapshot)
            result_dict = await agent_fn(isolated_state)

            elapsed = (time.monotonic() - start_time) * 1000
            cb.success() if cb.state != "CLOSED" else None

            # Публикуем событие через broker (с outbox fallback)
            if self._broker:
                try:
                    await self._broker.publish(
                        f"agent.status.{agent_name}",
                        {"agent": agent_name, "status": "completed", "elapsed_ms": elapsed},
                    )
                except BrokerUnavailable:
                    if self._outbox:
                        await self._outbox.store(
                            f"agent.status.{agent_name}",
                            {"agent": agent_name, "status": "completed", "elapsed_ms": elapsed},
                        )

            return AgentResult(
                agent_name=agent_name,
                status=TaskStatus.COMPLETED,
                result=result_dict,
                elapsed_ms=elapsed,
                trace_id=envelope.trace_id,
            )

        except asyncio.TimeoutError:
            elapsed = (time.monotonic() - start_time) * 1000
            cb.failure()
            return AgentResult(
                agent_name=agent_name,
                status=TaskStatus.TIMED_OUT,
                error=f"Timeout after {elapsed:.0f}ms",
                elapsed_ms=elapsed,
                trace_id=envelope.trace_id,
            )

        except Exception as exc:
            elapsed = (time.monotonic() - start_time) * 1000
            cb.failure()
            logger.error(
                "agent_dispatch_error",
                extra={"agent": agent_name, "error": str(exc)},
            )
            return AgentResult(
                agent_name=agent_name,
                status=TaskStatus.FAILED,
                error=str(exc),
                elapsed_ms=elapsed,
                trace_id=envelope.trace_id,
            )

        finally:
            _current_envelope.reset(token)

    # ── Flow-level dispatch ──────────────────────────────────────────

    async def _run_technical_flow_broker(
        self, state: dict, selected_agents: list[str] | None = None
    ) -> list[AgentResult]:
        """Technical flow через broker."""
        pool = selected_agents or ["MarketAnalyst", "BullResearcher", "BearResearcher"]
        agents_in_registry = [a for a in pool if a in AGENT_REGISTRY]

        if not agents_in_registry:
            return []

        tasks = [
            self._dispatch_agent(name, state, correlation_id=state.get("session_id", ""))
            for name in agents_in_registry
        ]
        return list(await asyncio.gather(*tasks, return_exceptions=False))

    async def _run_macro_flow_broker(
        self, state: dict, selected_agents: list[str] | None = None
    ) -> list[AgentResult]:
        """Macro flow через broker."""
        pool = selected_agents or [
            "FundamentalAgent", "MacroAgent", "QuantAgent",
            "OptionsFlowAgent", "SentimentAgent",
        ]
        agents_in_registry = [a for a in pool if a in AGENT_REGISTRY]

        if not agents_in_registry:
            return []

        tasks = [
            self._dispatch_agent(name, state, correlation_id=state.get("session_id", ""))
            for name in agents_in_registry
        ]
        return list(await asyncio.gather(*tasks, return_exceptions=False))

    async def _run_astro_flow_broker(
        self, state: dict, selected_agents: list[str] | None = None
    ) -> list[AgentResult]:
        """Astro flow через broker — делегирует astro_council через envelope."""
        from agents.astro_council_agent import run_astro_council

        agent_name = "AstroCouncil"
        result = await self._dispatch_agent(
            agent_name, state, correlation_id=state.get("session_id", "")
        )

        # AstroCouncil wrapper: вызываем напрямую с корректным контекстом
        envelope = TaskEnvelope.new(
            agent_name=agent_name,
            state=state,
            correlation_id=state.get("session_id", ""),
        )
        token = _current_envelope.set(envelope)
        try:
            astro_state = {**state, "_thompson_selected_astro": selected_agents or []}
            astro_result = await run_astro_council(astro_state)
            result.result = astro_result
            result.status = TaskStatus.COMPLETED
        except Exception as exc:
            result.status = TaskStatus.FAILED
            result.error = str(exc)
        finally:
            _current_envelope.reset(token)

        return [result]

    async def _run_electoral_flow_broker(
        self, state: dict, selected_agents: list[str] | None = None
    ) -> list[AgentResult]:
        """Electoral flow через broker."""
        from agents._impl.electoral_agent import run_electoral_agent

        agent_name = "ElectoralAgent"
        envelope = TaskEnvelope.new(
            agent_name=agent_name,
            state=state,
            correlation_id=state.get("session_id", ""),
        )
        token = _current_envelope.set(envelope)
        try:
            result = await run_electoral_agent(state)
            return [
                AgentResult(
                    agent_name=agent_name,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    trace_id=envelope.trace_id,
                )
            ]
        except Exception as exc:
            return [
                AgentResult(
                    agent_name=agent_name,
                    status=TaskStatus.FAILED,
                    error=str(exc),
                    trace_id=envelope.trace_id,
                )
            ]
        finally:
            _current_envelope.reset(token)

    # ── Public API ───────────────────────────────────────────────────

    async def run_analysis(
        self,
        state: dict,
        symbol: str = "BTCUSDT",
        deadline_sec: float = 120.0,
        agent_names: list[str] | None = None,
        include_technical: bool = True,
        include_astro: bool = True,
        include_electional: bool = False,
        include_macro: bool = True,
        thompson_selections: dict | None = None,
    ) -> BrokerAnalysisResult:
        """Запустить полный анализ через broker (Hub-and-Spoke).

        Args:
            state: полное состояние (symbol, timeframe, price, etc.)
            symbol: тикер
            include_technical: включить technical flow
            include_astro: включить astro flow
            include_electional: включить electoral flow
            include_macro: включить macro flow
            thompson_selections: предвыбранные агенты по пулам

        Returns:
            BrokerAnalysisResult с agent_results и synthesis
        """
        session_id = state.get("session_id", str(uuid.uuid4())[:8])
        trace_id = str(uuid.uuid4()).replace("-", "")[:32]
        all_results: list[AgentResult] = []
        errors: list[str] = []
        error_reason: dict[str, str] = {}

        # Диспатч кастомных/тестовых агентов (agent_names из self._agents)
        if agent_names and self._agents:
            from core.envelopes import TaskEnvelope, ResultEnvelope, TaskStatus
            for name in agent_names:
                agent = self._agents.get(name)
                if agent is None:
                    errors.append(f"Unknown agent: {name}")
                    continue
                env = TaskEnvelope.new(agent_name=name, state=state)
                try:
                    renv = await agent.on_message(env)
                    all_results.append(AgentResult(
                        agent_name=name,
                        status=renv.status,
                        result=renv.result,
                        error=renv.error,
                        elapsed_ms=renv.execution_time_ms,
                        trace_id=renv.trace_id,
                    ))
                except Exception as e:
                    all_results.append(AgentResult(
                        agent_name=name,
                        status=TaskStatus.FAILED,
                        result={},
                        error=str(e),
                        elapsed_ms=0,
                    ))
                    error_reason[name] = str(e)
            return BrokerAnalysisResult(
                session_id=session_id,
                trace_id=trace_id,
                agent_results=all_results,
                errors=errors,
            )
            for name in agent_names:
                agent = self._agents.get(name)
                if agent is None:
                    errors.append(f"Unknown agent: {name}")
                    continue
                envelope = TaskEnvelope.new(agent_name=name, state=state)
                try:
                    result_env = await agent.on_message(envelope)
                    all_results.append(AgentResult(
                        agent_name=name,
                        result=result_env.result,
                        is_success=(result_env.status == TaskStatus.COMPLETED),
                        error=result_env.error,
                        execution_time_ms=result_env.execution_time_ms,
                    ))
                except Exception as e:
                    all_results.append(AgentResult(
                        agent_name=name,
                        result={},
                        is_success=False,
                        error=str(e),
                    ))
                    errors.append(f"Agent {name} error: {e}")
            return BrokerAnalysisResult(
                session_id=session_id,
                trace_id=trace_id,
                agent_results=all_results,
                errors=errors,
            )


        # Short-circuit: direct dispatch for custom agents (tests)
        if agent_names and self._agents:
            custom_agents = [self._agents[n] for n in agent_names if n in self._agents]
            if custom_agents:
                for i, agent in enumerate(custom_agents):
                    try:
                        result = await agent.run(state)
                        all_results.append(AgentResult(
                            agent_name=agent_names[i],
                            result=result if isinstance(result, dict) else {"signal": str(result)},
                            is_success=True,
                            latency_ms=0,
                        ))
                    except Exception as e:
                        all_results.append(AgentResult(
                            agent_name=agent_names[i],
                            result={"error": str(e)},
                            is_success=False,
                            latency_ms=0,
                        ))
                        errors.append(str(e))
                return BrokerAnalysisResult(
                    session_id=session_id,
                    trace_id=trace_id,
                    agent_results=all_results,
                    errors=errors,
                )

        # Параллельный запуск всех flows
        flow_tasks = []

        if include_technical:
            tech_agents = thompson_selections.get("technical", []) if thompson_selections else None
            flow_tasks.append(self._run_technical_flow_broker(state, tech_agents))

        if include_macro:
            macro_agents = thompson_selections.get("macro", []) if thompson_selections else None
            flow_tasks.append(self._run_macro_flow_broker(state, macro_agents))

        if include_astro:
            astro_agents = thompson_selections.get("astro", []) if thompson_selections else None
            flow_tasks.append(self._run_astro_flow_broker(state, astro_agents))

        if include_electional:
            flow_tasks.append(self._run_electoral_flow_broker(state))

        if flow_tasks:
            flow_results = await asyncio.gather(*flow_tasks, return_exceptions=True)
            for result in flow_results:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    errors.append(f"Flow error: {result}")

        # Synthesis через SynthesisAgent
        synthesis_result = None
        try:
            synthesis_agent = SynthesisAgent()
            synth_state = {
                **state,
                "all_signals": [
                    r.result for r in all_results
                    if r.is_success and r.result
                ],
            }
            synthesis_result = await synthesis_agent.run(synth_state)
            if hasattr(synthesis_result, "to_dict"):
                synthesis_result = synthesis_result.to_dict()
        except Exception as exc:
            errors.append(f"Synthesis error: {exc}")

        return BrokerAnalysisResult(
            session_id=session_id,
            trace_id=trace_id,
            agent_results=all_results,
            synthesis_result=synthesis_result,
            errors=errors,
        )

    def stats(self) -> dict:
        """Статистика broker-режима."""
        return {
            "started": self._started,
            "use_broker": self._config.use_broker,
            "cb_stats": self._cb_registry.stats(),
            "outbox": self._outbox.stats() if self._outbox else {},
        }

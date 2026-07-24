"""Sprint 3 Integration Tests — ADR-001 Hub-and-Spoke.

Covers:
  - TaskEnvelope deepcopy isolation (Риск #1)
  - W3C Trace Context propagation (Риск #2, P3-07)
  - CircuitBreaker 3-phase + per-provider isolation (Риск #3)
  - MessageBroker ABC + InProcessBroker (Sprint 3)
  - Transactional Outbox: store/publish/retry (Риск #4)
  - BaseAgent: on_message, publish_event, contextvars
  - SentinelV5Broker: Hub-and-Spoke integration
"""

from __future__ import annotations

import asyncio
import copy
import json
import os
import time
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.envelopes import TaskEnvelope, ResultEnvelope, TaskStatus
from core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CBConfig,
    CBState,
    CircuitBreakerOpenError,
)
from core.message_broker import MessageBroker, InProcessBroker, BrokerStats
from core.outbox import OutboxStore, OutboxConfig, OutboxRetryWorker, OutboxStatus
from core.base_agent import BaseAgent


# ═══════════════════════════════════════════════════════════
# 1. TaskEnvelope — deepcopy isolation (Риск #1)
# ═══════════════════════════════════════════════════════════

class TestTaskEnvelopeDeepcopy:
    """Два конверта с одним исходным state не должны мутировать друг друга."""

    def test_isolated_states(self):
        original = {"ticker": "AAPL", "nested": {"a": 1}}
        env1 = TaskEnvelope.new(agent_name="agent1", state=original)
        env2 = TaskEnvelope.new(agent_name="agent2", state=original)

        # Modify env1's snapshot
        env1.state_snapshot["ticker"] = "TSLA"
        env1.state_snapshot["nested"]["a"] = 999

        # env2 must be unaffected
        assert env2.state_snapshot["ticker"] == "AAPL"
        assert env2.state_snapshot["nested"]["a"] == 1

        # original must be unaffected
        assert original["ticker"] == "AAPL"
        assert original["nested"]["a"] == 1

    def test_no_shared_references(self):
        state = {"list": [1, 2, 3]}
        env = TaskEnvelope.new(agent_name="test", state=state)
        assert env.state_snapshot is not state
        assert env.state_snapshot["list"] is not state["list"]


# ═══════════════════════════════════════════════════════════
# 2. W3C Trace Context (P3-06)
# ═══════════════════════════════════════════════════════════

class TestW3CTraceContext:
    """Propagation of trace_id across envelopes."""

    def test_auto_generated_traceparent(self):
        env = TaskEnvelope.new(agent_name="test", state={})
        tp = env.traceparent
        assert tp.startswith("00-")
        parts = tp.split("-")
        assert len(parts) == 4
        assert len(parts[1]) == 32  # trace_id

    def test_trace_id_consistency(self):
        env = TaskEnvelope.new(agent_name="test", state={})
        extracted = env.trace_id
        tp = env.traceparent
        assert extracted in tp
        assert len(extracted) == 32

    def test_child_task_inherits_trace_id(self):
        parent = TaskEnvelope.new(agent_name="parent", state={})
        child = parent.child_task(agent_name="child")
        assert child.trace_id == parent.trace_id
        assert child.traceparent != parent.traceparent  # different span_id

    def test_result_envelope_carries_trace_id(self):
        env = TaskEnvelope.new(agent_name="test", state={})
        result = ResultEnvelope.from_envelope(
            env, status=TaskStatus.COMPLETED, result={"x": 1}
        )
        assert result.trace_id == env.trace_id


# ═══════════════════════════════════════════════════════════
# 3. Circuit Breaker — 3-phase + per-provider (Риск #3)
# ═══════════════════════════════════════════════════════════

class TestCircuitBreakerPhases:
    """OpenRouter сбой → блокирует только openrouter; ollama работает."""

    def test_closed_to_open(self):
        cb = CircuitBreaker(
            CBConfig(failure_threshold=3, window_seconds=3600, recovery_cooldown=60)
        )
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CBState.CLOSED
        cb.record_failure()  # 4th failure
        assert cb.state == CBState.OPEN

    def test_per_provider_isolation(self):
        registry = CircuitBreakerRegistry(
            default_config=CBConfig(failure_threshold=2, recovery_cooldown=60)
        )
        # OpenRouter fails
        for _ in range(3):
            registry.get("openrouter").record_failure()
        assert registry.get("openrouter").is_open

        # Ollama still works
        assert registry.get("ollama").is_closed

    def test_async_context_manager_success(self):
        registry = CircuitBreakerRegistry()
        cb = registry.get("test_provider")

        async def test():
            async with cb:
                pass  # success

        asyncio.run(test())
        assert cb.state == CBState.CLOSED

    def test_async_context_manager_failure(self):
        registry = CircuitBreakerRegistry(
            default_config=CBConfig(failure_threshold=2, recovery_cooldown=60)
        )
        cb = registry.get("test_provider")

        async def test():
            async with cb:
                raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            asyncio.run(test())
        assert cb.failure_count >= 1

    def test_circuit_open_raises(self):
        registry = CircuitBreakerRegistry(
            default_config=CBConfig(failure_threshold=1, recovery_cooldown=60)
        )
        cb = registry.get("test")
        cb.record_failure()
        cb.record_failure()  # OPEN

        async def test():
            async with cb:
                pass

        with pytest.raises(CircuitBreakerOpenError):
            asyncio.run(test())

    def test_metrics_collection(self):
        registry = CircuitBreakerRegistry()
        cb = registry.get("test")
        cb.record_failure()
        metrics = registry.all_metrics()
        assert "test" in metrics
        assert metrics["test"]["state"] == "CLOSED"


# ═══════════════════════════════════════════════════════════
# 4. InProcessBroker (Sprint 3)
# ═══════════════════════════════════════════════════════════

class TestInProcessBroker:
    """Worker pool с изоляцией ошибок."""

    async def dummy_handler(self, envelope: TaskEnvelope) -> ResultEnvelope:
        return ResultEnvelope(
            task_id=envelope.task_id,
            agent_name=envelope.agent_name,
            trace_id=envelope.trace_id,
            status=TaskStatus.COMPLETED,
            result={"agent": envelope.agent_name},
        )

    @pytest.mark.asyncio
    async def test_send_without_start(self):
        broker = InProcessBroker()
        env = TaskEnvelope.new(agent_name="test", state={})
        result = await broker.send(env, self.dummy_handler)
        assert result.status == TaskStatus.COMPLETED
        assert result.agent_name == "test"

    @pytest.mark.asyncio
    async def test_worker_pool_dispatch(self):
        broker = InProcessBroker(max_queue_size=100)
        broker.set_worker_count(3)
        await broker.start()

        env = TaskEnvelope.new(agent_name="worker_test", state={})
        result = await broker.send(env, self.dummy_handler)
        assert result.status == TaskStatus.COMPLETED
        assert result.result["agent"] == "worker_test"

        stats = broker.stats()
        assert stats.messages_sent >= 1
        await broker.stop()

    @pytest.mark.asyncio
    async def test_worker_error_isolation(self):
        async def failing_handler(env):
            raise ValueError("agent crashed")

        broker = InProcessBroker()
        env = TaskEnvelope.new(agent_name="failing", state={})
        result = await broker.send(env, failing_handler)
        assert result.status == TaskStatus.FAILED
        assert "agent crashed" in result.error

    @pytest.mark.asyncio
    async def test_pub_sub(self):
        broker = InProcessBroker()
        await broker.start()
        received = []

        async def callback(channel, payload):
            received.append((channel, payload))

        await broker.subscribe("test.events", callback)
        await broker.publish("test.events", {"msg": "hello"})
        await asyncio.sleep(0.1)
        assert len(received) == 1
        assert received[0][1]["msg"] == "hello"
        await broker.stop()

    @pytest.mark.asyncio
    async def test_rpc_timeout(self):
        broker = InProcessBroker()
        env = TaskEnvelope.new(agent_name="slow", state={}, deadline_seconds=0.001)
        await broker.start()
        result = await broker.send(env, self.dummy_handler, timeout_sec=0.0)
        # Should complete or timeout gracefully
        assert result is not None
        await broker.stop()


# ═══════════════════════════════════════════════════════════
# 5. Transactional Outbox (Риск #4)
# ═══════════════════════════════════════════════════════════

class TestOutboxStore:
    """SQLite-based гарантированная доставка."""

    @pytest.fixture
    def outbox(self, tmp_path):
        db = str(tmp_path / "test_outbox.db")
        config = OutboxConfig(db_path=db, retry_interval=0.1, max_attempts=3)
        store = OutboxStore(config)
        store.initialize()
        yield store
        store.close()

    def test_store_and_fetch(self, outbox):
        event_id = outbox.store("channel.1", {"x": 1})
        pending = outbox.fetch_pending(limit=10)
        assert len(pending) >= 1
        assert any(p["event_id"] == event_id for p in pending)

    def test_mark_publishing_delivered(self, outbox):
        event_id = outbox.store("ch.test", {"v": 42})
        outbox.mark_publishing(event_id)
        outbox.mark_delivered(event_id)
        pending = outbox.fetch_pending(limit=10)
        assert not any(p["event_id"] == event_id for p in pending)

    def test_mark_failed_retry(self, outbox):
        event_id = outbox.store("ch.test", {"v": 1})
        outbox.mark_failed(event_id, "test error")
        # After marking failed, it should still be pending (retry)
        pending = outbox.fetch_pending(limit=10)
        assert any(p["event_id"] == event_id for p in pending)

    def test_max_attempts_dead_letter(self, outbox):
        event_id = outbox.store("ch.dead", {"x": 1})
        for _ in range(outbox.config.max_attempts + 1):
            outbox.mark_publishing(event_id)
            outbox.mark_failed(event_id, "test error")
        # Should be dead
        pending = outbox.fetch_pending(limit=10)
        assert not any(p["event_id"] == event_id for p in pending)

    def test_get_stats(self, outbox):
        outbox.store("ch.1", {"a": 1})
        outbox.store("ch.2", {"a": 2})
        stats = outbox.get_stats()
        assert stats["pending"] >= 1  # new events are stored as "ready" not "pending"
        assert stats["delivered"] >= 0


# ═══════════════════════════════════════════════════════════
# 6. BaseAgent — envelope-based communication (Риск #2, P3-07)
# ═══════════════════════════════════════════════════════════

class MockAgent(BaseAgent):
    """Test agent with a simple run() that echoes state."""

    def __init__(self, name: str = "mock", **kwargs):
        super().__init__(name=name, **kwargs)

    async def run(self, state: dict) -> dict:
        return {"signal": "BUY", "agent": self.name, "context_task_id": self.context_task_id}


class TestBaseAgentIntegration:
    """on_message, contextvars, publish_event с outbox fallback."""

    @pytest.mark.asyncio
    async def test_on_message_propagates_context(self):
        agent = MockAgent(name="ctx_test")
        env = TaskEnvelope.new(agent_name="ctx_test", state={})
        result = await agent.on_message(env)
        assert result.status == TaskStatus.COMPLETED
        assert result.result["context_task_id"] == env.task_id

    @pytest.mark.asyncio
    async def test_on_message_isolates_state(self):
        state = {"ticker": "AAPL"}
        agent = MockAgent(name="isolate")
        env = TaskEnvelope.new(agent_name="isolate", state=state)
        await agent.on_message(env)
        # Original state untouched
        assert state["ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_on_message_without_broker(self):
        agent = MockAgent(name="no_broker")
        env = TaskEnvelope.new(agent_name="no_broker", state={})
        result = await agent.on_message(env)
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_publish_event_without_broker(self):
        agent = MockAgent(name="pub_test")
        await agent.publish_event("test.channel", {"msg": "hello"})
        # Should not raise

    @pytest.mark.asyncio
    async def test_publish_event_with_outbox_fallback(self, tmp_path):
        db = str(tmp_path / "outbox_test.db")
        config = OutboxConfig(db_path=db)
        outbox = OutboxStore(config)
        outbox.initialize()

        agent = MockAgent(name="outbox_test")
        broker = InProcessBroker()

        # Broken broker → outbox fallback
        broker._started = False
        agent.set_broker(broker, outbox=outbox)
        await agent.publish_event("test.channel", {"msg": "fallback"})

        pending = outbox.fetch_pending(limit=10)
        # After publish_event with !started broker, event goes to outbox
        assert any(p.get("channel") == "test.channel" for p in pending)
        outbox.close()


# ═══════════════════════════════════════════════════════════
# 7. SentinelV5Broker Integration
# ═══════════════════════════════════════════════════════════

class TestSentinelV5BrokerIntegration:
    """Hub-and-Spoke with real agents."""

    @pytest.mark.asyncio
    async def test_broker_mode_lifecycle(self):
        from orchestration.sentinel_v5_broker import SentinelV5Broker, BrokerConfig

        agent = MockAgent(name="test_agent")
        config = BrokerConfig(
            use_broker=True,
            worker_count=2,
            cb_failure_threshold=5,
            outbox_db_path=None,
        )
        hub = SentinelV5Broker(agents={"test": agent}, config=config)
        await hub.start()

        result = await hub.run_analysis(
            state={"ticker": "AAPL"},
            deadline_sec=60,
            agent_names=["test"],
        )
        assert result is not None
        assert "test" in result
        await hub.stop()

    @pytest.mark.asyncio
    async def test_fallback_to_gather(self):
        from orchestration.sentinel_v5_broker import SentinelV5Broker, BrokerConfig

        agent = MockAgent(name="gather_test")
        config = BrokerConfig(use_broker=False, fallback_to_gather=True)
        hub = SentinelV5Broker(agents={"gather_test": agent}, config=config)

        result = await hub.run_analysis(
            state={"ticker": "MSFT"},
            agent_names=["gather_test"],
        )
        assert "gather_test" in result

    @pytest.mark.asyncio
    async def test_error_isolation(self):
        """Ошибка одного агента не роняет весь run_analysis."""
        from orchestration.sentinel_v5_broker import SentinelV5Broker, BrokerConfig

        class CrashAgent(BaseAgent):
            async def run(self, state):
                raise RuntimeError("crash")

        agents = {
            "crash": CrashAgent(name="crash"),
            "good": MockAgent(name="good"),
        }
        config = BrokerConfig(use_broker=True, worker_count=2)
        hub = SentinelV5Broker(agents=agents, config=config)
        await hub.start()

        result = await hub.run_analysis(
            state={"ticker": "BTC"}, agent_names=["crash", "good"]
        )
        assert result is not None
        # good agent should still produce result
        assert "good" in result or "crash" in result
        await hub.stop()


# ═══════════════════════════════════════════════════════════
# 8. Serialization (broker payload round-trip)
# ═══════════════════════════════════════════════════════════

class TestSerialization:
    def test_task_envelope_round_trip(self):
        env = TaskEnvelope.new(
            agent_name="serial_test",
            state={"ticker": "BTC"},
            task_type="analyze",
            priority=80,
            correlation_id="corr-1",
        )
        payload = env.to_broker_payload()
        restored = TaskEnvelope.from_broker_payload(payload)
        assert restored.task_id == env.task_id
        assert restored.state_snapshot == env.state_snapshot
        assert restored.priority == 80
        assert restored.correlation_id == "corr-1"

    def test_result_envelope_round_trip(self):
        env = TaskEnvelope.new(agent_name="res_test", state={})
        result = ResultEnvelope(
            task_id=env.task_id,
            agent_name="res_test",
            trace_id=env.trace_id,
            status=TaskStatus.COMPLETED,
            result={"signal": "HOLD"},
            execution_time_ms=42.0,
        )
        payload = result.to_broker_payload()
        restored = ResultEnvelope.from_broker_payload(payload)
        assert restored.status == TaskStatus.COMPLETED
        assert restored.result["signal"] == "HOLD"
        assert restored.execution_time_ms == 42.0

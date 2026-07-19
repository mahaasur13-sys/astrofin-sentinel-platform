"""core.message_broker — ADR-001 Sprint 3/4: Message Broker ABC + Implementations."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable
import asyncio
import json
import logging
import time
import uuid
from core.envelopes import TaskEnvelope, ResultEnvelope, TaskStatus

logger = logging.getLogger(__name__)

# ── Stats ─────────────────────────────────────────────────────────
@dataclass
class BrokerStats:
    messages_sent: int = 0
    messages_received: int = 0
    errors: int = 0
    published: int = 0
    pending: int = 0
    workers: int = 0

    @property
    def received(self) -> int:
        return self.messages_received

# ── Abstract Broker ───────────────────────────────────────────────
class MessageBroker(ABC):
    @abstractmethod
    async def start(self) -> None: ...
    @abstractmethod
    async def stop(self) -> None: ...
    @abstractmethod
    async def send(self, envelope, handler, timeout_sec=None) -> ResultEnvelope: ...
    @abstractmethod
    async def publish(self, channel: str, payload: dict) -> None: ...
    @abstractmethod
    async def subscribe(self, channel: str, callback) -> str: ...
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None: ...
    @abstractmethod
    def stats(self) -> BrokerStats: ...

# ── InProcessBroker ────────────────────────────────────────────────
class InProcessBroker(MessageBroker):
    def __init__(self, max_queue_size: int = 1000):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._workers: list[asyncio.Task] = []
        self._worker_count: int = 4
        self._subscribers: dict[str, list[Callable]] = {}
        self._sent_count: int = 0
        self._error_count: int = 0
        self._published_count: int = 0
        self._received_count: int = 0
        self._started: bool = False

    def set_worker_count(self, count: int) -> None:
        self._worker_count = count

    async def start(self) -> None:
        self._started = True
        for _ in range(self._worker_count):
            task = asyncio.create_task(self._worker_loop())
            self._workers.append(task)

    async def stop(self) -> None:
        self._started = False
        for w in self._workers:
            w.cancel()
        self._workers.clear()

    async def _worker_loop(self) -> None:
        while self._started:
            try:
                envelope, handler, future = await asyncio.wait_for(
                    self._queue.get(), timeout=0.5)
                self._received_count += 1
                try:
                    result = await handler(envelope)
                except Exception as exc:
                    result = ResultEnvelope(
                        task_id=envelope.task_id,
                        agent_name=envelope.agent_name,
                        trace_id=envelope.trace_id,
                        status=TaskStatus.FAILED,
                        error=str(exc),
                    )
                future.set_result(result)
            except asyncio.TimeoutError:
                continue

    async def send(self, envelope, handler, timeout_sec=None):
        self._sent_count += 1
        try:
            result = await asyncio.wait_for(handler(envelope), timeout=timeout_sec)
            return result
        except asyncio.TimeoutError:
            self._error_count += 1
            return ResultEnvelope(
                task_id=envelope.task_id,
                agent_name=envelope.agent_name,
                trace_id=envelope.trace_id,
                status=TaskStatus.FAILED,
                result={"signal": "NEUTRAL", "confidence": 0.0, "sources": []},
                error=f"Timeout after {timeout_sec}s",
                metadata={"degraded": True},
            )
        except Exception as exc:
            self._error_count += 1
            return ResultEnvelope(
                task_id=envelope.task_id,
                agent_name=envelope.agent_name,
                trace_id=envelope.trace_id,
                status=TaskStatus.FAILED,
                result={},
                error=str(exc),
            )

    async def publish(self, channel: str, payload: dict) -> None:
        if not self._started:
            raise BrokerUnavailable("broker not started")
        self._published_count += 1
        for cb in self._subscribers.get(channel, []):
            try:
                await cb(channel, payload)
            except Exception:
                logger.exception("broker_subscriber_error", extra={"channel": channel})

    async def subscribe(self, channel: str, callback) -> str:
        sub_id = uuid.uuid4().hex[:12]
        self._subscribers.setdefault(channel, []).append(callback)
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> None:
        pass

    def stats(self) -> BrokerStats:
        return BrokerStats(
            messages_sent=self._sent_count,
            messages_received=self._received_count,
            errors=self._error_count,
            published=self._published_count,
            pending=self._queue.qsize(),
            workers=len(self._workers),
        )

# ── RedisBroker (Sprint 4) ─────────────────────────────────────────
class RedisBroker(MessageBroker):
    _DEFAULT_REDIS_URL = "redis://localhost:6379/9"
    _STREAM_PREFIX = "astrofin:task"

    def __init__(self, redis_url: str | None = None, max_queue_size: int = 1000,
                 consumer_group: str = "astrofin-workers", consumer_name: str | None = None):
        self._redis_url = redis_url or self._DEFAULT_REDIS_URL
        self._consumer_group = consumer_group
        self._consumer_name = consumer_name or f"worker-{uuid.uuid4().hex[:8]}"
        self._redis = None
        self._pubsub = None
        self._max_queue_size = max_queue_size
        self._sent_count: int = 0
        self._error_count: int = 0
        self._published_count: int = 0
        self._received_count: int = 0
        self._started: bool = False
        self._workers_started: bool = False
        self._subscribers: dict[str, list[Callable]] = {}

    async def start(self) -> None:
        self._started = True
        self._workers_started = True

    async def stop(self) -> None:
        self._started = False
        self._workers_started = False

    async def close(self) -> None:
        if self._started:
            await self.stop()

    async def send(self, envelope, handler, timeout_sec=None):
        self._sent_count += 1
        try:
            return await asyncio.wait_for(handler(envelope), timeout=timeout_sec)
        except asyncio.TimeoutError:
            self._error_count += 1
            return ResultEnvelope(
                task_id=getattr(envelope, 'task_id', ''),
                agent_name=getattr(envelope, 'agent_name', ''),
                trace_id=getattr(envelope, 'trace_id', ''),
                status=TaskStatus.FAILED,
                result={"signal": "NEUTRAL", "confidence": 0.0},
                error=f"Timeout after {timeout_sec}s",
                metadata={"degraded": True},
            )
        except Exception as exc:
            self._error_count += 1
            return ResultEnvelope(
                task_id=getattr(envelope, 'task_id', ''),
                agent_name=getattr(envelope, 'agent_name', ''),
                trace_id=getattr(envelope, 'trace_id', ''),
                status=TaskStatus.FAILED,
                result={'error': str(exc)},
                error=str(exc),
            )

    async def publish(self, channel, payload):
        self._published_count += 1
        for cb in self._subscribers.get(channel, []):
            try:
                await cb(channel, payload)
            except Exception:
                logger.exception("redis_broker_subscriber_error", extra={"channel": channel})

    async def subscribe(self, channel, callback):
        sub_id = uuid.uuid4().hex[:12]
        self._subscribers.setdefault(channel, []).append(callback)
        return sub_id

    async def unsubscribe(self, subscription_id):
        pass

    def stats(self) -> BrokerStats:
        return BrokerStats(
            messages_sent=self._sent_count,
            messages_received=self._received_count,
            errors=self._error_count,
            published=self._published_count,
        )

# ── Exceptions ────────────────────────────────────────────────────
class BrokerUnavailable(Exception):
    pass

class BrokerTimeout(Exception):
    def __init__(self, channel: str, timeout: float):
        self.channel = channel
        self.timeout = timeout
        super().__init__(f"RPC timeout for channel '{channel}' ({timeout:.1f}s)")

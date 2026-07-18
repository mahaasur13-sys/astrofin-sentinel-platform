"""
core.message_broker — ADR-001 Sprint 3/4: Message Broker ABC + Implementations.

Sprint 3: InProcessBroker (backward compat)
Sprint 4: RedisBroker (cross-process, horizontal scaling)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from core.envelopes import TaskEnvelope, ResultEnvelope

logger = logging.getLogger(__name__)


# ── Broker Stats ──────────────────────────────────────────────────

@dataclass
class BrokerStats:
    messages_sent: int = 0
    messages_received: int = 0
    errors: int = 0
    published: int = 0
    pending: int = 0
    workers: int = 0


# ── Abstract Broker ───────────────────────────────────────────────

class MessageBroker(ABC):
    """Абстрактный интерфейс MessageBroker для Hub-and-Spoke."""

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def send(
        self,
        envelope: TaskEnvelope,
        handler: Callable[[TaskEnvelope], Awaitable[ResultEnvelope]],
        timeout_sec: float | None = None,
    ) -> ResultEnvelope: ...

    @abstractmethod
    async def publish(self, channel: str, payload: dict) -> None: ...

    @abstractmethod
    async def subscribe(
        self, channel: str, callback: Callable[[str, dict], Awaitable[None]]
    ) -> str: ...

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None: ...

    @abstractmethod
    def stats(self) -> BrokerStats: ...


# ── InProcessBroker ───────────────────────────────────────────────

class InProcessBroker(MessageBroker):
    """Локальный брокер: asyncio.Queue worker pool + in-memory pub/sub."""

    def __init__(self, max_queue_size: int = 1000):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._workers: list[asyncio.Task] = []
        self._worker_count: int = 4
        self._subscribers: dict[str, list[Callable]] = {}
        self._sent_count: int = 0
        self._error_count: int = 0
        self._published_count: int = 0
        self._received_count: int = 0
        self._started: bool = True

    def set_worker_count(self, count: int) -> None:
        self._worker_count = count

    async def start(self) -> None:
        for _ in range(self._worker_count):
            self._workers.append(asyncio.create_task(self._worker_loop()))

    async def stop(self) -> None:
        for w in self._workers:
            w.cancel()
        self._workers.clear()

    async def send(
        self,
        envelope: TaskEnvelope,
        handler: Callable[[TaskEnvelope], Awaitable[ResultEnvelope]],
        timeout_sec: float | None = None,
    ) -> ResultEnvelope:
        self._sent_count += 1
        try:
            result = await asyncio.wait_for(handler(envelope), timeout=timeout_sec)
            return result
        except Exception as exc:
            self._error_count += 1
            from core.envelopes import ResultEnvelope, TaskStatus
            return ResultEnvelope(
                task_id=envelope.task_id,
                agent_name=envelope.agent_name,
                trace_id=envelope.trace_id,
                status=TaskStatus.FAILED,
                result={},
                error=str(exc),
            )
        except asyncio.TimeoutError:
            self._error_count += 1
            from core.envelopes import ResultEnvelope
            return ResultEnvelope(
                task_id=envelope.task_id,
                agent_name=envelope.agent_name,
                trace_id=envelope.trace_id,
                status="FAILED",
                result={"signal": "NEUTRAL", "confidence": 0.0, "sources": []},
                error=f"Timeout after {timeout_sec}s",
                metadata={"degraded": True},
            )

    async def publish(self, channel: str, payload: dict) -> None:
        if not self._started:
            raise BrokerUnavailable("broker not started")
        self._published_count += 1
        callbacks = self._subscribers.get(channel, [])
        for cb in callbacks:
            try:
                await cb(channel, payload)
            except Exception:
                logger.exception("broker_subscriber_error", extra={"channel": channel})

    async def subscribe(
        self, channel: str, callback: Callable[[str, dict], Awaitable[None]]
    ) -> str:
        sub_id = uuid.uuid4().hex[:12]
        self._subscribers.setdefault(channel, []).append(callback)
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> None:
        pass  # simplified — stored by ref, not id

    def stats(self) -> BrokerStats:
        return BrokerStats(
            messages_sent=self._sent_count,
            messages_received=self._received_count,
            errors=self._error_count,
            published=self._published_count,
            pending=self._queue.qsize(),
            workers=len(self._workers),
        )

    async def _worker_loop(self) -> None:
        while True:
            try:
                item = await self._queue.get()
                envelope, handler, future = item
                try:
                    result = await handler(envelope)
                    future.set_result(result)
                except Exception:
                    future.set_exception(asyncio.CancelledError())
            except asyncio.CancelledError:
                break


# ── RedisBroker (Sprint 4 stub) ───────────────────────────────────

    async def close(self) -> None:
        await self.stop()


class RedisBroker(MessageBroker):
    """Redis-based broker — stub for Sprint 4."""

    def __init__(self, max_queue_size: int = 1000):
        self._sent_count: int = 0
        self._error_count: int = 0
        self._published_count: int = 0

    async def start(self) -> None:
        self._started = True
        self._workers_started = True

    async def stop(self) -> None:
        pass

    async def send(self, envelope, handler, timeout_sec=None):
        self._sent_count += 1
        return await handler(envelope)

    async def publish(self, channel, payload):
        self._published_count += 1

    async def subscribe(self, channel, callback):
        return "redis-stub-sub"

    async def unsubscribe(self, subscription_id):
        pass

    def stats(self) -> BrokerStats:
        return BrokerStats(
            messages_sent=self._sent_count,
            errors=self._error_count,
            published=self._published_count,
        )


# ── Exceptions ────────────────────────────────────────────────────

class BrokerUnavailable(Exception):
    """Брокер недоступен."""

class BrokerTimeout(Exception):
    def __init__(self, channel: str, timeout: float):
        self.channel = channel
        self.timeout = timeout
        super().__init__(f"RPC timeout for channel '{channel}' ({timeout:.1f}s)")

"""
Redis Streams-backed durable task queue.

Design:
- XADD writes task to stream
- XREADGROUP (consumer group) provides at-least-once delivery
- Pending Entry List (PEL) tracks unacknowledged messages → auto-recover on crash
- XACK acknowledges after successful processing
- XTRIM trims stream to keep it bounded

Keys:
  agent:tasks           — Redis Stream (source of truth)
  task_state:<task_id>   — Task state hash (set by task_state.py)
  result:<task_id>       — Result payload (TTL = 3600s)

Consumer groups provide:
  - At-least-once delivery (message redelivered if not XACKed)
  - Pending Entry List (PEL) auto-recovery when worker crashes
  - Multiple concurrent workers with load balancing
"""

from __future__ import annotations

import asyncio
import json
import signal
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import redis.asyncio as aioredis
from agent_runtime.task_store import TaskStore

STREAM_KEY = "agent:tasks"


class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


STREAM_CONSUMER_GROUP = "agent-workers"
STREAM_CONSUMER_NAME_PREFIX = "worker-"
STREAM_MAX_LEN = 10_000


@dataclass
class QueuedTask:
    task_id: str
    payload: dict
    priority: int = 1
    enqueued_at: float = field(default_factory=time.time)
    stream_id: str = ""  # Redis Stream message ID


class DurableTaskQueue:
    """
    Redis Streams-based durable task queue.

    Guarantees:
    - At-least-once delivery via consumer groups + PEL
    - Crash recovery via Pending Entry List (PEL) scan on startup
    - Deduplication via task_id in payload
    - Graceful shutdown (finish in-flight tasks before exit)
    - Configurable concurrency per worker
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        stream_key: str = STREAM_KEY,
        consumer_group: str = STREAM_CONSUMER_GROUP,
        max_stream_len: int = STREAM_MAX_LEN,
        claim_stale_timeout: int = 60,
        batch_size: int = 10,
        block_ms: int = 5000,
    ):
        self._redis: aioredis.Redis | None = None
        self._redis_url = redis_url
        self._stream_key = stream_key
        self._consumer_group = consumer_group
        self._max_stream_len = max_stream_len
        self._claim_stale_timeout = claim_stale_timeout
        self._batch_size = batch_size
        self._block_ms = block_ms

        # Per-worker state
        self._worker_id: str = ""
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Shared components
        self._state_machine: TaskStore | None = None

    # ── redis connection ──────────────────────────────────────────────────────

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                max_connections=32,
            )
        return self._redis

    async def _get_state_machine(self) -> TaskStore:
        if self._state_machine is None:
            self._state_machine = TaskStore(self._redis_url)
        return self._state_machine

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def start(self, worker_id: str | None = None) -> None:
        """Initialize worker: register consumer group, recover stale tasks."""
        r = await self._get_redis()
        self._worker_id = worker_id or f"{STREAM_CONSUMER_NAME_PREFIX}{uuid.uuid4().hex[:8]}"
        self._running = True

        # Ensure consumer group exists (idempotent)
        try:
            await r.xgroup_create(
                self._stream_key,
                self._consumer_group,
                id="0",
                mkstream=True,
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Recover stale tasks (crashed workers)
        sm = await self._get_state_machine()
        recovered = await sm.recover_stale_tasks(self._worker_id)
        if recovered:
            print(f"[{self._worker_id}] Recovered {recovered} stale tasks from crashed workers")

        print(f"[{self._worker_id}] DurableTaskQueue started")

    async def stop(self) -> None:
        """Initiate graceful shutdown: stop accepting, finish in-flight."""
        print(f"[{self._worker_id}] Initiating graceful shutdown...")
        self._running = False
        self._shutdown_event.set()

    # ── enqueue ───────────────────────────────────────────────────────────────

    async def enqueue(
        self,
        payload: dict,
        task_id: str | None = None,
        priority: int = 1,
    ) -> str:
        """
        Add task to stream.
        Returns task_id.
        Deduplication: if task_id already exists in stream payload, skips.
        """
        task_id = task_id or uuid.uuid4().hex
        r = await self._get_redis()

        # XADD with MAXLEN to keep stream bounded
        await r.xadd(
            self._stream_key,
            {
                "task_id": task_id,
                "payload": json.dumps(payload),
                "priority": str(priority),
                "enqueued_at": str(time.time()),
            },
            max_len=self._max_stream_len,
            approximate=True,
        )

        return task_id

    # ── consume loop ─────────────────────────────────────────────────────────

    async def consume(
        self,
        handler: Callable[[QueuedTask], Any],
        concurrency: int = 4,
    ) -> None:
        """
        Main consume loop.
        Uses XREADGROUP to read from consumer group.
        Handles graceful shutdown via self._shutdown_event.
        """
        r = await self._get_redis()
        pending_ids: set[str] = set()  # track in-flight task IDs for graceful shutdown

        print(f"[{self._worker_id}] Starting consume loop (concurrency={concurrency})")

        while self._running:
            # Step 1: Try to claim pending messages (from crashed workers)
            await self._reclaim_pending(r)

            # Step 2: Read new messages
            try:
                results = await r.xreadgroup(
                    groupname=self._consumer_group,
                    consumername=self._worker_id,
                    streams={self._stream_key: ">"},
                    count=self._batch_size,
                    block=self._block_ms,
                )
            except aioredis.ResponseError:
                # Group might not exist yet (race on start)
                await asyncio.sleep(1)
                continue

            if not results:
                continue

            for stream_name, messages in results:
                for stream_id, fields in messages:
                    task_id = fields.get("task_id", "")
                    priority = int(fields.get("priority", "1"))
                    enqueued_at = float(fields.get("enqueued_at", "0"))

                    try:
                        payload = json.loads(fields.get("payload", "{}"))
                    except json.JSONDecodeError:
                        payload = {"raw": fields.get("payload", "")}

                    task = QueuedTask(
                        task_id=task_id,
                        payload=payload,
                        priority=priority,
                        enqueued_at=enqueued_at,
                        stream_id=stream_id,
                    )

                    pending_ids.add(stream_id)

                    try:
                        await self._process_task(handler, task)
                    except Exception as e:
                        print(f"[{self._worker_id}] Task {task_id} failed: {e}")

                    # Acknowledge (remove from PEL)
                    await r.xack(self._stream_key, self._consumer_group, stream_id)
                    pending_ids.discard(stream_id)

        # Graceful shutdown: wait for in-flight to complete
        print(f"[{self._worker_id}] Waiting for {len(pending_ids)} in-flight tasks...")
        while pending_ids:
            await asyncio.sleep(0.5)

        print(f"[{self._worker_id}] Consume loop stopped")

    async def _reclaim_pending(self, r: aioredis.Redis) -> None:
        """
        Find pending messages (delivered but not XACKed) and re-claim them.
        Uses XPENDING + XCLAIM to take ownership of stale messages.
        """
        try:
            pending = await r.xpending_range(
                self._stream_key,
                self._consumer_group,
                min="-",
                max="+",
                count=100,
            )
        except aioredis.ResponseError:
            return

        for entry in pending:
            # entry: (message_id, consumer, time_since_delivered, times_delivered)
            msg_id, consumer_name, idle_time_ms, times_delivered = entry

            if idle_time_ms >= self._claim_stale_timeout * 1000:
                # Stale message — claim it
                try:
                    await r.xclaim(
                        self._stream_key,
                        self._consumer_group,
                        self._worker_id,
                        min_idle_time=self._claim_stale_timeout * 1000,
                        message_ids=[msg_id],
                    )
                except aioredis.ResponseError:
                    pass

    async def _process_task(
        self,
        handler: Callable[[QueuedTask], Any],
        task: QueuedTask,
    ) -> Any:
        """Process a single task with state machine integration."""
        sm = await self._get_state_machine()

        # Record current worker as the processor
        record = await sm.claim_task(task.task_id, self._worker_id)
        if record is None:
            # Task was already claimed by another worker
            return None

        try:
            result = await handler(task)

            await sm.complete_task(task.task_id, self._worker_id, {"result": result})
            return result
        except Exception as e:
            await sm.fail_task(task.task_id, self._worker_id, str(e))
            raise

    # ── batch enqueue ─────────────────────────────────────────────────────────

    async def enqueue_batch(self, tasks: list[dict]) -> list[str]:
        """Enqueue multiple tasks atomically via Redis pipeline."""
        r = await self._get_redis()
        pipe = r.pipeline()
        task_ids = []

        for payload in tasks:
            task_id = uuid.uuid4().hex
            task_ids.append(task_id)
            pipe.xadd(
                self._stream_key,
                {
                    "task_id": task_id,
                    "payload": json.dumps(payload),
                    "priority": "1",
                    "enqueued_at": str(time.time()),
                },
                max_len=self._max_stream_len,
                approximate=True,
            )

        await pipe.execute()
        return task_ids

    # ── queue stats ──────────────────────────────────────────────────────────

    async def queue_stats(self) -> dict:
        """Stream length, consumer group info, pending count."""
        r = await self._get_redis()
        stream_len = await r.xlen(self._stream_key)

        try:
            group_info = await r.xinfo_groups(self._stream_key)
            consumer_count = len(group_info)
            pending_count = sum(g.get("pending", 0) for g in group_info)
        except aioredis.ResponseError:
            consumer_count = 0
            pending_count = 0
            group_info = []

        return {
            "stream_length": stream_len,
            "consumer_group": self._consumer_group,
            "consumer_count": consumer_count,
            "pending_count": pending_count,
            "worker_id": self._worker_id,
        }

    # ── graceful shutdown helper ───────────────────────────────────────────────

    def setup_signal_handlers(self) -> None:
        """Setup SIGTERM/SIGINT handlers for graceful shutdown."""
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
            except NotImplementedError:
                # Windows: signals not supported
                pass

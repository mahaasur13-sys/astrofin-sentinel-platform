"""
Async execution engine v2 — no threadpool bottleneck.

Changes from v1:
- Removed: run_in_executor(engine.run)
- Added: direct async engine.run() call
- Added: backpressure guard (queue depth monitoring)
- Added: cancellation support via Redis flags
- Added: worker saturation detection
- Added: concurrent message processing (batch=1..N)
"""

from __future__ import annotations

import asyncio
import json
import os
import traceback

import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectError

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STREAM_KEY = "agent:stream"
CONSUMER_GROUP = "agent-workers"
CONSUMER_NAME = os.getenv("HOSTNAME", "worker-1")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "4"))
QUEUE_DEPTH_LIMIT = int(os.getenv("QUEUE_DEPTH_LIMIT", "1000"))

# ── async redis ───────────────────────────────────────────────────────────────

_async_r: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _async_r
    if _async_r is None:
        _async_r = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _async_r


# ── backpressure guard ────────────────────────────────────────────────────────

async def queue_depth() -> int:
    """Current pending messages in stream (not yet ACKed)."""
    r = await _get_redis()
    try:
        info = await r.xinfo_groups(STREAM_KEY)
        # sum of lag across all consumers in group
        total = 0
        for group in info:
            total += group.get("lag", 0) or 0
        return max(0, total)
    except Exception:
        # fallback: len of stream
        try:
            return await r.xlen(STREAM_KEY)
        except Exception:
            return 0


async def is_queue_saturated() -> bool:
    """True if pending tasks exceed limit → reject new enqueue."""
    depth = await queue_depth()
    return depth >= QUEUE_DEPTH_LIMIT


# ── cancellation support ───────────────────────────────────────────────────────

async def _is_task_cancelled(task_id: str) -> bool:
    """Check if task has been externally cancelled."""
    r = await _get_redis()
    flag = await r.get(f"cancel:{task_id}")
    return flag == "1"


# ── queue ─────────────────────────────────────────────────────────────────────

async def enqueue(task_id: str, task_payload: dict) -> bool:
    """
    Add a task to the Redis stream.
    Returns False if queue is saturated (backpressure).
    """
    if await is_queue_saturated():
        return False  # backpressure — caller should handle retry/delay

    try:
        r = await _get_redis()
        await r.xadd(STREAM_KEY, {
            "task_id": task_id,
            "payload": json.dumps(task_payload),
        })
        return True
    except RedisConnectError:
        return False


async def revoke_task(task_id: str) -> bool:
    """Mark a running task for cancellation (best-effort)."""
    try:
        r = await _get_redis()
        await r.set(f"cancel:{task_id}", "1", ex=3600)
        return True
    except Exception:
        return False


async def setup_stream():
    """Create consumer group if it doesn't exist (idempotent)."""
    r = await _get_redis()
    try:
        await r.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except Exception:
        pass  # group already exists


# ── per-message processing (truly async, no threadpool) ───────────────────────

async def process_message(message_id: str, data: dict) -> None:
    """Process one stream message — fully async, no executor."""
    task_id = data["task_id"]
    payload = json.loads(data["payload"])

    worker_id = CONSUMER_NAME
    store = await _get_task_store()

    # honour cancellation flag before starting
    if await _is_task_cancelled(task_id):
        await store.cancel_task(task_id, worker_id)
        return

    # claim — единая точка входа для state
    record = await store.claim_task(task_id, worker_id)
    if not record:
        await store.record_metric(task_id, "epoch_mismatches")
        return  # already claimed or not PENDING

    await store.record_metric(task_id, "claims")
    claimed_epoch = record.epoch

    # EventStore: emit TASK_CLAIMED
    event_store = await _get_event_store()
    await event_store.append(
        task_id,
        TaskEvent.make(
            task_id=task_id,
            event_type=EventType.TASK_CLAIMED,
            worker_id=worker_id,
            epoch=claimed_epoch,
            lamport_ts=0,
        ),
    )

    from .engine import run as engine_run
    try:
        result = await engine_run(
            task=payload.get("task", ""),
            context=payload.get("context"),
        )

        # check cancellation one more time before storing
        if await _is_task_cancelled(task_id):
            await store.cancel_task(task_id, worker_id)
            return

        await store.complete_task(task_id, worker_id, result)
        await store.record_metric(task_id, "completions")

        # EventStore: emit TASK_COMPLETED
        await event_store.append_task_completed(task_id, claimed_epoch, worker_id, result)

    except Exception as exc:
        tb = traceback.format_exc()
        error_msg = f"{type(exc).__name__}: {exc}\n{tb}"
        fail_ok = await store.fail_task(task_id, worker_id, error_msg)
        if fail_ok:
            # check resulting state: PENDING means retry, FAILED means exhausted
            rec = await store.get_task(task_id)
            if rec and rec.state == TaskState.PENDING:
                await store.record_metric(task_id, "retries")
                # EventStore: emit TASK_RETRIED
                await event_store.append_task_retried(
                    task_id, claimed_epoch, worker_id, rec.epoch,
                )
            else:
                await store.record_metric(task_id, "failures")
                # EventStore: emit TASK_FAILED
                await event_store.append_task_failed(task_id, claimed_epoch, worker_id, error_msg)


# ── concurrent worker loop (semaphore-bounded) ───────────────────────────────

async def worker_loop():
    """
    Infinite consumer loop with controlled concurrency.
    Uses asyncio.Semaphore to bound parallel in-flight tasks.

    Run as: asyncio.create_task(worker_loop())
    """
    await setup_stream()
    r = await _get_redis()
    semaphore = asyncio.Semaphore(WORKER_CONCURRENCY)

    async def bounded_process(message_id: str, data: dict):
        async with semaphore:
            try:
                await process_message(message_id, data)
            finally:
                await r.xack(STREAM_KEY, CONSUMER_GROUP, message_id)

    while True:
        try:
            # batch of messages up to WORKER_CONCURRENCY
            messages = await r.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                {STREAM_KEY: ">"},
                count=WORKER_CONCURRENCY,
                block=5000,
            )
            if not messages:
                continue

            for stream_name, entries in messages:
                for message_id, data in entries:
                    # fire-and-forget per-message, bounded by semaphore
                    asyncio.create_task(bounded_process(message_id, data))
                    # do NOT ack here — ack after processing in bounded_process

        except RedisConnectError:
            await asyncio.sleep(5)
        except Exception:
            await asyncio.sleep(1)


_task_store: TaskStore | None = None


async def _get_task_store() -> TaskStore:
    global _task_store
    if _task_store is None:
        from .task_store import TaskStore
        _task_store = TaskStore(REDIS_URL)
    return _task_store


_event_store: EventStore | None = None


async def _get_event_store() -> EventStore:
    global _event_store
    if _event_store is None:
        from .event_store import EventStore
        _event_store = EventStore(REDIS_URL)
    return _event_store

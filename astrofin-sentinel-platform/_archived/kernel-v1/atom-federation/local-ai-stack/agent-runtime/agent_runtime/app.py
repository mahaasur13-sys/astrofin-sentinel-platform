"""
FastAPI entry point v3 — Durable Redis Streams + Structured Logging.

Changes from v2:
- Replaces in-memory AdaptiveScheduler with DurableTaskQueue (Redis Streams)
- Adds structured JSON logging with trace_id correlation
- Graceful shutdown (SIGTERM/SIGINT → finish in-flight, then exit)
- /metrics endpoint for Prometheus scraping
- Health endpoints: /health (liveness) + /health/ready (readiness)
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager

import uvicorn
from agent_runtime.config import settings
from agent_runtime.durable_queue import DurableTaskQueue, QueuedTask
from agent_runtime.resilience import CircuitBreakerRegistry, CircuitState
from agent_runtime.task_store import TaskState, TaskStore
from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel

# ── structured JSON logging ─────────────────────────────────────────────────

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == "json":
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    logger.addHandler(handler)


setup_logging()
log = logging.getLogger("agent_runtime.app")


# ── globals ─────────────────────────────────────────────────────────────────

_durable_queue: DurableTaskQueue | None = None
_worker_task: asyncio.Task | None = None
_shutdown_event = asyncio.Event()
_task_store: TaskStore | None = None


async def _get_task_store() -> TaskStore:
    global _task_store
    if _task_store is None:
        _task_store = TaskStore(settings.REDIS_URL)
    return _task_store


# ── task handler ─────────────────────────────────────────────────────────────

async def handle_task(task: QueuedTask) -> dict:
    """Process a single task: plan → execute → record result."""
    from agent_runtime.engine import run as engine_run

    task_id = task.task_id
    payload = task.payload
    trace_id = payload.get("_trace_id", task_id[:8])

    log.info("Processing task", extra={"task_id": task_id, "trace_id": trace_id})

    try:
        result = await engine_run(
            task=payload.get("task", ""),
            context={"task_id": task_id, "trace_id": trace_id},
        )
        log.info("Task completed", extra={"task_id": task_id, "trace_id": trace_id})
        return result
    except asyncio.CancelledError:
        log.warning("Task cancelled", extra={"task_id": task_id, "trace_id": trace_id})
        raise
    except Exception as exc:
        log.error(f"Task failed: {exc}", extra={"task_id": task_id, "trace_id": trace_id})
        raise


# ── lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _durable_queue, _worker_task

    # ── startup ──────────────────────────────────────────────────────────
    log.info("Starting agent-runtime v3...")

    queue = DurableTaskQueue(
        redis_url=settings.REDIS_URL,
        stream_key=settings.REDIS_STREAM_KEY,
        consumer_group=settings.REDIS_CONSUMER_GROUP,
    )

    await queue.start(worker_id=settings.REDIS_CONSUMER_NAME)

    _durable_queue = queue

    # Start worker loop as background task
    _worker_task = asyncio.create_task(
        queue.consume(handler=handle_task, concurrency=settings.API_WORKER_CONCURRENCY)
    )

    log.info(
        "Worker loop started",
        extra={"worker_id": settings.REDIS_CONSUMER_NAME, "concurrency": settings.API_WORKER_CONCURRENCY},
    )

    yield  # ── shutdown ───────────────────────────────────────────────────

    log.info("Initiating graceful shutdown...")

    if _durable_queue:
        await _durable_queue.stop()

    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass

    log.info("Graceful shutdown complete")
    sys.exit(0)


# ── models ───────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    task: str
    context: dict | None = None
    max_retries: int = 3
    priority: int = 1


class TaskSubmitResponse(BaseModel):
    task_id: str
    state: str
    trace_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    created_at: float
    updated_at: float
    retry_count: int
    max_retries: int
    error: str | None
    result: dict | None


class QueueStatsResponse(BaseModel):
    stream_length: int
    consumer_group: str
    consumer_count: int
    pending_count: int
    worker_id: str


# ── app ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agent Runtime v3",
    description="Durable Redis Streams task queue with graceful shutdown",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)


# ── health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def liveness():
    """Liveness probe — am I alive?"""
    return {"status": "ok", "service": "agent-runtime"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe — are dependencies available?"""
    import redis.asyncio as aioredis
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        await r.aclose()
        return {"status": "ready", "redis": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {e}")


# ── tasks ────────────────────────────────────────────────────────────────────

@app.post("/task", response_model=TaskSubmitResponse)
async def submit_task(body: TaskCreate):
    """
    Non-blocking task submission.
    Enqueues via Redis Streams, returns task_id immediately.
    """
    if _durable_queue is None:
        raise HTTPException(status_code=503, detail="Queue not initialized")

    trace_id = uuid.uuid4().hex[:8]
    payload = {
        "task": body.task,
        "context": body.context or {},
        "_trace_id": trace_id,
        "_created_at": time.time(),
    }

    task_id = await _durable_queue.enqueue(
        payload=payload,
        priority=body.priority,
    )

    log.info("Task submitted", extra={"task_id": task_id, "trace_id": trace_id})

    return TaskSubmitResponse(
        task_id=task_id,
        state=TaskState.PENDING.value,
        trace_id=trace_id,
    )


@app.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get current task state and result if available."""
    store = await _get_task_store()
    record = await store.get_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")

    result = await store.get_result(task_id)

    return TaskStatusResponse(
        task_id=record.task_id,
        state=record.state.value,
        created_at=record.enqueued_at,
        updated_at=record.finished_at or record.started_at or record.enqueued_at,
        retry_count=record.attempt,
        max_retries=record.max_attempts,
        error=record.error,
        result=result,
    )


@app.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """
    Best-effort cancellation — sets cancel flag.
    If task is PENDING → it will be skipped.
    If task is RUNNING → worker checks flag between steps.
    """
    store = await _get_task_store()
    record = await store.get_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")

    import redis.asyncio as aioredis
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await r.set(f"cancel:{task_id}", "1", ex=3600)
    await r.aclose()

    log.info("Cancel requested", extra={"task_id": task_id})
    return {"task_id": task_id, "cancel_requested": True}


# ── observability ──────────────────────────────────────────────────────────────

@app.get("/queue/stats", response_model=QueueStatsResponse)
async def get_queue_stats():
    """Queue depth, consumer group info, pending count."""
    if _durable_queue is None:
        raise HTTPException(status_code=503, detail="Queue not initialized")
    stats = await _durable_queue.queue_stats()
    return QueueStatsResponse(**stats)


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    if _durable_queue is None:
        return {"error": "queue not ready"}

    stats = await _durable_queue.queue_stats()
    cb_registry = get_cb_registry()

    cb_lines = []
    for name in ("ollama", "redis", "qdrant"):
        cb = cb_registry.get(name)
        status = await cb.get_status()
        cb_lines.extend([
            '# HELP circuit_breaker_state Circuit breaker state (0=closed, 1=open, 2=half_open)',
            '# TYPE circuit_breaker_state gauge',
            f'circuit_breaker_state{{name="{name}"}} {1 if status["state"] == "open" else 2 if status["state"] == "half_open" else 0}',
            '# HELP circuit_breaker_failures Current failure count',
            '# TYPE circuit_breaker_failures gauge',
            f'circuit_breaker_failures{{name="{name}"}} {status["failures"]}',
        ])

    metrics_text = "\n".join([
        "# HELP agent_queue_depth Current number of tasks in stream",
        "# TYPE agent_queue_depth gauge",
        f'agent_queue_depth{{consumer_group="{stats["consumer_group"]}"}} {stats["stream_length"]}',
        "# HELP agent_pending_count Tasks pending (delivered but not ACKed)",
        "# TYPE agent_pending_count gauge",
        f'agent_pending_count{{consumer_group="{stats["consumer_group"]}"}} {stats["pending_count"]}',
        "# HELP agent_worker_count Active consumers in group",
        "# TYPE agent_worker_count gauge",
        f'agent_worker_count{{consumer_group="{stats["consumer_group"]}"}} {stats["consumer_count"]}',
    ] + cb_lines)

    return ORJSONResponse(
        content=metrics_text,
        media_type="text/plain",
    )


# ── circuit breaker registry (singleton) ───────────────────────────────────────

_cb_registry: CircuitBreakerRegistry | None = None

def get_cb_registry() -> CircuitBreakerRegistry:
    global _cb_registry
    if _cb_registry is None:
        _cb_registry = CircuitBreakerRegistry(settings.REDIS_URL)
    return _cb_registry


@app.get("/circuit-breakers")
async def get_circuit_breakers():
    """Status of all circuit breakers (Ollama, Redis, Qdrant)."""
    registry = get_cb_registry()
    # Ensure all known dependencies are initialized
    for name in ("ollama", "redis", "qdrant"):
        registry.get(name)
    return {"circuit_breakers": registry.get_all_statuses()}


@app.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str):
    """Manually reset a circuit breaker to CLOSED state."""
    registry = get_cb_registry()
    cb = registry.get(name)
    await cb._reset_failures()
    await cb._set_state(CircuitState.CLOSED)
    return {"circuit": name, "state": "closed", "message": "Circuit manually reset"}


@app.get("/circuit-breakers/{name}")
async def get_circuit_breaker(name: str):
    """Status of a specific circuit breaker."""
    registry = get_cb_registry()
    cb = registry.get(name)
    return cb.get_status()


if __name__ == "__main__":
    uvicorn.run(
        "agent_runtime.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
    )

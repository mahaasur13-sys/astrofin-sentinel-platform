"""
Async execution engine v3 — Execution Intelligence Layer.

Integrates:
- DAGRecorder: step-level execution tracing
- AdaptiveScheduler: priority-aware scheduling
- HardCancellation: forced subprocess termination
- full async (aiohttp + subprocess + gather + semaphore)
"""

from __future__ import annotations

import asyncio
import json
import os
import traceback

import aiohttp

from .cancellation import CancellationStrength, HardCancellation
from .dag_recorder import DAGRecorder, StepStatus
from .event_sourcing import EventType, TaskEvent
from .event_store import EventStore
from .resilience import (

import logging
log = logging.getLogger(__name__)

    CircuitBreakerRegistry,
    CircuitOpenError,
    FailureKind,
    RetryBudget,
    RetryPolicyEngine,
    guarded,
)
from .scheduler import AdaptiveScheduler
from .task_store import TaskStore

# ── state: TaskStore (единый source of truth) ────────────────────────────────
_task_store: TaskStore | None = None


async def get_task_store() -> TaskStore:
    global _task_store
    if _task_store is None:
        from .task_store import TaskStore
        _task_store = TaskStore(REDIS_URL)
    return _task_store


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STREAM_KEY = "agent:stream"
CONSUMER_GROUP = "agent-workers"
CONSUMER_NAME = os.getenv("HOSTNAME", "worker-1")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# ── shared singleton instances ────────────────────────────────────────────────
_dag_recorder: DAGRecorder | None = None
_scheduler: AdaptiveScheduler | None = None
_cancellation: HardCancellation | None = None
_aiohttp_session: aiohttp.ClientSession | None = None
_retry_engine: RetryPolicyEngine | None = None
_cb_registry: CircuitBreakerRegistry | None = None


async def _get_session() -> aiohttp.ClientSession:
    global _aiohttp_session
    if _aiohttp_session is None or _aiohttp_session.closed:
        _aiohttp_session = aiohttp.ClientSession()
    return _aiohttp_session


async def get_dag_recorder() -> DAGRecorder:
    global _dag_recorder
    if _dag_recorder is None:
        _dag_recorder = DAGRecorder(REDIS_URL)
    return _dag_recorder


async def get_scheduler() -> AdaptiveScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AdaptiveScheduler(REDIS_URL)
    return _scheduler


async def get_cancellation() -> HardCancellation:
    global _cancellation
    if _cancellation is None:
        _cancellation = HardCancellation(REDIS_URL)
    return _cancellation


async def get_retry_engine() -> RetryPolicyEngine:
    global _retry_engine
    if _retry_engine is None:
        _retry_engine = RetryPolicyEngine(REDIS_URL)
    return _retry_engine


def get_cb_registry() -> CircuitBreakerRegistry:
    global _cb_registry
    if _cb_registry is None:
        _cb_registry = CircuitBreakerRegistry(REDIS_URL)
    return _cb_registry


# ── LLM call (async aiohttp, circuit-broken) ─────────────────────────────────

async def _llm(task: str, context: dict | None = None) -> dict:
    cb = get_cb_registry().get("ollama")
    session = await _get_session()
    payload = {
        "model": "llama3.2:latest",
        "prompt": task,
        "stream": False,
    }
    if context:
        payload["context"] = context

    async def _raw_call():
        async with session.post(
            OLLAMA_URL + "/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=120),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    try:
        return await guarded(cb, _raw_call)
    except CircuitOpenError:
        raise
    except aiohttp.ClientResponseError as e:
        if e.status == 429:
            raise Exception("429 TooManyRequests — rate limited, retry with backoff")
        raise


# ── shell execution (async subprocess) ───────────────────────────────────────

async def _run_shell(cmd: str) -> dict:
    proc = await asyncio.create_subprocess_exec(
        "sh", "-c", cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    cancellation = await get_cancellation()
    monitor_task = await cancellation.check_and_cancel_subprocess("shell", proc)

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        monitor_task.cancel()
        return {
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "returncode": proc.returncode,
        }
    except asyncio.TimeoutError:
        monitor_task.cancel()
        try:
            pgid = os.getpgid(proc.pid)
        except Exception:
            pgid = proc.pid
        await cancellation._send_signals([pgid], CancellationStrength.HARD, 0.0)
        return {"error": "timeout", "returncode": -1}


# ── step execution with DAG tracing ────────────────────────────────────────

async def run_step_with_trace(
    step: dict,
    dag_id: str,
    task_id: str,
) -> dict:
    """Execute a single step with DAG recording + cancellation monitoring."""
    step_id = step.get("id", "")
    tool = step.get("tool", "unknown")
    step.get("action", "")
    params = step.get("params", {})

    dag = await get_dag_recorder()
    await get_cancellation()

    await dag.start_step(dag_id, step_id)

    try:
        if tool == "llm":
            result = await _llm(params.get("prompt", ""), params.get("context"))
        elif tool == "shell":
            result = await _run_shell(params.get("command", ""))
        elif tool == "memory":
            result = {"status": "noop"}  # memory handled externally
        else:
            result = {"error": f"unknown tool: {tool}"}

        status = StepStatus.COMPLETED if "error" not in result else StepStatus.FAILED
        await dag.finish_step(dag_id, step_id, status=status, metadata={"result": result})
        return result
    except asyncio.CancelledError:
        await dag.finish_step(dag_id, step_id, status=StepStatus.CANCELLED)
        raise
    except Exception as exc:
        await dag.finish_step(dag_id, step_id, status=StepStatus.FAILED, error=str(exc))
        return {"error": str(exc)}


# ── planning + execution cycle ─────────────────────────────────────────────

async def plan(task: str) -> list[dict]:
    """Generate execution plan (step list) via LLM."""
    prompt = (
        "You are a task planner. Given a task, return a JSON array of steps.\n"
        "Each step: {\"id\": \"step_N\", \"tool\": \"llm|shell|memory\", "
        "\"action\": \"description\", \"params\": {...}}\n"
        f"Task: {task}\n\nRespond with valid JSON only."
    )
    result = await _llm(prompt)
    raw = result.get("response", "[]")
    try:
        # strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        steps = json.loads(raw)
        if isinstance(steps, dict):
            steps = steps.get("steps", [steps])
        return steps
    except Exception:
        return [{"id": "step_1", "tool": "llm", "action": "respond", "params": {"prompt": task}}]


# ── engine.run() — full async with DAG + scheduling ─────────────────────────

async def run(task: str, context: dict | None = None) -> dict:
    """
    Full async execution:
    1. Plan steps
    2. Create DAG
    3. Execute steps concurrently (bounded by semaphore)
    4. Record execution trace
    5. Return result
    """
    dag = await get_dag_recorder()
    await get_cancellation()

    # ── planning ──────────────────────────────────────────────────────────
    steps = await plan(task)

    # ── create task id for cancellation registration ─────────────────────
    task_id = context.get("task_id", "unknown") if context else "unknown"
    dag_id = await dag.create(task_id)

    # ── register all steps in DAG ─────────────────────────────────────────
    step_ids = []
    for step in steps:
        sid = await dag.add_step(
            dag_id=dag_id,
            step_name=step.get("action", "unknown"),
            tool=step.get("tool", "unknown"),
            parent_id=None,
        )
        step["_dag_id"] = dag_id
        step["_step_id"] = sid
        step_ids.append(sid)

    # ── concurrent execution (bounded) ───────────────────────────────────
    semaphore = asyncio.Semaphore(4)  # worker concurrency

    async def bounded_run_step(step: dict) -> dict:
        async with semaphore:
            return await run_step_with_trace(step, dag_id, task_id)

    try:
        results = await asyncio.gather(
            *[bounded_run_step(step) for step in steps],
            return_exceptions=True,
        )
    except asyncio.CancelledError:
        # hard-cancel all steps
        for sid in step_ids:
            await dag.finish_step(dag_id, sid, status=StepStatus.CANCELLED)
        raise

    # ── finalize DAG ─────────────────────────────────────────────────────
    await dag.finalize(dag_id)

    # ── build response ───────────────────────────────────────────────────
    outputs = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            outputs.append({"error": str(r)})
        else:
            outputs.append(r)

    return {
        "result": outputs,
        "dag_id": dag_id,
        "observability": await dag.get_observability_report(dag_id),
    }


# ── worker loop v3 ──────────────────────────────────────────────────────────

async def worker_loop():
    """
    Worker loop using AdaptiveScheduler + HardCancellation.
    Replaces Redis Stream consumer group pattern with sorted-set scheduler.
    """
    await get_dag_recorder()
    scheduler = await get_scheduler()
    await get_cancellation()

    asyncio.get_running_loop()

    while True:
        try:
            # adapt concurrency dynamically
            concurrency = await scheduler.compute_target_concurrency()
            asyncio.Semaphore(concurrency)

            # dequeue highest-priority tasks
            tasks = await scheduler.dequeue(count=concurrency)
            if not tasks:
                await asyncio.sleep(1)
                continue

            async def process_task(task_payload: dict):
                task_id = task_payload.get("task_id", "unknown")
                payload = task_payload.get("payload", {})
                max_retries = int(payload.get("max_retries", MAX_RETRIES))
                worker_id = CONSUMER_NAME

                store = await get_task_store()
                retry_engine = await get_retry_engine()
                event_store = EventStore(REDIS_URL)

                budget = RetryBudget(task_id=task_id, max_attempts=max_retries)
                await retry_engine.init_budget(task_id, budget)

                # claim — единая точка входа для state
                record = await store.claim_task(task_id, worker_id)
                if not record:
                    await store.record_metric(task_id, "epoch_mismatches")
                    return  # already claimed or other worker got it

                await store.record_metric(task_id, "claims")
                claimed_epoch = record.epoch

                # EventStore: TASK_CLAIMED
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

                dag_id = await (await get_dag_recorder()).create(task_id, epoch=claimed_epoch)

                attempt = 0

                while True:
                    try:
                        result = await run(
                            task=payload.get("task", ""),
                            context={"task_id": task_id, "dag_id": dag_id},
                        )
                        has_error = any(
                            isinstance(r, dict) and "error" in r
                            for r in result.get("result", [])
                        )
                        if has_error:
                            error_str = "; ".join(
                                r.get("error", "") for r in result.get("result", []) if isinstance(r, dict) and "error" in r
                            )
                            should_retry, kind, _ = await retry_engine.should_retry(task_id, error_str)
                            if should_retry and kind in (FailureKind.TRANSIENT, FailureKind.UNKNOWN):
                                attempt, delay = await retry_engine.record_failure(task_id)
                                await retry_engine.init_budget(task_id, budget)
                                await asyncio.sleep(delay)
                                await store.record_metric(task_id, "retries")
                                # EventStore: TASK_RETRIED
                                rec = await store.get_task(task_id)
                                new_epoch = rec.epoch if rec else claimed_epoch
                                await event_store.append_task_retried(task_id, claimed_epoch, worker_id, new_epoch)
                                continue
                            await store.complete_task(task_id, worker_id, result)
                            await store.fail_task(task_id, worker_id, error_str)
                            await store.record_metric(task_id, "failures")
                            # EventStore: TASK_FAILED
                            await event_store.append_task_failed(task_id, claimed_epoch, worker_id, error_str)
                        else:
                            await store.complete_task(task_id, worker_id, result)
                            await store.record_metric(task_id, "completions")
                            # EventStore: TASK_COMPLETED
                            await event_store.append_task_completed(task_id, claimed_epoch, worker_id, result)
                        break

                    except CircuitOpenError as e:
                        await store.complete_task(task_id, worker_id, {"error": str(e)})
                        await store.fail_task(task_id, worker_id, str(e))
                        await store.record_metric(task_id, "failures")
                        await event_store.append_task_failed(task_id, claimed_epoch, worker_id, str(e))
                        break
                    except asyncio.CancelledError:
                        await store.cancel_task(task_id, worker_id)
                        break
                    except Exception as exc:
                        tb = traceback.format_exc()
                        error_msg = f"{type(exc).__name__}: {exc}\n{tb}"
                        should_retry, kind, _ = await retry_engine.should_retry(task_id, error_msg)
                        if should_retry and kind in (FailureKind.TRANSIENT, FailureKind.UNKNOWN):
                            attempt, delay = await retry_engine.record_failure(task_id)
                            await retry_engine.init_budget(task_id, budget)
                            await asyncio.sleep(delay)
                            continue
                        await store.complete_task(task_id, worker_id, {"error": error_msg})
                        await store.fail_task(task_id, worker_id, error_msg)
                        await event_store.append_task_failed(task_id, claimed_epoch, worker_id, error_msg)
                        break

            # fire tasks bounded by semaphore
            for task in tasks:
                asyncio.create_task(process_task(task))

            await asyncio.sleep(0.1)

        except Exception as e:
            log.info(f"worker error: {e}")
            await asyncio.sleep(5)

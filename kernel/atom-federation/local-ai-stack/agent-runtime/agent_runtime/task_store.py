"""
TaskStore — единый источник истины для управления состоянием задач.

Заменяет:
- TaskStateMachine (task_state.py) — оставляем, но чистим
- state_machine.py — удаляем полностью

Принципы:
- Единственный state owner
- Ownership check перед КАЖДЫМ переходом
- Epoch versioning для retry safety
- Lua-атомарные переходы
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum

import redis
import redis.asyncio as aioredis

REDIS_URL = redis.environ.get("REDIS_URL", "redis://localhost:6379")

STATE_PREFIX = "task_state:"
RESULT_PREFIX = "result:"
EPOCH_PREFIX = "task_epoch:"

RESULT_TTL = 3600  # 1 час


class TaskState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class TaskRecord:
    task_id: str
    state: TaskState
    worker_id: str
    epoch: int
    attempt: int
    max_attempts: int
    enqueued_at: float
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "state": self.state.value,
            "worker_id": self.worker_id,
            "epoch": self.epoch,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "enqueued_at": self.enqueued_at,
            "started_at": str(self.started_at) if self.started_at else "",
            "finished_at": str(self.finished_at) if self.finished_at else "",
            "error": self.error or "",
            "payload": json.dumps(self.payload),
        }

    @classmethod
    def from_dict(cls, raw: dict) -> TaskRecord:
        started = raw.get("started_at", "")
        finished = raw.get("finished_at", "")
        return cls(
            task_id=raw.get("task_id", ""),
            state=TaskState(raw.get("state", "PENDING")),
            worker_id=raw.get("worker_id", ""),
            epoch=int(raw.get("epoch", "0")),
            attempt=int(raw.get("attempt", "0")),
            max_attempts=int(raw.get("max_attempts", "3")),
            enqueued_at=float(raw.get("enqueued_at", "0")),
            started_at=float(started) if started else None,
            finished_at=float(finished) if finished else None,
            error=raw.get("error") or None,
            payload=json.loads(raw.get("payload", "{}")),
        )


_async_r: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _async_r
    if _async_r is None:
        _async_r = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _async_r


def _state_key(task_id: str) -> str:
    return f"{STATE_PREFIX}{task_id}"


def _result_key(task_id: str) -> str:
    return f"{RESULT_PREFIX}{task_id}"


def _epoch_key(task_id: str) -> str:
    return f"{EPOCH_PREFIX}{task_id}"


# ── singleton ────────────────────────────────────────────────────────────────

_store: TaskStore | None = None


def get_task_store(redis_url: str = REDIS_URL) -> TaskStore:
    global _store
    if _store is None:
        _store = TaskStore(redis_url)
    return _store


# ── TaskStore ────────────────────────────────────────────────────────────────


class TaskStore:
    """
    Единый источник истины для task lifecycle.

    Все переходы — атомарные, с ownership check, epoch-aware.
    """

    def __init__(self, redis_url: str = REDIS_URL, result_ttl: int = RESULT_TTL):
        self._redis_url = redis_url
        self._result_ttl = result_ttl
        self._r: aioredis.Redis | None = None

    async def _redis(self) -> aioredis.Redis:
        if self._r is None:
            self._r = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._r

    def _metrics_key(self, task_id: str, name: str) -> str:
        return f"task_metric:{task_id}:{name}"

    # ── create ────────────────────────────────────────────────────────────────

    async def create_task(
        self,
        task_id: str,
        payload: dict,
        max_attempts: int = 3,
    ) -> TaskRecord:
        """
        Регистрирует новую задачу в PENDING.
        Idempotent — если уже существует, возвращает текущую запись.
        """
        r = await self._redis()
        key = _state_key(task_id)
        now = time.time()

        lua = """
        local key = KEYS[1]
        local exists = redis.call('EXISTS', key)
        if exists == 1 then
            return 'EXISTS'
        end
        redis.call('HSET', key,
            'task_id', ARGV[1],
            'state', 'PENDING',
            'worker_id', '',
            'epoch', '0',
            'attempt', '0',
            'max_attempts', ARGV[2],
            'enqueued_at', ARGV[3],
            'started_at', '',
            'finished_at', '',
            'error', '',
            'payload', ARGV[4]
        )
        redis.call('EXPIRE', key, ARGV[5])
        return 'CREATED'
        """

        result = await r.eval(
            lua, 1, key,
            task_id, str(max_attempts), str(now), json.dumps(payload),
            str(self._result_ttl * 2),
        )

        if result == "EXISTS":
            raw = await r.hgetall(key)
            return TaskRecord.from_dict(raw)

        record = TaskRecord(
            task_id=task_id,
            state=TaskState.PENDING,
            worker_id="",
            epoch=0,
            attempt=0,
            max_attempts=max_attempts,
            enqueued_at=now,
            payload=payload,
        )
        return record

    # ── claim (PENDING → RUNNING) ────────────────────────────────────────────

    async def claim_task(self, task_id: str, worker_id: str) -> TaskRecord | None:
        """
        Атомарно захватывает PENDING задачу.
        Returns TaskRecord если успех, None если уже claimed/running/done.
        Проверяет epoch — только актуальные задачи.
        """
        r = await self._redis()
        key = _state_key(task_id)
        now = time.time()

        # Lua: atomic claim if PENDING + increment epoch
        lua = """
        local key = KEYS[1]
        local state = redis.call('HGET', key, 'state')
        if state == nil then
            return '{"error":"NOT_FOUND"}'
        end
        if state ~= 'PENDING' then
            return '{"error":"NOT_PENDING"}'
        end
        -- increment epoch on each claim (retry cycle marker)
        local epoch = redis.call('HINCRBY', key, 'epoch', 1)
        redis.call('HSET', key,
            'state', 'RUNNING',
            'worker_id', ARGV[1],
            'started_at', ARGV[2],
            'attempt', '0'
        )
        return '{"ok":1}'
        """

        result = await r.eval(lua, 1, key, worker_id, str(now))

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            return None

        if "error" in parsed:
            return None

        raw = await r.hgetall(key)
        return TaskRecord.from_dict(raw)

    # ── complete (RUNNING → DONE) ───────────────────────────────────────────

    async def complete_task(
        self,
        task_id: str,
        worker_id: str,
        result: dict,
    ) -> bool:
        """
        Атомарно завершает задачу.
        Проверяет: worker_id match + state==RUNNING.
        """
        r = await self._redis()
        key = _state_key(task_id)

        lua = """
        local current_worker = redis.call('HGET', KEYS[1], 'worker_id')
        local state = redis.call('HGET', KEYS[1], 'state')
        if state ~= 'RUNNING' then return 0 end
        if current_worker ~= ARGV[1] then return 0 end
        redis.call('HSET', KEYS[1], 'state', 'DONE', 'finished_at', ARGV[2])
        return 1
        """

        ok = await r.eval(lua, 1, key, worker_id, str(time.time()))
        if not ok:
            return False

        result_key = _result_key(task_id)
        await r.setex(result_key, self._result_ttl, json.dumps(result))
        return True

    # ── fail (RUNNING → FAILED или → PENDING для retry) ─────────────────────

    async def fail_task(
        self,
        task_id: str,
        worker_id: str,
        error: str,
    ) -> bool:
        """
        Обрабатывает failure задачи.
        attempt < max_attempts → retry (state=PENDING, новый epoch)
        attempt >= max_attempts → FAILED
        """
        r = await self._redis()
        key = _state_key(task_id)

        lua = """
        local state = redis.call('HGET', KEYS[1], 'state')
        local current_worker = redis.call('HGET', KEYS[1], 'worker_id')
        if state ~= 'RUNNING' then return 0 end
        if current_worker ~= ARGV[1] then return 0 end

        local attempt = tonumber(redis.call('HGET', KEYS[1], 'attempt') or '0') + 1
        local max_attempts = tonumber(redis.call('HGET', KEYS[1], 'max_attempts') or '3')
        redis.call('HSET', KEYS[1], 'attempt', tostring(attempt))

        if attempt >= max_attempts then
            redis.call('HSET', KEYS[1], 'state', 'FAILED',
                'finished_at', ARGV[2], 'error', ARGV[3])
        else
            -- increment epoch for retry (stale workers detect mismatch)
            redis.call('HINCRBY', KEYS[1], 'epoch', 1)
            redis.call('HSET', KEYS[1],
                'state', 'PENDING',
                'worker_id', '',
                'started_at', '',
                'error', ARGV[3]
            )
        end
        return 1
        """

        ok = await r.eval(
            lua, 1, key, worker_id,
            str(time.time()), error,
        )
        return bool(ok)

    # ── retry (RUNNING → PENDING, новый epoch) ────────────────────────────────

    async def retry_task(self, task_id: str, worker_id: str) -> bool:
        """
        Принудительный retry — новый epoch, сброс worker_id.
        Используется когда задача должна быть перезапущена извне.
        """
        r = await self._redis()
        key = _state_key(task_id)

        lua = """
        local state = redis.call('HGET', KEYS[1], 'state')
        local current_worker = redis.call('HGET', KEYS[1], 'worker_id')
        if state ~= 'RUNNING' then return 0 end
        if current_worker ~= ARGV[1] then return 0 end
        redis.call('HINCRBY', KEYS[1], 'epoch', 1)
        redis.call('HSET', KEYS[1],
            'state', 'PENDING',
            'worker_id', '',
            'started_at', '',
            'error', ''
        )
        return 1
        """

        ok = await r.eval(lua, 1, key, worker_id)
        return bool(ok)

    # ── cancel ───────────────────────────────────────────────────────────────

    async def cancel_task(self, task_id: str, worker_id: str) -> bool:
        """Отмена задачи — только owner может отменить."""
        r = await self._redis()
        key = _state_key(task_id)

        lua = """
        local current_worker = redis.call('HGET', KEYS[1], 'worker_id')
        local state = redis.call('HGET', KEYS[1], 'state')
        if state == 'DONE' or state == 'FAILED' then return 0 end
        if current_worker ~= '' and current_worker ~= ARGV[1] then return 0 end
        redis.call('HSET', KEYS[1], 'state', 'CANCELLED',
            'finished_at', ARGV[2], 'error', 'cancelled')
        return 1
        """

        ok = await r.eval(lua, 1, key, worker_id, str(time.time()))
        return bool(ok)

    # ── stale recovery ───────────────────────────────────────────────────────

    async def recover_stale_tasks(self, worker_id: str, stale_timeout: int = 300) -> int:
        """
        Находит RUNNING задачи, которые stale (worker упал).
        Восстанавливает их для нового worker.
        """
        r = await self._redis()
        recovered = 0
        stale_before = time.time() - stale_timeout
        cursor = 0

        while True:
            cursor, keys = await r.scan(cursor, match=f"{STATE_PREFIX}*", count=200)
            for state_key in keys:
                raw = await r.hgetall(state_key)
                state = raw.get("state", "")
                if state != TaskState.RUNNING.value:
                    continue
                started_at = float(raw.get("started_at") or 0)
                if started_at < stale_before:
                    task_id = state_key[len(STATE_PREFIX):]
                    record = await self.claim_task(task_id, worker_id)
                    if record:
                        recovered += 1
            if cursor == 0:
                break

        return recovered

    # ── read ─────────────────────────────────────────────────────────────────

    async def get_task(self, task_id: str) -> TaskRecord | None:
        r = await self._redis()
        raw = await r.hgetall(_state_key(task_id))
        if not raw:
            return None
        return TaskRecord.from_dict(raw)

    async def get_result(self, task_id: str) -> dict | None:
        r = await self._redis()
        raw = await r.get(_result_key(task_id))
        return json.loads(raw) if raw else None

    async def get_all_by_state(self, state: TaskState) -> list[TaskRecord]:
        r = await self._redis()
        cursor = 0
        results = []
        while True:
            cursor, keys = await r.scan(cursor, match=f"{STATE_PREFIX}*", count=200)
            for state_key in keys:
                raw = await r.hgetall(state_key)
                if raw.get("state") == state.value:
                    results.append(TaskRecord.from_dict(raw))
            if cursor == 0:
                break
        return results

    # ── observability + idempotency ─────────────────────────────────────────────

    @staticmethod
    def make_idempotency_key(task_id: str, epoch: int, step_id: str) -> str:
        """
        Idempotency key for side-effect protection.
        Format: idem:{task_id}:{epoch}:{step_id}
        Store in Redis with SET NX + EX to guard against double execution.
        """
        return f"idem:{task_id}:{epoch}:{step_id}"

    async def check_and_set_idempotency(
        self,
        task_id: str,
        epoch: int,
        step_id: str,
        ttl: int = 86400,
    ) -> bool:
        """
        Atomically check-and-set idempotency key.
        Returns True if this is the FIRST execution (key was set).
        Returns False if already executed (duplicate).
        Use before any side-effect (shell, API call, git push).
        """
        key = self.make_idempotency_key(task_id, epoch, step_id)
        r = await self._redis()
        # SET NX = only set if not exists
        ok = await r.set(key, "1", nx=True, ex=ttl)
        return ok is not None

    async def record_metric(self, task_id: str, name: str, delta: int = 1) -> None:
        """Increment a named counter for task_id."""
        r = await self._redis()
        key = self._metrics_key(task_id, name)
        await r.hincrby(key, "count", delta)
        await r.expire(key, self._result_ttl * 2)

    async def get_metrics(self, task_id: str) -> dict:
        """Return all metric counters for a task_id."""
        r = await self._redis()
        key_prefix = f"task_metric:{task_id}:"
        metric_names = ["claims", "completions", "failures", "retries", "epoch_mismatches", "duplicate_aborts"]
        result = {}
        for name in metric_names:
            val = await r.hget(key_prefix + name, "count")
            result[name] = int(val) if val else 0
        return result

    # ── delete ───────────────────────────────────────────────────────────────

    async def delete_task(self, task_id: str) -> None:
        r = await self._redis()
        await r.delete(_state_key(task_id), _result_key(task_id), _epoch_key(task_id))
        # also clean up metrics
        metric_names = ["claims", "completions", "failures", "retries", "epoch_mismatches", "duplicate_aborts"]
        keys_to_delete = [self._metrics_key(task_id, n) for n in metric_names]
        if keys_to_delete:
            await r.delete(*keys_to_delete)

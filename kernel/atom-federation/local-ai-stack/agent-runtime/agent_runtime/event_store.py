"""
EventStore — Redis Streams backed event log with Lamport clock.

Components:
1. EventStore    — append-only event log, per-task streams
2. LamportClock — monotonic logical clock per task
3. ReplayEngine — deterministic replay from event history
"""

from __future__ import annotations

import redis.asyncio as aioredis

from .event_sourcing import EventType, TaskEvent

STREAM_PREFIX = "events:"
STREAM_META_PREFIX = "events:meta:"
LAMPORT_PREFIX = "lamport:"
TTL_SECONDS = 86400 * 7  # 7 days


class LamportClock:
    """
    Per-task Lamport clock for causal ordering.

    Each task_id has its own logical clock in Redis.
    Increment-on-send: max(local, remote) + 1
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis: aioredis.Redis | None = None
        self._redis_url = redis_url

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    def _key(self, task_id: str) -> str:
        return f"{LAMPORT_PREFIX}{task_id}"

    async def tick(self, task_id: str) -> int:
        """Increment and return new Lamport timestamp for task_id."""
        r = await self._get_redis()
        new_ts = await r.incr(self._key(task_id))
        await r.expire(self._key(task_id), TTL_SECONDS)
        return int(new_ts)

    async def update(self, task_id: str, remote_ts: int) -> int:
        """
        Merge remote timestamp: max(local, remote) + 1.
        Returns new local timestamp.
        """
        r = await self._get_redis()
        key = self._key(task_id)
        lua = """
        local current = tonumber(redis.call('GET', KEYS[1]) or '0')
        local remote = tonumber(ARGV[1])
        local new_val = math.max(current, remote) + 1
        redis.call('SET', KEYS[1], tostring(new_val), 'EX', ARGV[2])
        return new_val
        """
        new_ts = await r.eval(lua, 1, key, str(remote_ts), str(TTL_SECONDS))
        return int(new_ts)

    async def get(self, task_id: str) -> int:
        """Get current Lamport timestamp (0 if never set)."""
        r = await self._get_redis()
        val = await r.get(self._key(task_id))
        return int(val or 0)


class EventStore:
    """
    Append-only event log backed by Redis Streams.

    Design:
    - One stream per task_id: events:{task_id}
    - Events are immutable, strictly ordered by Lamport timestamp
    - Stream acts as WAL: replay reads from stream
    - Meta index: events:meta:{task_id} → latest stream id (for replay cursor)

    Replay guarantees:
    - Same event sequence → same execution outcome
    - Deterministic: no external state dependencies in replay
    - Idempotent: replay of already-executed steps detects via IDEMPOTENCY_SET
    """

    STREAM_PREFIX = STREAM_PREFIX
    META_PREFIX   = STREAM_META_PREFIX

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis: aioredis.Redis | None = None
        self._redis_url = redis_url
        self._clock = LamportClock(redis_url)

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    # ── append ───────────────────────────────────────────────────────────────

    async def append(
        self,
        task_id: str,
        event: TaskEvent,
    ) -> str:
        """
        Append event to task's stream. Returns stream entry ID.
        Also updates Lamport clock and meta index.
        """
        r = await self._get_redis()
        stream_key = f"{self.STREAM_PREFIX}{task_id}"

        # update Lamport clock
        new_ts = await self._clock.tick(task_id)
        event.lamport_ts = new_ts

        # XADD with explicit ID from lamport (works as sequence number)
        # Format: Lamport timestamp as integer ID part
        entry_id = f"{new_ts}-0"

        await r.xadd(stream_key, event.to_stream_fields(), id=entry_id)
        await r.expire(stream_key, TTL_SECONDS)

        # meta index: latest event ID for this task
        await r.set(f"{self.META_PREFIX}{task_id}", entry_id, ex=TTL_SECONDS)

        return entry_id

    async def append_step_executed(
        self,
        task_id: str,
        epoch: int,
        worker_id: str,
        step_id: str,
        step_name: str,
        tool: str,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        metadata: dict | None = None,
    ) -> str:
        """Convenience: emit STEP_EXECUTED with full step data."""
        event = TaskEvent.make(
            task_id=task_id,
            event_type=EventType.STEP_EXECUTED,
            worker_id=worker_id,
            epoch=epoch,
            lamport_ts=0,  # filled by append()
            step_id=step_id,
            payload={
                "step_name":   step_name,
                "tool":        tool,
                "latency_ms":  latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "metadata":    metadata or {},
            },
        )
        return await self.append(task_id, event)

    async def append_task_completed(
        self,
        task_id: str,
        epoch: int,
        worker_id: str,
        result: dict,
    ) -> str:
        event = TaskEvent.make(
            task_id=task_id,
            event_type=EventType.TASK_COMPLETED,
            worker_id=worker_id,
            epoch=epoch,
            lamport_ts=0,
            payload={"result": result},
        )
        return await self.append(task_id, event)

    async def append_task_failed(
        self,
        task_id: str,
        epoch: int,
        worker_id: str,
        error: str,
    ) -> str:
        event = TaskEvent.make(
            task_id=task_id,
            event_type=EventType.TASK_FAILED,
            worker_id=worker_id,
            epoch=epoch,
            lamport_ts=0,
            payload={"error": error},
        )
        return await self.append(task_id, event)

    async def append_task_retried(
        self,
        task_id: str,
        epoch: int,
        worker_id: str,
        new_epoch: int,
    ) -> str:
        event = TaskEvent.make(
            task_id=task_id,
            event_type=EventType.TASK_RETRIED,
            worker_id=worker_id,
            epoch=epoch,
            lamport_ts=0,
            payload={"new_epoch": new_epoch},
        )
        return await self.append(task_id, event)

    async def append_idempotency_set(
        self,
        task_id: str,
        epoch: int,
        worker_id: str,
        step_id: str,
        step_name: str,
    ) -> str:
        event = TaskEvent.make(
            task_id=task_id,
            event_type=EventType.IDEMPOTENCY_SET,
            worker_id=worker_id,
            epoch=epoch,
            lamport_ts=0,
            step_id=step_id,
            payload={"step_name": step_name},
        )
        return await self.append(task_id, event)

    async def append_epoch_changed(
        self,
        task_id: str,
        epoch: int,
        worker_id: str,
        new_epoch: int,
    ) -> str:
        event = TaskEvent.make(
            task_id=task_id,
            event_type=EventType.EPOCH_CHANGED,
            worker_id=worker_id,
            epoch=epoch,
            lamport_ts=0,
            payload={"new_epoch": new_epoch},
        )
        return await self.append(task_id, event)

    # ── read ────────────────────────────────────────────────────────────────

    async def get_events(
        self,
        task_id: str,
        from_id: str = "0",
        to_id: str = "+",
    ) -> list[TaskEvent]:
        """
        Read event range from task stream.
        from_id="0" means from beginning.
        to_id="+" means to latest.
        """
        r = await self._get_redis()
        stream_key = f"{self.STREAM_PREFIX}{task_id}"

        raw = await r.xrange(stream_key, id=f"{from_id}-{from_id}", id2=f"{to_id}-+")
        events = []
        for entry_id, fields in raw:
            try:
                fields["entry_id"] = entry_id
                events.append(TaskEvent.from_stream_fields(fields))
            except Exception:
                continue
        return events

    async def get_all_events(self, task_id: str) -> list[TaskEvent]:
        """Read all events for task (convenience)."""
        return await self.get_events(task_id, "0", "+")

    async def get_latest_entry_id(self, task_id: str) -> str | None:
        """Get latest stream entry ID (for replay cursor)."""
        r = await self._get_redis()
        return await r.get(f"{self.META_PREFIX}{task_id}")

    async def count_events(self, task_id: str) -> int:
        """Event count for task."""
        r = await self._get_redis()
        return await r.xlen(f"{self.STREAM_PREFIX}{task_id}")

    # ── replay engine ────────────────────────────────────────────────────────

    async def replay(
        self,
        task_id: str,
        from_entry_id: str | None = None,
        event_handler=None,
    ) -> list[dict]:
        """
        Deterministic replay of task's event history.

        Args:
            task_id        — task to replay
            from_entry_id  — start from this entry ID (None = from beginning)
            event_handler — optional async callable(event: TaskEvent) → None.
                            Called for each event during replay.

        Returns:
            List of event results (step outputs, completion, etc.)
            extracted from payload during replay.

        Replay semantics:
        - Events replayed in Lamport timestamp order
        - IDEMPOTENCY_SET events skip already-executed steps
        - STEP_EXECUTED → reproduce step execution record
        - TASK_COMPLETED/TASK_FAILED → terminate replay
        - Deterministic: same event sequence → same results
        """
        events = await self.get_all_events(task_id)
        if from_entry_id:
            events = [
                e for e in events
                if f"{e.lamport_ts}-0" > from_entry_id
            ]

        # sort by Lamport timestamp (already sorted, but enforce)
        events.sort(key=lambda e: e.lamport_ts)

        results: list[dict] = []
        executed_steps: set[str] = set()

        for event in events:
            # skip already-executed steps (idempotency check)
            if event.event_type == EventType.IDEMPOTENCY_SET and event.step_id:
                executed_steps.add(event.step_id)
                continue

            if event.event_type == EventType.STEP_EXECUTED:
                if event.step_id and event.step_id in executed_steps:
                    continue  # skip duplicate
                if event.step_id:
                    executed_steps.add(event.step_id)

                step_result = {
                    "event_id":   event.event_id,
                    "step_id":    event.step_id,
                    "step_name":  event.payload.get("step_name"),
                    "tool":       event.payload.get("tool"),
                    "latency_ms": event.payload.get("latency_ms", 0),
                    "status":     "replayed",
                }
                results.append(step_result)

            elif event.event_type == EventType.TASK_COMPLETED:
                results.append({
                    "event_type": "TASK_COMPLETED",
                    "result":     event.payload.get("result", {}),
                })

            elif event.event_type == EventType.TASK_FAILED:
                results.append({
                    "event_type": "TASK_FAILED",
                    "error":      event.payload.get("error", ""),
                })

            elif event.event_type == EventType.TASK_RETRIED:
                results.append({
                    "event_type": "TASK_RETRIED",
                    "new_epoch":  event.payload.get("new_epoch"),
                })

            if event_handler:
                await event_handler(event)

        return results

    async def get_audit_trail(self, task_id: str) -> dict:
        """
        Full audit trail: every event in order with human-readable summary.
        """
        events = await self.get_all_events(task_id)
        events.sort(key=lambda e: e.lamport_ts)

        trail = []
        for e in events:
            summary = {
                "event_id":   e.event_id,
                "type":       e.event_type.value,
                "epoch":      e.epoch,
                "lamport_ts": e.lamport_ts,
                "worker_id":  e.worker_id,
                "timestamp":  e.timestamp,
            }
            if e.step_id:
                summary["step_id"] = e.step_id
            if e.event_type == EventType.STEP_EXECUTED:
                summary["step_name"] = e.payload.get("step_name")
                summary["tool"]      = e.payload.get("tool")
                summary["latency_ms"] = e.payload.get("latency_ms", 0)
            elif e.event_type == EventType.TASK_COMPLETED:
                summary["has_result"] = "result" in e.payload
            elif e.event_type == EventType.TASK_FAILED:
                summary["error"] = e.payload.get("error", "")[:100]
            elif e.event_type == EventType.TASK_RETRIED:
                summary["new_epoch"] = e.payload.get("new_epoch")
            elif e.event_type == EventType.EPOCH_CHANGED:
                summary["new_epoch"] = e.payload.get("new_epoch")
            trail.append(summary)

        return {
            "task_id": task_id,
            "total_events": len(events),
            "events": trail,
        }

    # ── global ordering ────────────────────────────────────────────────────

    async def get_global_sequence(
        self,
        task_ids: list[str],
    ) -> list[TaskEvent]:
        """
        Merge events from multiple tasks, sorted by Lamport timestamp.
        Used for cross-task causal ordering (multi-agent scenarios).
        """
        all_events: list[TaskEvent] = []
        for tid in task_ids:
            events = await self.get_all_events(tid)
            all_events.extend(events)

        all_events.sort(key=lambda e: e.lamport_ts)
        return all_events

    # ── delete ─────────────────────────────────────────────────────────────

    async def delete_stream(self, task_id: str) -> None:
        """Delete event stream for task (audit data usually preserved)."""
        r = await self._get_redis()
        await r.delete(f"{self.STREAM_PREFIX}{task_id}")
        await r.delete(f"{self.META_PREFIX}{task_id}")
        await r.delete(f"{LAMPORT_PREFIX}{task_id}")

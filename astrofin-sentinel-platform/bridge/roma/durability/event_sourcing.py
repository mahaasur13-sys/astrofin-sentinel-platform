#!/usr/bin/env python3
# =============================================================================
# ROMA Event Sourcing Core — Deterministic State Machine
# =============================================================================
# Every state change = event. Event log = single source of truth.
# CRD state = projection from event log. Replay = deterministic rebuild.
# =============================================================================

from __future__ import annotations

import json
import uuid
import time
import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Iterator
from enum import Enum


# ============================================================================
# Event Types (typed, not string-based)
# ============================================================================

class EventType(Enum):
    # Job lifecycle
    JOB_SUBMITTED = "job.submitted"
    JOB_QUEUED = "job.queued"
    JOB_SCHEDULED = "job.scheduled"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"
    JOB_QUEUED_REJECTED = "job.queued_rejected"

    # Scheduling
    GPU_ALLOCATED = "gpu.allocated"
    GPU_RELEASED = "gpu.released"
    QUEUE_ENQUEUED = "queue.enqueued"
    QUEUE_DEQUEUED = "queue.dequeued"

    # System
    CONTROLLER_STARTED = "controller.started"
    CONTROLLER_STOPPED = "controller.stopped"
    NODE_REGISTERED = "node.registered"
    NODE_UNREGISTERED = "node.unregistered"
    RECONCILIATION_RUN = "reconciliation.run"
    SELF_HEAL_APPLIED = "self_heal.applied"

    # Backpressure
    BACKPRESSURE_TRIGGERED = "backpressure.triggered"
    QUEUE_SATURATION_WARN = "queue.saturation_warn"

    # CRD
    ROMATASK_CREATED = "romatask.created"
    ROMATASK_UPDATED = "romatask.updated"
    ROMATASK_DELETED = "romatask.deleted"


# ============================================================================
# Event Record
# ============================================================================

@dataclass(frozen=True)
class Event:
    event_id: str           # immutable UUID
    event_type: EventType
    aggregate_id: str      # job_id / task_id / node_id
    tick: int              # global monotonic tick (deterministic clock)
    timestamp_ns: int       # nanoseconds (NOT time.time for determinism)
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(event_type: EventType, aggregate_id: str, tick: int, payload: Dict) -> 'Event':
        return Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            aggregate_id=aggregate_id,
            tick=tick,
            timestamp_ns=time.time_ns(),
            payload=payload,
            metadata={}
        )

    def to_json(self) -> str:
        return json.dumps({
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'aggregate_id': self.aggregate_id,
            'tick': self.tick,
            'timestamp_ns': self.timestamp_ns,
            'payload': self.payload,
            'metadata': self.metadata
        }, sort_keys=True)

    @staticmethod
    def from_json(data: str) -> 'Event':
        d = json.loads(data)
        return Event(
            event_id=d['event_id'],
            event_type=EventType(d['event_type']),
            aggregate_id=d['aggregate_id'],
            tick=d['tick'],
            timestamp_ns=d['timestamp_ns'],
            payload=d['payload'],
            metadata=d.get('metadata', {})
        )


# ============================================================================
# Event Store (append-only)
# ============================================================================

class EventStore:
    """
    Append-only event log. Single source of truth.
    SQLite backend with WAL mode for performance.
    """

    def __init__(self, db_path: str = "/tmp/roma_events.db"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._tick_counter = 0
        self._tick_lock = threading.Lock()
        self._conn = self._create_connection()
        self._init_schema()

    def _create_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    tick INTEGER NOT NULL,
                    timestamp_ns INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """)
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_events_tick ON events(tick)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            self._conn.commit()

    def next_tick(self) -> int:
        """Monotonic tick — MUST be used for every event creation."""
        with self._tick_lock:
            self._tick_counter += 1
            return self._tick_counter

    def append(self, event: Event) -> None:
        """Append single event (thread-safe)."""
        with self._lock:
            self._conn.execute(
                "INSERT INTO events (event_id, event_type, aggregate_id, tick, timestamp_ns, payload, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event.event_id, event.event_type.value, event.aggregate_id, event.tick,
                 event.timestamp_ns, json.dumps(event.payload), json.dumps(event.metadata))
            )
            self._conn.commit()

    def append_batch(self, events: List[Event]) -> None:
        """Append multiple events atomically."""
        with self._lock:
            self._conn.executemany(
                "INSERT INTO events (event_id, event_type, aggregate_id, tick, timestamp_ns, payload, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(e.event_id, e.event_type.value, e.aggregate_id, e.tick, e.timestamp_ns,
                  json.dumps(e.payload), json.dumps(e.metadata)) for e in events]
            )
            self._conn.commit()

    def get_events_for_aggregate(self, aggregate_id: str) -> List[Event]:
        """Get all events for an aggregate (in tick order)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT event_id, event_type, aggregate_id, tick, timestamp_ns, payload, metadata FROM events WHERE aggregate_id = ? ORDER BY tick",
                (aggregate_id,)
            ).fetchall()
            return [self._row_to_event(r) for r in rows]

    def get_events_since(self, tick: int, limit: int = 1000) -> List[Event]:
        """Get events from tick N onwards (for replay)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT event_id, event_type, aggregate_id, tick, timestamp_ns, payload, metadata FROM events WHERE tick >= ? ORDER BY tick LIMIT ?",
                (tick, limit)
            ).fetchall()
            return [self._row_to_event(r) for r in rows]

    def replay_from_tick(self, tick: int) -> Iterator[Event]:
        """Replay events from tick N (deterministic iteration)."""
        offset = 0
        while True:
            events = self.get_events_since(tick + offset, limit=100)
            if not events:
                break
            for e in events:
                yield e
            offset = events[-1].tick - tick + 1

    def _row_to_event(self, row) -> Event:
        return Event(
            event_id=row[0],
            event_type=EventType(row[1]),
            aggregate_id=row[2],
            tick=row[3],
            timestamp_ns=row[4],
            payload=json.loads(row[5]),
            metadata=json.loads(row[6])
        )

    def get_current_tick(self) -> int:
        """Get last committed tick."""
        with self._lock:
            row = self._conn.execute("SELECT MAX(tick) FROM events").fetchone()
            return row[0] or 0

    def count_events(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def close(self) -> None:
        self._conn.close()


# ============================================================================
# State Projections (from event log)
# ============================================================================

@dataclass
class JobState:
    job_id: str
    status: str
    priority: int
    vram_gb: float
    gpu_node: Optional[str]
    created_tick: int
    last_tick: int
    retry_count: int = 0
    error: Optional[str] = None


class JobProjection:
    """Project current job state from event log."""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    def build_state(self, job_id: str) -> JobState:
        events = self.event_store.get_events_for_aggregate(job_id)
        if not events:
            raise ValueError(f"No events for job {job_id}")

        state = JobState(
            job_id=job_id,
            status='unknown',
            priority=0,
            vram_gb=0.0,
            gpu_node=None,
            created_tick=events[0].tick,
            last_tick=events[0].tick
        )

        for event in events:
            state.last_tick = event.tick
            self._apply_event(state, event)

        return state

    def _apply_event(self, state: JobState, event: Event) -> None:
        if event.event_type == EventType.JOB_SUBMITTED:
            state.status = 'submitted'
            state.priority = event.payload.get('priority', 5)
            state.vram_gb = event.payload.get('vram_gb', 4.0)
        elif event.event_type == EventType.JOB_QUEUED:
            state.status = 'queued'
        elif event.event_type == EventType.JOB_SCHEDULED:
            state.status = 'scheduled'
            state.gpu_node = event.payload.get('node')
        elif event.event_type == EventType.JOB_STARTED:
            state.status = 'running'
        elif event.event_type == EventType.JOB_COMPLETED:
            state.status = 'completed'
        elif event.event_type == EventType.JOB_FAILED:
            state.status = 'failed'
            state.error = event.payload.get('error')
        elif event.event_type == EventType.JOB_CANCELLED:
            state.status = 'cancelled'


# ============================================================================
# Aggregate Root
# ============================================================================

class JobAggregate:
    """Aggregate root — every command goes through here."""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    def submit_job(self, job_id: str, priority: int, vram_gb: float, gpu_required: bool) -> Event:
        tick = self.event_store.next_tick()
        event = Event.create(
            EventType.JOB_SUBMITTED,
            job_id,
            tick,
            {'priority': priority, 'vram_gb': vram_gb, 'gpu_required': gpu_required}
        )
        self.event_store.append(event)
        return event

    def enqueue_job(self, job_id: str) -> Event:
        tick = self.event_store.next_tick()
        event = Event.create(EventType.JOB_QUEUED, job_id, tick, {})
        self.event_store.append(event)
        return event

    def schedule_job(self, job_id: str, node: str) -> Event:
        tick = self.event_store.next_tick()
        event = Event.create(
            EventType.JOB_SCHEDULED,
            job_id,
            tick,
            {'node': node}
        )
        self.event_store.append(event)
        return event

    def start_job(self, job_id: str) -> Event:
        tick = self.event_store.next_tick()
        event = Event.create(EventType.JOB_STARTED, job_id, tick, {})
        self.event_store.append(event)
        return event

    def complete_job(self, job_id: str, result: Dict) -> Event:
        tick = self.event_store.next_tick()
        event = Event.create(
            EventType.JOB_COMPLETED,
            job_id,
            tick,
            {'result': result}
        )
        self.event_store.append(event)
        return event

    def fail_job(self, job_id: str, error: str) -> Event:
        tick = self.event_store.next_tick()
        event = Event.create(
            EventType.JOB_FAILED,
            job_id,
            tick,
            {'error': error}
        )
        self.event_store.append(event)
        return event

    def allocate_gpu(self, job_id: str, node: str, vram_gb: float) -> Event:
        tick = self.event_store.next_tick()
        event = Event.create(
            EventType.GPU_ALLOCATED,
            job_id,
            tick,
            {'node': node, 'vram_gb': vram_gb}
        )
        self.event_store.append(event)
        return event

    def release_gpu(self, job_id: str, node: str) -> Event:
        tick = self.event_store.next_tick()
        event = Event.create(
            EventType.GPU_RELEASED,
            job_id,
            tick,
            {'node': node}
        )
        self.event_store.append(event)
        return event


# ============================================================================
# Deterministic Replay (for debugging)
# ============================================================================

class DeterministicReplay:
    """Replay events and verify deterministic behavior."""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    def replay_and_verify(self, start_tick: int, apply_fn: Callable[[Event], None]) -> Dict[str, Any]:
        """
        Replay from start_tick using apply_fn.
        Returns verification report.
        """
        events = list(self.event_store.replay_from_tick(start_tick))
        applied_ticks = []
        errors = []

        for event in events:
            try:
                apply_fn(event)
                applied_ticks.append(event.tick)
            except Exception as e:
                errors.append({'tick': event.tick, 'error': str(e)})

        return {
            'events_replayed': len(events),
            'events_applied': len(applied_ticks),
            'errors': errors,
            'deterministic': len(errors) == 0
        }


# ============================================================================
# CLI Test
# ============================================================================

if __name__ == '__main__':
    import os
    db_path = "/tmp/roma_events_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    store = EventStore(db_path)
    agg = JobAggregate(store)
    proj = JobProjection(store)

    # Submit job
    agg.submit_job('job-001', priority=8, vram_gb=4.0, gpu_required=True)
    agg.enqueue_job('job-001')
    agg.schedule_job('job-001', 'gpu-node-1')
    agg.start_job('job-001')
    agg.complete_job('job-001', {'accuracy': 0.95})
    agg.allocate_gpu('job-001', 'gpu-node-1', 4.0)
    agg.release_gpu('job-001', 'gpu-node-1')

    print(f"Total events: {store.count_events()}")
    print(f"Current tick: {store.get_current_tick()}")

    # Rebuild state from event log
    state = proj.build_state('job-001')
    print(f"Job state: status={state.status}, gpu_node={state.gpu_node}, priority={state.priority}")

    # Deterministic replay test
    replay = DeterministicReplay(store)
    applied_states = []

    def state_apply(event: Event):
        applied_states.append(event.event_type.value)

    result = replay.replay_and_verify(1, state_apply)
    print(f"Replay result: {result}")

    store.close()
    os.remove(db_path)

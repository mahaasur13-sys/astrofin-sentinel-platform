"""
ROMA Event Store — Append-only event log (SQLite/PostgreSQL).
Every state change is captured as an immutable event.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
import threading
import sqlite3


class EventType(str, Enum):
    JOB_SUBMITTED = "job.submitted"
    JOB_QUEUED = "job.queued"
    JOB_DISPATCHED = "job.dispatched"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"
    GPU_LOCKED = "gpu.locked"
    GPU_RELEASED = "gpu.released"
    RECONCILER_SYNC = "reconciler.sync"
    RECONCILER_REPAIR = "reconciler.repair"
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


@dataclass
class Event:
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    event_type: str = ""
    job_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sequence: int = 0

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "job_id": self.job_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        return cls(**d)


class EventStore:
    """
    Append-only event store with replay capability.
    Uses SQLite by default (swap to PostgreSQL via connection_string).
    """

    def __init__(self, db_path: str = "/tmp/roma-events.db", connection_string: Optional[str] = None):
        self.db_path = db_path
        self.connection_string = connection_string  # Not used yet — PostgreSQL swap possible
        self._lock = threading.RLock()
        self._sequence = 0

        self._init_db()

    def _init_db(self):
        """Create tables if not exists."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                job_id TEXT,
                payload TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sequence INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_job_id ON events(job_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_sequence ON events(sequence)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)
        """)
        conn.commit()

        # Get current max sequence
        cursor = conn.execute("SELECT MAX(sequence) FROM events")
        max_seq = cursor.fetchone()[0]
        self._sequence = max_seq or 0

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def append(self, event: Event) -> Event:
        """Append an event to the log. Returns the event with sequence number."""
        with self._lock:
            self._sequence += 1
            event.sequence = self._sequence

            conn = self._get_conn()
            conn.execute(
                "INSERT INTO events (event_id, event_type, job_id, payload, timestamp, sequence) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.event_type,
                    event.job_id,
                    json.dumps(event.payload),
                    event.timestamp,
                    event.sequence,
                ),
            )
            conn.commit()

        return event

    def emit(self, event_type: EventType, job_id: Optional[str] = None, payload: Optional[Dict] = None) -> Event:
        """Convenience method to emit a new event."""
        event = Event(
            event_type=event_type.value,
            job_id=job_id,
            payload=payload or {},
        )
        return self.append(event)

    def replay(self, from_sequence: int = 0, event_filter: Optional[List[str]] = None) -> List[Event]:
        """
        Replay all events from from_sequence (exclusive) to latest.
        Optionally filter by event types.
        """
        conn = self._get_conn()
        query = "SELECT * FROM events WHERE sequence > ? ORDER BY sequence ASC"
        args = [from_sequence]

        if event_filter:
            placeholders = ",".join("?" * len(event_filter))
            query = f"SELECT * FROM events WHERE sequence > ? AND event_type IN ({placeholders}) ORDER BY sequence ASC"
            args = [from_sequence] + event_filter

        rows = conn.execute(query, args).fetchall()
        return [self._row_to_event(row) for row in rows]

    def get_events_for_job(self, job_id: str) -> List[Event]:
        """Get all events for a specific job."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM events WHERE job_id = ? ORDER BY sequence ASC",
            (job_id,),
        ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def get_latest_sequence(self) -> int:
        """Get the latest event sequence number."""
        return self._sequence

    def get_events_since(self, since: int) -> List[Event]:
        """Get events after a specific sequence number."""
        return self.replay(from_sequence=since)

    def _row_to_event(self, row: tuple) -> Event:
        return Event(
            event_id=row[0],
            event_type=row[1],
            job_id=row[2],
            payload=json.loads(row[3]),
            timestamp=row[4],
            sequence=row[5],
        )

    def replay_to_state(self, job_id: str) -> Dict[str, Any]:
        """
        Replay all events for a job and compute final state.
        Returns: {job_id, status, gpu_used, events[], final_state}
        """
        events = self.get_events_for_job(job_id)
        state: Dict[str, Any] = {
            "job_id": job_id,
            "status": "unknown",
            "gpu_used": False,
            "events": [e.to_dict() for e in events],
            "final_state": {},
        }

        for event in events:
            if event.event_type in (EventType.JOB_COMPLETED.value, EventType.JOB_SUCCEEDED.value if hasattr(EventType, 'JOB_SUCCEEDED') else "job.completed"):
                state["status"] = "completed"
            elif event.event_type == EventType.JOB_FAILED.value:
                state["status"] = "failed"
                state["error"] = event.payload.get("error", "unknown")
            elif event.event_type == EventType.JOB_CANCELLED.value:
                state["status"] = "cancelled"
            elif event.event_type == EventType.JOB_STARTED.value:
                state["status"] = "running"
            elif event.event_type == EventType.GPU_LOCKED.value:
                state["gpu_used"] = True

            state["final_state"] = event.payload

        return state

    def export_events(self, from_seq: int = 0) -> List[Dict]:
        """Export events as list of dicts (for backup / migration)."""
        return [e.to_dict() for e in self.replay(from_sequence=from_seq)]

    def close(self):
        """Close connection (no-op for SQLite but needed for interface)."""
        pass


class DurabilityLayer:
    """
    Top-level durability facade: event store + current state snapshots.
    """

    def __init__(self, db_path: str = "/tmp/roma-state.db"):
        self.events = EventStore(db_path.replace(".db", "-events.db"))
        self.snapshots = EventStore(db_path.replace(".db", "-snapshots.db"))
        self._snapshots_interval = 100  # snapshot every 100 events

    def record(self, event_type: EventType, job_id: Optional[str] = None, payload: Optional[Dict] = None) -> Event:
        """Record an event to the append-only log."""
        return self.events.emit(event_type, job_id, payload)

    def record_job_submitted(self, job_id: str, plan: dict, priority: int) -> Event:
        return self.record(EventType.JOB_SUBMITTED, job_id, {"plan": plan, "priority": priority})

    def record_job_dispatched(self, job_id: str, manifest_name: str, execution_mode: str) -> Event:
        return self.record(EventType.JOB_DISPATCHED, job_id, {"manifest": manifest_name, "mode": execution_mode})

    def record_job_completed(self, job_id: str, result: Optional[Dict] = None) -> Event:
        return self.record(EventType.JOB_COMPLETED, job_id, result or {})

    def record_job_failed(self, job_id: str, error: str) -> Event:
        return self.record(EventType.JOB_FAILED, job_id, {"error": error})

    def record_gpu_locked(self, job_id: str, vram_mb: int) -> Event:
        return self.record(EventType.GPU_LOCKED, job_id, {"vram_mb": vram_mb})

    def record_gpu_released(self, job_id: str) -> Event:
        return self.record(EventType.GPU_RELEASED, job_id, {})

    def replay_job_history(self, job_id: str) -> Dict[str, Any]:
        """Full replay of job lifecycle."""
        return self.events.replay_to_state(job_id)

    def replay_all(self, from_sequence: int = 0) -> List[Event]:
        return self.events.replay(from_sequence=from_sequence)

    def get_durability_report(self) -> Dict[str, Any]:
        """Current durability metrics."""
        total_events = self.events.get_latest_sequence()
        return {
            "total_events": total_events,
            "snapshots_count": self.snapshots.get_latest_sequence(),
            "db_paths": {
                "events": self.events.db_path,
                "snapshots": self.snapshots.db_path,
            },
            "last_sequence": total_events,
        }

    def checkpoint(self, component: str, state: Dict) -> Event:
        """Write a system checkpoint snapshot."""
        return self.snapshots.emit(
            EventType.SYSTEM_STARTUP,  # reuse for checkpoint
            job_id=None,
            payload={"component": component, "state": state},
        )

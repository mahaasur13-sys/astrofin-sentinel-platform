"""
ROMA State Store — Current state management with event sourcing.
Provides: save, load, compare, rollback capabilities.
"""

import json
import os
from typing import Dict, Any, List
from durability.event_store import EventStore, Event, EventType


class StateStore:
    """
    Key-value state store backed by the event log.
    State = latest snapshot + replay of events after snapshot.
    """

    def __init__(self, db_path: str = "/tmp/roma-state.db"):
        self._event_store = EventStore(db_path.replace(".db", "-events.db"))
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._snapshots_path = db_path.replace(".db", "-snapshots.json")
        self._load_snapshots()

    def _load_snapshots(self):
        if os.path.exists(self._snapshots_path):
            try:
                with open(self._snapshots_path) as f:
                    raw = json.load(f)
                    self._snapshots = raw.get("snapshots", {})
            except Exception:  # noqa: BLE001
                self._snapshots = {}

    def _save_snapshots(self):
        with open(self._snapshots_path, "w") as f:
            json.dump({"snapshots": self._snapshots}, f)

    # -------------------------------------------------------------------------
    # Job state operations
    # -------------------------------------------------------------------------

    def get_job_state(self, job_id: str) -> Dict[str, Any]:
        """
        Get current job state: reconstruct via event replay.
        """
        events = self._event_store.get_events_for_job(job_id)
        state = {
            "job_id": job_id,
            "status": "unknown",
            "gpu_used": False,
            "attempts": 0,
        }

        for event in events:
            et = event.event_type
            if et == EventType.JOB_SUBMITTED.value:
                state["status"] = "submitted"
                state["priority"] = event.payload.get("priority", 5)
            elif et == EventType.JOB_QUEUED.value:
                state["status"] = "queued"
            elif et == EventType.JOB_DISPATCHED.value:
                state["status"] = "dispatched"
                state["manifest"] = event.payload.get("manifest")
                state["execution_mode"] = event.payload.get("mode")
            elif et == EventType.JOB_STARTED.value:
                state["status"] = "running"
                state["started_at"] = event.timestamp
            elif et == EventType.JOB_COMPLETED.value:
                state["status"] = "completed"
                state["finished_at"] = event.timestamp
                state["result"] = event.payload
            elif et == EventType.JOB_FAILED.value:
                state["status"] = "failed"
                state["finished_at"] = event.timestamp
                state["error"] = event.payload.get("error")
            elif et == EventType.JOB_CANCELLED.value:
                state["status"] = "cancelled"
            elif et == EventType.GPU_LOCKED.value:
                state["gpu_used"] = True
                state["gpu_vram_mb"] = event.payload.get("vram_mb", 0)
            elif et == EventType.GPU_RELEASED.value:
                state["gpu_used"] = False

            # Merge payload into state
            state.update(event.payload)

        return state

    def save_job_state(self, job_id: str, state: Dict[str, Any]) -> Event:
        """
        Save a checkpoint snapshot for a job.
        This creates a "boundary" so replay doesn't start from 0.
        """
        self._snapshots[job_id] = state
        self._save_snapshots()

        return self._event_store.emit(
            EventType.SYSTEM_STARTUP,  # reuse as checkpoint event
            job_id=job_id,
            payload={"type": "snapshot", "state": state},
        )

    # -------------------------------------------------------------------------
    # Global state
    # -------------------------------------------------------------------------

    def get_all_jobs(self) -> List[str]:
        """Get list of all known job IDs from snapshots."""
        return list(self._snapshots.keys())

    def get_global_state(self) -> Dict[str, Any]:
        """
        Reconstruct full system state.
        """
        return {
            "jobs": {job_id: self.get_job_state(job_id) for job_id in self.get_all_jobs()},
            "durability": self._event_store.get_latest_sequence(),
        }

    # -------------------------------------------------------------------------
    # Comparison / diff
    # -------------------------------------------------------------------------

    def diff_state(self, job_id: str, expected: Dict[str, Any]) -> List[str]:
        """
        Compare current state vs expected.
        Returns list of differences.
        """
        current = self.get_job_state(job_id)
        diffs = []
        for key, expected_val in expected.items():
            current_val = current.get(key)
            if current_val != expected_val:
                diffs.append(f"  {key}: expected={expected_val}, actual={current_val}")
        return diffs

    # -------------------------------------------------------------------------
    # Rollback
    # -------------------------------------------------------------------------

    def rollback_to_sequence(self, job_id: str, target_sequence: int) -> bool:
        """
        Rollback job state to before a given sequence number.
        Returns True if rollback was possible.
        """
        events = self._event_store.get_events_for_job(job_id)
        pre_events = [e for e in events if e.sequence <= target_sequence]

        if not pre_events:
            return False

        # Rebuild state from pre-events
        temp_state = {"job_id": job_id}
        for event in pre_events:
            if event.event_type == EventType.JOB_STARTED.value:
                temp_state["status"] = "running"
            elif event.event_type == EventType.JOB_COMPLETED.value:
                temp_state["status"] = "completed"
            elif event.event_type == EventType.JOB_FAILED.value:
                temp_state["status"] = "failed"
                temp_state["error"] = event.payload.get("error")

        self.save_job_state(job_id, temp_state)
        return True

    # -------------------------------------------------------------------------
    # Export / import (for backup / migration)
    # -------------------------------------------------------------------------

    def export_all(self) -> Dict[str, Any]:
        """Export full state (snapshots + events) as dict."""
        return {
            "snapshots": self._snapshots,
            "events": self._event_store.export_events(),
        }

    def import_all(self, data: Dict[str, Any]):
        """Import state from dict (for recovery)."""
        self._snapshots = data.get("snapshots", {})
        self._save_snapshots()

        for event_dict in data.get("events", []):
            event = Event.from_dict(event_dict)
            self._event_store.append(event)
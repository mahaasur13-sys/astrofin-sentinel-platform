#!/usr/bin/env python3
"""
Job Engine — Event-Driven Finite State Machine with Telemetry Generation.
Each state transition generates an event for the event log (telemetry).
Supports hooks: on_state_change, on_failure, on_retry.

State Machine: CREATED → ADMITTED → SCHEDULED → RUNNING → SUCCESS/FAIL/RETRY
"""
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

logger = logging.getLogger("job_engine")


class JobState(Enum):
    CREATED = "CREATED"
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    RETRY = "RETRY"
    QUEUED = "QUEUED"


# Valid transitions: current_state → set of valid next states
TRANSITIONS: dict[JobState, list[JobState]] = {
    JobState.CREATED: [JobState.ADMITTED, JobState.REJECTED, JobState.QUEUED],
    JobState.ADMITTED: [JobState.SCHEDULED],
    JobState.QUEUED: [JobState.ADMITTED, JobState.REJECTED],
    JobState.SCHEDULED: [JobState.RUNNING],
    JobState.RUNNING: [JobState.SUCCESS, JobState.FAIL, JobState.RETRY],
    JobState.RETRY: [JobState.SCHEDULED],
    JobState.SUCCESS: [],
    JobState.FAIL: [],
}


@dataclass
class Job:
    id: str
    job_type: str
    priority: int
    memory_gb: int
    state: JobState = JobState.CREATED
    node_id: str | None = None
    attempts: int = 0
    max_attempts: int = 3
    created_at: float = field(default_factory=time.time)
    scheduled_at: float | None = None
    started_at: float | None = None
    completed_at: float | None = None
    last_error: str | None = None


# Event hooks — override these to add telemetry
class JobEventHooks:
    def on_state_change(self, job: Job, old: JobState, new: JobState) -> None:
        logger.info(f"[{job.id}] {old.value} → {new.value} (node={job.node_id})")

    def on_failure(self, job: Job, reason: str) -> None:
        logger.error(f"[{job.id}] FAILURE: {reason}")

    def on_retry(self, job: Job, attempt: int) -> None:
        logger.warning(f"[{job.id}] RETRY {attempt}/{job.max_attempts}")

    def on_submit(self, job: Job) -> None:
        logger.info(f"[{job.id}] submitted (type={job.job_type}, priority={job.priority})")


class TelemetryJobEngine(JobEventHooks):
    """
    Job engine with built-in telemetry generation.
    Every transition writes to the event log for ML dataset generation.
    """

    def __init__(self, db=None):
        self.jobs: dict[str, Job] = {}
        self._lock = Lock()
        self._db = db  # optional StateStore connection

    # ---------------------------------------------------------------------------
    # State Machine Operations
    # ---------------------------------------------------------------------------
    def create_job(self, job_type: str, priority: int, memory_gb: int) -> Job:
        job = Job(
            id=str(uuid.uuid4())[:8],
            job_type=job_type,
            priority=priority,
            memory_gb=memory_gb,
        )
        with self._lock:
            self.jobs[job.id] = job
        self.on_submit(job)
        self._write_event(job, job.state, None, "job_created")
        return job

    def admit(self, job_id: str, node_id: str) -> bool:
        job = self._get(job_id)
        return self._transition(job, JobState.ADMITTED, extra=lambda: setattr(job, "node_id", node_id))

    def reject(self, job_id: str, reason: str) -> bool:
        job = self._get(job_id)
        job.last_error = reason
        return self._transition(job, JobState.REJECTED)

    def schedule(self, job_id: str, node_id: str) -> bool:
        job = self._get(job_id)
        job.node_id = node_id
        job.scheduled_at = time.time()
        return self._transition(job, JobState.SCHEDULED)

    def start(self, job_id: str) -> bool:
        job = self._get(job_id)
        job.started_at = time.time()
        return self._transition(job, JobState.RUNNING)

    def succeed(self, job_id: str) -> bool:
        job = self._get(job_id)
        job.completed_at = time.time()
        return self._transition(job, JobState.SUCCESS)

    def fail(self, job_id: str, reason: str) -> bool:
        job = self._get(job_id)
        job.last_error = reason
        job.attempts += 1
        if job.attempts < job.max_attempts:
            self.on_retry(job, job.attempts)
            ok = self._transition(job, JobState.RETRY)
            if ok:
                self._write_event(job, JobState.RETRY, reason, "job_retry")
            return ok
        job.completed_at = time.time()
        self.on_failure(job, reason)
        return self._transition(job, JobState.FAIL)

    def get_job(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def get_jobs_by_state(self, state: JobState) -> list[Job]:
        return [j for j in self.jobs.values() if j.state == state]

    # ---------------------------------------------------------------------------
    # State Machine Logic
    # ---------------------------------------------------------------------------
    def _transition(self, job: Job, new_state: JobState, extra: Callable = None) -> bool:
        old_state = job.state
        if new_state not in TRANSITIONS.get(old_state, []):
            logger.warning(f"[{job.id}] INVALID TRANSITION {old_state.value} → {new_state.value}")
            return False
        with self._lock:
            job.state = new_state
        self.on_state_change(job, old_state, new_state)
        self._write_event(
            job,
            new_state,
            job.last_error,
            f"transition_{old_state.value}_{new_state.value}",
        )
        if extra:
            extra()
        return True

    def _get(self, job_id: str) -> Job:
        if job_id not in self.jobs:
            raise KeyError(f"Job {job_id} not found")
        return self.jobs[job_id]

    def _write_event(self, job: Job, state: JobState, error: str | None, event_type: str) -> None:
        """Write event to telemetry log (append-only, immutable)."""
        if self._db is None:
            return
        self._db.write_event(
            job_id=job.id,
            event_type=event_type,
            state=state.value,
            node_id=job.node_id,
            error=error,
            metadata={
                "job_type": job.job_type,
                "priority": job.priority,
                "memory_gb": job.memory_gb,
                "attempts": job.attempts,
                "duration_s": (job.completed_at - job.started_at if job.completed_at and job.started_at else None),
            },
        )

    # ---------------------------------------------------------------------------
    # Hooks (override to add telemetry)
    # ---------------------------------------------------------------------------
    def on_state_change(self, job: Job, old: JobState, new: JobState) -> None:
        logger.info(f"[{job.id}] {old.value} → {new.value}")

    def on_failure(self, job: Job, reason: str) -> None:
        logger.error(f"[{job.id}] FAILED: {reason}")

    def on_retry(self, job: Job, attempt: int) -> None:
        logger.warning(f"[{job.id}] RETRY attempt {attempt}/{job.max_attempts}")

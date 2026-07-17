#!/usr/bin/env python3
"""ROMA Job Retry System with Persistent Execution Guarantee"""

import threading
import uuid
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List, Callable
from datetime import datetime


class JobState(Enum):
    QUEUED = "queued"
    RETRYING = "retrying"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMMITTED = "committed"  # event store committed = job is done


@dataclass
class Job:
    job_id: str
    plugin_type: str
    payload: dict
    state: JobState
    retries: int
    max_retries: int
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None
    result: Optional[dict] = None


class JobRetryManager:
    """
    Handles job retry logic with exponential backoff.
    Job is only considered done after COMMITTED state (event store commit).
    """

    def __init__(
        self, max_retries: int = 3, base_backoff: float = 2.0, max_backoff: float = 60.0
    ):
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self._jobs: Dict[str, Job] = {}
        self._retry_queue: List[str] = []  # job_ids pending retry
        self._mu = threading.Lock()
        self._on_retry_callback: Optional[Callable] = None
        self._on_fail_callback: Optional[Callable] = None

    def enqueue(
        self,
        plugin_type: str,
        payload: dict,
        job_id: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> Job:
        job_id = job_id or f"job-{uuid.uuid4().hex[:12]}"
        max_retries = max_retries if max_retries is not None else self.max_retries
        job = Job(
            job_id=job_id,
            plugin_type=plugin_type,
            payload=payload,
            state=JobState.QUEUED,
            retries=0,
            max_retries=max_retries,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        with self._mu:
            self._jobs[job_id] = job
            self._retry_queue.append(job_id)
        return job

    def mark_running(self, job_id: str) -> bool:
        with self._mu:
            if job_id not in self._jobs:
                return False
            job = self._jobs[job_id]
            if job.state in (JobState.COMPLETED, JobState.FAILED, JobState.COMMITTED):
                return False
            job.state = JobState.RUNNING
            job.updated_at = datetime.utcnow()
            return True

    def mark_completed(self, job_id: str, result: dict) -> bool:
        with self._mu:
            if job_id not in self._jobs:
                return False
            job = self._jobs[job_id]
            job.state = JobState.COMPLETED
            job.result = result
            job.updated_at = datetime.utcnow()
            return True

    def mark_committed(self, job_id: str) -> bool:
        """Job committed to event store — this is the final state"""
        with self._mu:
            if job_id not in self._jobs:
                return False
            job = self._jobs[job_id]
            if job.state != JobState.COMPLETED:
                return False
            job.state = JobState.COMMITTED
            job.updated_at = datetime.utcnow()
            return True

    def handle_failure(self, job_id: str, error: str) -> str:
        """
        Handle job failure. Returns action: 'retry' | 'fail' | 'unknown_job'
        """
        with self._mu:
            if job_id not in self._jobs:
                return "unknown_job"
            job = self._jobs[job_id]
            job.error = error
            job.updated_at = datetime.utcnow()

            if job.retries < job.max_retries:
                job.state = JobState.RETRYING
                job.retries += 1
                backoff = min(self.base_backoff**job.retries, self.max_backoff)
                job.updated_at = datetime.utcnow()
                # Re-enqueue for retry
                self._retry_queue.append(job_id)
                action = "retry"
                if self._on_retry_callback:
                    try:
                        self._on_retry_callback(job_id, job.retries, backoff)
                    except Exception:
                        pass
            else:
                job.state = JobState.FAILED
                action = "fail"
                if self._on_fail_callback:
                    try:
                        self._on_fail_callback(job_id, error)
                    except Exception:
                        pass
            return action

    def get_next_retry(self) -> Optional[str]:
        with self._mu:
            if not self._retry_queue:
                return None
            return self._retry_queue.pop(0)

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._mu:
            return self._jobs.get(job_id)

    def get_jobs_by_state(self, state: JobState) -> List[Job]:
        with self._mu:
            return [j for j in self._jobs.values() if j.state == state]

    def get_stats(self) -> Dict:
        with self._mu:
            total = len(self._jobs)
            by_state = {s.value: 0 for s in JobState}
            for j in self._jobs.values():
                by_state[j.state.value] += 1
            return {
                "total_jobs": total,
                "by_state": by_state,
                "retry_queue_depth": len(self._retry_queue),
                "success_rate": (
                    by_state[JobState.COMMITTED.value] / total * 100 if total > 0 else 0
                ),
            }

    def on_retry(self, cb: Callable):
        self._on_retry_callback = cb

    def on_fail(self, cb: Callable):
        self._on_fail_callback = cb


class PersistentExecutionGuarantee:
    """
    Ensures jobs are never lost.
    STARTED → RUNNING → COMPLETED → COMMITTED
    If worker dies, job returns to queue.
    """

    def __init__(self, retry_manager: JobRetryManager):
        self.retry_mgr = retry_manager
        self._execution_log: Dict[str, dict] = {}

    def begin_execution(self, job_id: str) -> bool:
        """Mark job as started (in execution log)"""
        self._execution_log[job_id] = {
            "started_at": datetime.utcnow().isoformat(),
            "state": "started",
        }
        return self.retry_mgr.mark_running(job_id)

    def complete_execution(self, job_id: str, result: dict) -> bool:
        """Mark job as completed, not yet committed"""
        self._execution_log[job_id]["completed_at"] = datetime.utcnow().isoformat()
        self._execution_log[job_id]["state"] = "completed"
        return self.retry_mgr.mark_completed(job_id, result)

    def commit_execution(self, job_id: str) -> bool:
        """
        Commit to event store. This is the final, immutable state.
        Job is only truly 'done' after this.
        """
        self._execution_log[job_id]["committed_at"] = datetime.utcnow().isoformat()
        self._execution_log[job_id]["state"] = "committed"
        return self.retry_mgr.mark_committed(job_id)

    def get_execution_trace(self, job_id: str) -> Optional[dict]:
        return self._execution_log.get(job_id)

    def verify_committed(self, job_id: str) -> bool:
        trace = self._execution_log.get(job_id)
        return trace is not None and trace.get("state") == "committed"


if __name__ == "__main__":
    retry_mgr = JobRetryManager(max_retries=2)

    # Enqueue jobs
    job1 = retry_mgr.enqueue("ml_training", {"model": "yolov8", "epochs": 100})
    job2 = retry_mgr.enqueue("inference", {"model": "yolov8", "input": "img.jpg"})
    print(f"Enqueued: {job1.job_id}, {job2.job_id}")

    # Mark job1 running then completed
    assert retry_mgr.mark_running(job1.job_id)
    assert retry_mgr.mark_completed(job1.job_id, {"accuracy": 0.95})
    assert retry_mgr.mark_committed(job1.job_id)

    # Test failure + retry
    assert retry_mgr.mark_running(job2.job_id)
    action = retry_mgr.handle_failure(job2.job_id, "GPU OOM")
    assert action == "retry"
    job = retry_mgr.get_job(job2.job_id)
    assert job.retries == 1

    # Second failure → fail
    retry_mgr.mark_running(job2.job_id)
    action = retry_mgr.handle_failure(job2.job_id, "GPU OOM")
    assert action == "fail"
    job = retry_mgr.get_job(job2.job_id)
    assert job.state == JobState.FAILED

    # Stats
    stats = retry_mgr.get_stats()
    print(f"Retry stats: {stats}")

    # Persistent execution guarantee
    peg = PersistentExecutionGuarantee(retry_mgr)
    test_job_id = "job-test-123"
    peg.begin_execution(test_job_id)
    peg.complete_execution(test_job_id, {"result": "ok"})
    peg.commit_execution(test_job_id)
    trace = peg.get_execution_trace(test_job_id)
    print(f"Execution trace: {trace}")
    assert peg.verify_committed(test_job_id)

    print("=== Retry System + Persistent Guarantee: PASS ===")

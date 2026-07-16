"""Job Store — Durable State Machine"""

import json
import logging
import threading
import time
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from .core_models import Job, JobStatus

log = logging.getLogger("job_store")


class JobStore:
    def __init__(self, path: str = "/tmp/roma_jobs.json"):
        self._path = path
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._seq = 0
        self._load()

    def _load(self):
        try:
            with open(self._path) as f:
                data = json.load(f)
                for jd in data.get("jobs", []):
                    self._jobs[jd["id"]] = Job(**jd)
                self._seq = data.get("seq", 0)
            log.info(f"Loaded {len(self._jobs)} jobs")
        except FileNotFoundError:
            log.info("Fresh job store")

    def _save(self):
        with open(self._path, "w") as f:
            json.dump({"seq": self._seq, "jobs": [asdict(j) for j in self._jobs.values()]}, f)

    def submit(
        self,
        plugin: str,
        payload: dict[str, Any],
        gpu: float = 1.0,
        ttl: float = 3600.0,
        max_retries: int = 3,
    ) -> Job:
        with self._lock:
            self._seq += 1
            job = Job(
                id=f"job-{self._seq:05d}-{uuid.uuid4().hex[:8]}",
                plugin=plugin,
                payload=payload,
                gpu_allocated=gpu,
                ttl_seconds=ttl,
                max_retries=max_retries,
            )
            self._jobs[job.id] = job
            self._save()
            log.info(f"SUBMITTED: {job.id} ({plugin})")
            return job

    def schedule(self, job_id: str, worker_id: str) -> bool:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j or j.status != JobStatus.SUBMITTED:
                return False
            j.status = JobStatus.SCHEDULED
            j.worker_id = worker_id
            j.scheduled_at = time.time()
            self._save()
            log.info(f"SCHEDULED: {job_id} -> {worker_id}")
            return True

    def start(self, job_id: str) -> bool:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j or j.status != JobStatus.SCHEDULED:
                return False
            j.status = JobStatus.RUNNING
            j.started_at = time.time()
            self._save()
            log.info(f"STARTED: {job_id}")
            return True

    def complete(self, job_id: str) -> bool:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j or j.status != JobStatus.RUNNING:
                return False
            j.status = JobStatus.COMPLETED
            j.completed_at = time.time()
            self._save()
            log.info(f"COMPLETED: {job_id}")
            return True

    def commit(self, job_id: str) -> bool:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j or j.status != JobStatus.COMPLETED:
                return False
            j.status = JobStatus.COMMITTED
            self._save()
            log.info(f"COMMITTED: {job_id}")
            return True

    def fail(self, job_id: str, error: str) -> bool:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j or j.status not in (JobStatus.RUNNING, JobStatus.SCHEDULED):
                return False
            j.status = JobStatus.FAILED
            j.error = error
            j.completed_at = time.time()
            self._save()
            log.warning(f"FAILED: {job_id} - {error}")
            return True

    def requeue(self, job_id: str) -> bool:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return False
            if not j.is_retryable():
                j.status = JobStatus.DEAD
                self._save()
                log.error(f"DEAD (no retries): {job_id}")
                return False
            j.status = JobStatus.PENDING_RETRY
            j.worker_id = None
            j.retry_count += 1
            self._save()
            log.info(f"REQUEUED: {job_id} (attempt {j.retry_count}/{j.max_retries})")
            return True

    def advance_pending(self) -> list[Job]:
        with self._lock:
            ready = [j for j in self._jobs.values() if j.status == JobStatus.PENDING_RETRY]
            for j in ready:
                j.status = JobStatus.SUBMITTED
            if ready:
                self._save()
            return ready

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_by_worker(self, wid: str) -> list[Job]:
        with self._lock:
            return [j for j in self._jobs.values() if j.worker_id == wid]

    def list_pending(self) -> list[Job]:
        with self._lock:
            return [j for j in self._jobs.values() if j.status == JobStatus.SUBMITTED]

    def list_failed(self) -> list[Job]:
        with self._lock:
            return [j for j in self._jobs.values() if j.status == JobStatus.FAILED]

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {s.value: sum(1 for j in self._jobs.values() if j.status == s) for s in JobStatus}

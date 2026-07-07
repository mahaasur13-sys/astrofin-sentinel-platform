"""Reconciler — Self-Healing Control Loop"""

import time
import threading
import logging
from typing import Optional
from .core_models import JobStatus
from .registry import WorkerRegistry
from .job_store import JobStore
from .leases import GPULeaseManager

log = logging.getLogger("reconciler")


class Reconciler:
    def __init__(self, registry: WorkerRegistry, jobs: JobStore, leases: GPULeaseManager, ht: float = 15.0):
        self.reg = registry
        self.jobs = jobs
        self.leases = leases
        self._ht = ht
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tick_count: int = 0  # renamed: was _tick (shadowed method)

    def _tick(self):
        self._tick_count += 1
        recovered = 0

        for w in self.reg.list_all():
            if time.time() - w.last_heartbeat > self._ht and w.is_healthy():
                self.reg.mark_dead(w.id)
                log.warning(f"Worker {w.id} marked DEAD (heartbeat timeout)")

                for job in self.jobs.list_by_worker(w.id):
                    if job.status == JobStatus.RUNNING:
                        self.jobs.fail(job.id, f"Worker {w.id} died")
                        log.info(f"Job {job.id} marked FAILED (worker dead)")
                    if job.status in (JobStatus.SCHEDULED, JobStatus.FAILED):
                        if self.jobs.requeue(job.id):
                            recovered += 1
                            for i in range(int(job.gpu_allocated)):
                                self.leases.release(f"{w.id}-gpu-{i}", job.id)

        self.leases.cleanup_expired()

        ready = self.jobs.advance_pending()
        if ready:
            log.info(f"AdvancePending: {len(ready)} jobs back to SUBMITTED")

        log.debug(f"[Tick {self._tick_count}] recovered={recovered} healthy={len(self.reg.list_healthy())}")

    def start(self, interval: float = 5.0):
        self._running = True
        self._thread = threading.Thread(target=self._loop, args=(interval,), daemon=True)
        self._thread.start()
        log.info(f"Reconciler started (interval={interval}s)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self, interval: float):
        while self._running:
            try:
                self._tick()
            except Exception as e:
                log.error(f"Reconciler error: {e}")
            time.sleep(interval)

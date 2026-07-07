"""Worker Registry — Source of Truth"""

import time
import threading
import logging
from typing import Optional, List, Dict, Any
from .core_models import Worker, WorkerStatus

log = logging.getLogger("registry")


class WorkerRegistry:
    def __init__(self, heartbeat_timeout: float = 15.0):
        self._w: Dict[str, Worker] = {}
        self._lock = threading.RLock()
        self._ht = heartbeat_timeout

    def register(self, wid: str, gpu: float = 1.0, tags=None, addr: str = "") -> Worker:
        with self._lock:
            w = Worker(id=wid, gpu_total=gpu, status=WorkerStatus.HEALTHY, tags=tags or {}, addr=addr)
            self._w[wid] = w
            log.info(f"Registered {wid} ({gpu} GPU)")
            return w

    def heartbeat(self, wid: str, gpu_used: float = 0.0, active_jobs: int = 0) -> Optional[Worker]:
        with self._lock:
            w = self._w.get(wid)
            if w:
                w.gpu_used = gpu_used
                w.active_jobs = active_jobs
                w.touch()
                w.status = WorkerStatus.HEALTHY
                return w
            return None

    def mark_dead(self, wid: str):
        with self._lock:
            if wid in self._w:
                self._w[wid].status = WorkerStatus.DEAD
                log.warning(f"Worker {wid} DEAD")

    def get(self, wid: str) -> Optional[Worker]:
        with self._lock:
            return self._w.get(wid)

    def list_healthy(self) -> List[Worker]:
        with self._lock:
            return [w for w in self._w.values() if w.is_healthy() and (time.time() - w.last_heartbeat) < self._ht]

    def list_all(self) -> List[Worker]:
        with self._lock:
            return list(self._w.values())

    def select_best(self, gpu_needed: float = 1.0) -> Optional[Worker]:
        avail = [w for w in self.list_healthy() if w.gpu_free() >= gpu_needed]
        if not avail:
            return None
        return min(avail, key=lambda w: (w.gpu_used, w.active_jobs))

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._w)
            healthy = sum(1 for w in self._w.values() if w.is_healthy())
            dead = sum(1 for w in self._w.values() if w.status == WorkerStatus.DEAD)
            return {"total": total, "healthy": healthy, "dead": dead, "gpu_total": sum(w.gpu_total for w in self._w.values()), "gpu_used": sum(w.gpu_used for w in self._w.values())}

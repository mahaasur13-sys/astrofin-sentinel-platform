"""GPU Lease Manager — etcd-style distributed locking"""

import threading
import logging
from typing import Optional
from .core_models import GPULease

log = logging.getLogger("leases")


class GPULeaseManager:
    def __init__(self):
        self._leases: dict[str, GPULease] = {}
        self._lock = threading.RLock()

    def acquire(
        self, gpu_id: str, job_id: str, worker_id: str, ttl: float = 30.0
    ) -> bool:
        with self._lock:
            lease = self._leases.get(gpu_id)
            if lease is None or lease.is_expired():
                self._leases[gpu_id] = GPULease(
                    gpu_id=gpu_id, job_id=job_id, worker_id=worker_id, ttl=ttl
                )
                log.debug(f"Lease acquired: {gpu_id} -> job {job_id}")
                return True
            log.debug(f"Lease DENIED: {gpu_id} held by {lease.job_id}")
            return False

    def release(self, gpu_id: str, job_id: str) -> bool:
        with self._lock:
            lease = self._leases.get(gpu_id)
            if lease and lease.job_id == job_id:
                del self._leases[gpu_id]
                log.debug(f"Lease released: {gpu_id}")
                return True
            return False

    def renew(self, gpu_id: str, job_id: str) -> bool:
        with self._lock:
            lease = self._leases.get(gpu_id)
            if lease and lease.job_id == job_id:
                lease.renewed += 1
                return True
            return False

    def is_locked(self, gpu_id: str) -> bool:
        with self._lock:
            lease = self._leases.get(gpu_id)
            return lease is not None and not lease.is_expired()

    def get_holder(self, gpu_id: str) -> Optional[str]:
        with self._lock:
            lease = self._leases.get(gpu_id)
            return lease.job_id if lease and not lease.is_expired() else None

    def cleanup_expired(self) -> int:
        with self._lock:
            before = len(self._leases)
            self._leases = {k: v for k, v in self._leases.items() if not v.is_expired()}
            return before - len(self._leases)

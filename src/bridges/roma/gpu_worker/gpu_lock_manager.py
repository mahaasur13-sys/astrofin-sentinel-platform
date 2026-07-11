#!/usr/bin/env python3
"""GPU Lock Manager — prevents double execution on same GPU"""

import threading
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GPULock:
    gpu_id: str
    job_id: str
    acquired_at: datetime
    ttl_seconds: int


class GPULockManager:
    """
    Prevents two jobs from running on the same GPU simultaneously.
    Uses in-memory locks with TTL for crash-safe locking.
    For production: replace _locks with Redis for distributed locking.
    """

    def __init__(self, default_ttl: int = 3600):
        self._locks: Dict[str, GPULock] = {}
        self._mu = threading.Lock()
        self.default_ttl = default_ttl
        self._callbacks: Dict[str, callable] = {}  # gpu_id -> on_release callback

    def acquire(self, gpu_id: str, job_id: str, ttl: Optional[int] = None) -> bool:
        """
        Acquire lock on GPU for job.
        Returns True if acquired, False if GPU is already locked.
        """
        ttl = ttl or self.default_ttl
        with self._mu:
            if gpu_id in self._locks:
                existing = self._locks[gpu_id]
                # Check if lock has expired
                age = (datetime.utcnow() - existing.acquired_at).total_seconds()
                if age < ttl:
                    return False  # still locked
                # Lock expired, allow re-acquire
            self._locks[gpu_id] = GPULock(gpu_id=gpu_id, job_id=job_id, acquired_at=datetime.utcnow(), ttl_seconds=ttl)
            return True

    def release(self, gpu_id: str):
        """Release lock on GPU."""
        with self._mu:
            if gpu_id in self._locks:
                job_id = self._locks[gpu_id].job_id
                del self._locks[gpu_id]
                # Fire release callback if registered
                if gpu_id in self._callbacks:
                    try:
                        self._callbacks[gpu_id](job_id)
                    except Exception:  # noqa: BLE001
                        pass

    def is_locked(self, gpu_id: str) -> bool:
        with self._mu:
            if gpu_id not in self._locks:
                return False
            age = (datetime.utcnow() - self._locks[gpu_id].acquired_at).total_seconds()
            return age < self._locks[gpu_id].ttl_seconds

    def get_lock_holder(self, gpu_id: str) -> Optional[str]:
        """Return job_id holding the lock, or None."""
        with self._mu:
            if gpu_id in self._locks and self.is_locked(gpu_id):
                return self._locks[gpu_id].job_id
            return None

    def get_all_locks(self) -> List[GPULock]:
        with self._mu:
            return [lock for lock in self._locks.values() if self.is_locked(lock.gpu_id)]

    def cleanup_expired(self):
        """Remove expired locks."""
        with self._mu:
            now = datetime.utcnow()
            expired = [
                gpu_id
                for gpu_id, lock in self._locks.items()
                if (now - lock.acquired_at).total_seconds() >= lock.ttl_seconds
            ]
            for gpu_id in expired:
                del self._locks[gpu_id]
            return expired

    def force_release(self, gpu_id: str, job_id: str) -> bool:
        """Force release if job_id matches."""
        with self._mu:
            if gpu_id in self._locks and self._locks[gpu_id].job_id == job_id:
                del self._locks[gpu_id]
                return True
            return False

    def register_release_callback(self, gpu_id: str, cb: callable):
        """Register callback to fire when GPU is released."""
        self._callbacks[gpu_id] = cb

    def stats(self) -> Dict:
        with self._mu:
            return {
                "total_locks": len(self._locks),
                "locked_gpus": list(self._locks.keys()),
                "lock_details": [
                    {
                        "gpu_id": l.gpu_id,
                        "job_id": l.job_id,
                        "age_s": (datetime.utcnow() - l.acquired_at).total_seconds(),
                    }
                    for l in self._locks.values()
                ],
            }


if __name__ == "__main__":
    lock_mgr = GPULockManager(default_ttl=60)

    # Test basic locking
    assert lock_mgr.acquire("gpu-0", "job-001")
    assert not lock_mgr.acquire("gpu-0", "job-002")  # already locked
    assert lock_mgr.get_lock_holder("gpu-0") == "job-001"

    # Release and re-acquire
    lock_mgr.release("gpu-0")
    assert lock_mgr.acquire("gpu-0", "job-002")

    # Test multiple GPUs
    assert lock_mgr.acquire("gpu-1", "job-003")
    assert lock_mgr.acquire("gpu-2", "job-004")

    # Stats
    stats = lock_mgr.stats()
    print(f"Lock stats: {stats}")

    # Cleanup
    lock_mgr.release("gpu-0")
    lock_mgr.release("gpu-1")
    lock_mgr.release("gpu-2")
    expired = lock_mgr.cleanup_expired()
    print(f"Cleanup: {expired} expired locks")

    print("=== GPU Lock Manager: PASS ===")

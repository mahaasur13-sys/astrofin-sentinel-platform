#!/usr/bin/env python3
"""ROMA Worker Registry + Heartbeat System"""
import logging
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

log = logging.getLogger(__name__)


@dataclass
class WorkerStatus:
    worker_id: str
    gpu_util: float
    vram_used_gb: float
    vram_total_gb: float
    status: str  # healthy | degraded | dead
    last_heartbeat: datetime
    jobs_completed: int
    jobs_failed: int
    current_job: Optional[str] = None

class WorkerRegistry:
    def __init__(self):
        self._workers: Dict[str, WorkerStatus] = {}
        self._locks: Dict[str, str] = {}  # gpu_id -> job_id
        self._heartbeat_timeout = 30  # seconds
        self._mu = threading.Lock()

    def register_worker(self, worker_id: str, vram_total_gb: float = 8.0) -> bool:
        with self._mu:
            if worker_id in self._workers:
                return False
            self._workers[worker_id] = WorkerStatus(
                worker_id=worker_id,
                gpu_util=0.0,
                vram_used_gb=0.0,
                vram_total_gb=vram_total_gb,
                status="healthy",
                last_heartbeat=datetime.utcnow(),
                jobs_completed=0,
                jobs_failed=0
            )
            return True

    def heartbeat(self, worker_id: str, gpu_util: float,
                   vram_used_gb: float, status: str = "healthy",
                   current_job: Optional[str] = None) -> bool:
        with self._mu:
            if worker_id not in self._workers:
                return False
            ws = self._workers[worker_id]
            ws.gpu_util = gpu_util
            ws.vram_used_gb = vram_used_gb
            ws.status = status
            ws.last_heartbeat = datetime.utcnow()
            ws.current_job = current_job
            return True

    def get_worker(self, worker_id: str) -> Optional[WorkerStatus]:
        with self._mu:
            return self._workers.get(worker_id)

    def get_all_workers(self) -> List[WorkerStatus]:
        with self._mu:
            return list(self._workers.values())

    def get_available_workers(self, min_vram_gb: float = 4.0) -> List[WorkerStatus]:
        with self._mu:
            return [
                w for w in self._workers.values()
                if w.status == "healthy"
                and (w.vram_total_gb - w.vram_used_gb) >= min_vram_gb
                and w.current_job is None
            ]

    def mark_worker_dead(self, worker_id: str):
        with self._mu:
            if worker_id in self._workers:
                self._workers[worker_id].status = "dead"

    def heartbeat_timeout_check(self) -> List[str]:
        """Return list of dead worker IDs"""
        dead = []
        now = datetime.utcnow()
        with self._mu:
            for wid, ws in self._workers.items():
                if (now - ws.last_heartbeat).total_seconds() > self._heartbeat_timeout:
                    ws.status = "dead"
                    dead.append(wid)
        return dead

    def cleanup_dead_workers(self):
        with self._mu:
            self._workers = {
                wid: ws for wid, ws in self._workers.items()
                if ws.status != "dead"
            }

    def acquire_gpu_lock(self, worker_id: str, job_id: str) -> bool:
        with self._mu:
            if worker_id not in self._workers:
                return False
            ws = self._workers[worker_id]
            if ws.current_job is not None:
                return False
            ws.current_job = job_id
            return True

    def release_gpu_lock(self, worker_id: str):
        with self._mu:
            if worker_id in self._workers:
                self._workers[worker_id].current_job = None

    def job_completed(self, worker_id: str, success: bool):
        with self._mu:
            if worker_id in self._workers:
                ws = self._workers[worker_id]
                if success:
                    ws.jobs_completed += 1
                else:
                    ws.jobs_failed += 1
                ws.current_job = None

    def aggregate_gpu_usage(self) -> Dict:
        with self._mu:
            if not self._workers:
                return {"total_workers": 0, "avg_gpu_util": 0,
                        "total_vram_used_gb": 0, "total_vram_gb": 0}
            total_util = sum(w.gpu_util for w in self._workers.values())
            total_vram = sum(w.vram_used_gb for w in self._workers.values())
            total_cap = sum(w.vram_total_gb for w in self._workers.values())
            alive = [w for w in self._workers.values() if w.status == "healthy"]
            return {
                "total_workers": len(self._workers),
                "healthy_workers": len(alive),
                "avg_gpu_util": total_util / len(self._workers) if self._workers else 0,
                "total_vram_used_gb": round(total_vram, 2),
                "total_vram_gb": round(total_cap, 2),
                "utilization_pct": round((total_vram / total_cap * 100) if total_cap else 0, 1)
            }

    def to_dict(self) -> dict:
        return {wid: asdict(ws) for wid, ws in self._workers.items()}


if __name__ == "__main__":
    reg = WorkerRegistry()

    # Register 3 GPU workers
    assert reg.register_worker("gpu-node-1", vram_total_gb=8.0)
    assert reg.register_worker("gpu-node-2", vram_total_gb=24.0)
    assert reg.register_worker("gpu-node-3", vram_total_gb=24.0)

    # Simulate heartbeats
    assert reg.heartbeat("gpu-node-1", gpu_util=0.72, vram_used_gb=5.1)
    assert reg.heartbeat("gpu-node-2", gpu_util=0.45, vram_used_gb=12.0)
    assert reg.heartbeat("gpu-node-3", gpu_util=0.0, vram_used_gb=0.0)

    # Test lock acquisition
    assert reg.acquire_gpu_lock("gpu-node-1", "job-001")
    assert not reg.acquire_gpu_lock("gpu-node-1", "job-002")  # already locked

    # Release and re-acquire
    reg.release_gpu_lock("gpu-node-1")
    assert reg.acquire_gpu_lock("gpu-node-1", "job-002")

    # Mark job completed
    reg.job_completed("gpu-node-1", success=True)

    # Get available workers (need 4GB free)
    available = reg.get_available_workers(min_vram_gb=4.0)
    log.info(f"Available workers (need 4GB free): {[w.worker_id for w in available]}")

    # Get aggregate stats
    stats = reg.aggregate_gpu_usage()
    log.info(f"GPU usage: {stats}")

    log.info("=== Worker Registry: PASS ===")

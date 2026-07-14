#!/usr/bin/env python3
"""ROMA GPU Connector — Connects ROMA scheduler to GPU workers
Handles worker discovery, job dispatch, result collection."""

import os
import uuid
import asyncio
import logging
from typing import Optional

import requests

logger = logging.getLogger("roma.gpu_connector")

# =============================================================================
# Config
# =============================================================================
ROMA_GPU_WORKER_URL = os.getenv("ROMA_GPU_WORKER_URL", "http://localhost:8000")
ROMA_GPU_TIMEOUT = int(os.getenv("ROMA_GPU_TIMEOUT", "300"))
GPU_POOL_DISCOVERY = os.getenv("GPU_POOL_DISCOVERY", "static")  # static | dynamic


# =============================================================================
# GPU Worker Pool
# =============================================================================
class GPUWorkerPool:
    def __init__(self):
        self.workers: list[dict] = []
        self.active_jobs: dict[str, str] = {}  # job_id -> worker_id
        self._load_static_workers()

    def _load_static_workers(self):
        """Load workers from environment variables."""
        worker_urls = os.getenv("ROMA_GPU_WORKERS", ROMA_GPU_WORKER_URL)
        for url in worker_urls.split(","):
            url = url.strip()
            if url:
                self.workers.append(
                    {
                        "url": url,
                        "id": f"worker-{url.split('://')[1].split(':')[0]}",
                        "available": True,
                        "gpu_name": "unknown",
                        "load": 0,
                    }
                )

    def discover_workers(self) -> list[dict]:
        """Discover available GPU workers via health check."""
        discovered = []
        for worker in self.workers:
            try:
                resp = requests.get(f"{worker['url']}/health", timeout=2)
                if resp.status_code == 200:
                    data = resp.json()
                    worker["available"] = data.get("gpu_available", False)
                    worker["gpu_name"] = data.get("gpu_device", "unknown")
                    discovered.append(worker)
            except Exception:
                worker["available"] = False
        return discovered

    def select_worker(self) -> Optional[dict]:
        """Select least-loaded available worker."""
        available = [w for w in self.workers if w.get("available", False)]
        if not available:
            return None
        return min(available, key=lambda w: w.get("load", 0))

    async def submit_job(self, job: dict) -> dict:
        """Submit job to GPU worker and return result."""
        worker = self.select_worker()
        if not worker:
            return {"status": "no_worker_available", "job_id": job.get("job_id")}

        job_id = job.get("job_id", str(uuid.uuid4()))
        worker_id = worker["id"]

        self.active_jobs[job_id] = worker_id
        worker["load"] += 1

        try:
            payload = {
                "job_id": job_id,
                "command": job.get("command", "echo 'no command'"),
                "image": job.get("image"),
                "gpu": job.get("gpu", "any"),
                "memory": job.get("memory", "8GB"),
                "timeout": job.get("timeout", 3600),
                "environment": job.get("environment", {}),
                "mount_paths": job.get("mount_paths", {}),
            }

            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{worker['url']}/execute", json=payload, timeout=ROMA_GPU_TIMEOUT
                ),
            )

            if resp.status_code == 200:
                result = resp.json()
                result["worker_id"] = worker_id
                return result
            else:
                return {
                    "status": "worker_error",
                    "job_id": job_id,
                    "worker_id": worker_id,
                    "error": f"HTTP {resp.status_code}",
                }

        except requests.exceptions.Timeout:
            return {
                "status": "timeout",
                "job_id": job_id,
                "worker_id": worker_id,
                "error": "Job timed out on GPU worker",
            }
        except Exception as e:
            return {
                "status": "failed",
                "job_id": job_id,
                "worker_id": worker_id,
                "error": str(e),
            }
        finally:
            worker["load"] = max(0, worker["load"] - 1)
            self.active_jobs.pop(job_id, None)


# =============================================================================
# ROMA GPU Connector (singleton)
# =============================================================================
class ROMAGPUConnector:
    def __init__(self):
        self.pool = GPUWorkerPool()
        self.connected = len(self.pool.workers) > 0

    def is_available(self) -> bool:
        """Check if any GPU worker is available."""
        return self.pool.select_worker() is not None

    def get_worker_count(self) -> int:
        return len(self.pool.workers)

    async def execute(self, job: dict) -> dict:
        """Execute a job on GPU worker pool."""
        if not self.is_available():
            return {
                "status": "no_gpu_available",
                "job_id": job.get("job_id"),
                "message": "No GPU workers available in pool",
            }

        result = await self.pool.submit_job(job)

        if result.get("status") == "success":
            logger.info(
                f"Job {result['job_id']} completed on {result['worker_id']} in {result.get('duration_seconds', 0):.2f}s"
            )
        else:
            logger.warning(f"Job {result.get('job_id')} failed: {result.get('status')}")

        return result

    def get_metrics(self) -> dict:
        """Get GPU pool metrics."""
        workers = self.pool.discover_workers()
        return {
            "connector_available": self.is_available(),
            "worker_count": len(workers),
            "available_workers": len([w for w in workers if w.get("available")]),
            "workers": [
                {
                    "id": w["id"],
                    "url": w["url"],
                    "available": w.get("available", False),
                    "gpu": w.get("gpu_name", "unknown"),
                    "load": w.get("load", 0),
                }
                for w in workers
            ],
        }


# Singleton
_gpu_connector: Optional[ROMAGPUConnector] = None


def get_gpu_connector() -> ROMAGPUConnector:
    global _gpu_connector
    if _gpu_connector is None:
        _gpu_connector = ROMAGPUConnector()
    return _gpu_connector


# =============================================================================
# Convenience function for scheduler
# =============================================================================
async def execute_on_gpu(job: dict) -> dict:
    """High-level API: send job to GPU worker pool."""
    connector = get_gpu_connector()
    return await connector.execute(job)


# =============================================================================
# Demo / test
# =============================================================================
if __name__ == "__main__":

    async def demo():
        connector = get_gpu_connector()
        metrics = connector.get_metrics()

        print("=== ROMA GPU Connector ===")
        print(f"Available: {metrics['connector_available']}")
        print(f"Workers: {metrics['worker_count']}")
        print(f"URL: {ROMA_GPU_WORKER_URL}")

        # Test job
        test_job = {
            "job_id": f"test-{uuid.uuid4().hex[:8]}",
            "command": "echo 'ROM A GPU working!' && nvidia-smi --query-gpu=name --format=csv,noheader",
            "memory": "4GB",
            "timeout": 30,
        }

        print(f"\n--- Test job: {test_job['job_id']} ---")
        result = await connector.execute(test_job)
        print(f"Status: {result.get('status')}")
        print(f"Worker: {result.get('worker_id', 'none')}")
        print(f"Output: {result.get('stdout', result.get('error', ''))[:200]}")

    asyncio.run(demo())

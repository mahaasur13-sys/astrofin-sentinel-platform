#!/usr/bin/env python3
"""ROMA Scheduler — GPU-enabled task orchestration
Routes jobs to GPU workers based on cost/performance policy."""

import os
import asyncio
import logging
from typing import Optional

from scheduler.gpu_scheduler import GPUScheduler
from gpu_worker.connector import get_gpu_connector
from cost.gate import DecisionGate
from cost.predictor import CostPredictor
from queue_manager.queue_manager import QueueManager

logger = logging.getLogger("roma.scheduler")


class ROMAGPUScheduler:
    def __init__(self):
        qm = QueueManager()
        self.gpu_scheduler = GPUScheduler(queue_manager=qm)
        self.gpu_connector = get_gpu_connector()
        self.cost_gate = DecisionGate()
        self.predictor = CostPredictor()
        self.local_mode = os.getenv("ROMA_EXECUTION_MODE", "local")

    def route_job(self, job: dict) -> dict:
        gpu_required = job.get("gpu_required", True)

        prediction = self.predictor.predict(
            task=job.get("task_type", "default"),
            gpu_required=gpu_required,
            plugin_type=job.get("tenant_tier", "PRO")
        )

        gate_result = self.cost_gate.evaluate(
            task=job.get("task_type", "default"),
            gpu_required=gpu_required,
            tenant_id=job.get("tenant_id", "default"),
            plugin_type=job.get("plan_tier", "PRO")
        )

        if gpu_required and self.gpu_connector.is_available():
            if gate_result.get("decision") == "REJECTED":
                return {
                    "status": "rejected",
                    "reason": gate_result.get("reason"),
                    "estimated_cost": prediction.get("estimated_cost", 0)
                }
            execution_target = "gpu_worker"
        else:
            execution_target = "local"

        return {
            "status": "queued",
            "execution_target": execution_target,
            "job_id": job.get("job_id"),
            "estimated_cost": prediction.get("estimated_cost", 0),
            "gate_decision": gate_result.get("decision")
        }

    async def execute_job(self, job: dict) -> dict:
        route = self.route_job(job)
        if route.get("status") == "rejected":
            return route

        if route["execution_target"] == "gpu_worker":
            gpu_job = {
                "job_id": job.get("job_id"),
                "command": job.get("command"),
                "image": job.get("docker_image"),
                "gpu": job.get("gpu", "any"),
                "memory": job.get("memory", "8GB"),
                "timeout": job.get("timeout", 3600),
                "environment": job.get("environment", {})
            }
            result = await self.gpu_connector.execute(gpu_job)
            result["execution_target"] = "gpu_worker"
            return result
        else:
            return self._execute_local(job)

    def _execute_local(self, job: dict) -> dict:
        import shlex
        import subprocess

        # TODO(security): validate `command` against an allowlist of
        # permitted executables (e.g. {"echo", "nvidia-smi", "python3"})
        # before exec. shlex.split + shell=False closes the B602 vector
        # but a hostile job could still invoke any binary on PATH.

        raw_command = job.get("command", "echo 'local execution'")
        try:
            argv = shlex.split(raw_command) if isinstance(raw_command, str) else list(raw_command)
        except ValueError as exc:
            return {
                "status": "failed",
                "error": f"invalid command syntax: {exc}",
                "execution_target": "local",
            }

        if not argv:
            return {
                "status": "failed",
                "error": "empty command",
                "execution_target": "local",
            }

        try:
            result = subprocess.run(  # nosec B602 — shell=False; command is split via shlex
                argv,
                shell=False, capture_output=True, text=True,
                timeout=job.get("timeout", 300),
            )
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout, "stderr": result.stderr,
                "returncode": result.returncode, "execution_target": "local", "duration_seconds": 0
            }
        except subprocess.TimeoutExpired as e:
            return {"status": "failed", "error": f"timeout after {e.timeout}s", "execution_target": "local"}
        except FileNotFoundError as e:
            return {"status": "failed", "error": f"executable not found: {e.filename}", "execution_target": "local"}
        except Exception as e:  # noqa: BLE001 — surface unexpected failures to caller
            return {"status": "failed", "error": str(e), "execution_target": "local"}

    def get_status(self) -> dict:
        return {
            "execution_mode": self.local_mode,
            "gpu_available": self.gpu_connector.is_available(),
            "gpu_worker_count": self.gpu_connector.get_worker_count(),
            "gpu_metrics": self.gpu_connector.get_metrics()
        }


class ROMAJobExecutor:
    def __init__(self):
        self.scheduler = ROMAGPUScheduler()
        self.results: dict = {}

    async def submit(self, job: dict) -> dict:
        import uuid
        job_id = job.get("job_id") or str(uuid.uuid4())
        job["job_id"] = job_id
        route = self.scheduler.route_job(job)
        if route.get("status") == "rejected":
            return route

        async def run():
            return await self.scheduler.execute_job(job)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: asyncio.run(run()))
        self.results[job_id] = result
        return result

    def get_result(self, job_id: str) -> Optional[dict]:
        return self.results.get(job_id)

    def get_metrics(self) -> dict:
        return {"results_tracked": len(self.results), "scheduler": self.scheduler.get_status()}


_executor: Optional[ROMAJobExecutor] = None


def get_executor() -> ROMAJobExecutor:
    global _executor
    if _executor is None:
        _executor = ROMAJobExecutor()
    return _executor


if __name__ == "__main__":
    async def demo():
        executor = get_executor()
        print("=== ROMA GPU Scheduler ===")
        print(f"Status: {executor.get_metrics()}")

        gpu_job = {
            "job_id": "demo-gpu-001",
            "task_type": "ml_training",
            "command": "echo 'GPU ready!' && nvidia-smi --query-gpu=name --format=csv,noheader",
            "gpu_required": True,
            "memory": "8GB",
            "timeout": 30,
            "tenant_tier": "PRO"
        }

        print("\n--- Submit GPU job ---")
        result = await executor.submit(gpu_job)
        print(f"Status: {result.get('status')}")
        print(f"Target: {result.get('execution_target', 'unknown')}")
        print(f"Worker: {result.get('worker_id', 'none')}")
        print(f"Output: {result.get('stdout', result.get('error', ''))[:200]}")

        local_job = {
            "job_id": "demo-local-001",
            "task_type": "data_prep",
            "command": "echo 'Local execution'",
            "gpu_required": False,
            "tenant_tier": "FREE"
        }

        print("\n--- Submit local job ---")
        result = await executor.submit(local_job)
        print(f"Status: {result.get('status')}")
        print(f"Target: {result.get('execution_target')}")

    asyncio.run(demo())
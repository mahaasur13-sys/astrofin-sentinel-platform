#!/usr/bin/env python3
"""ROMA GPU Worker — Distributed Compute Execution Node
Receives jobs from ROMA control plane, executes on GPU, returns results."""

import os
import uuid
import subprocess
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

# =============================================================================
# Config
# =============================================================================
GPU_WORKER_HOST = os.getenv("GPU_WORKER_HOST", "0.0.0.0")
GPU_WORKER_PORT = int(os.getenv("GPU_WORKER_PORT", "8000"))
GPU_DEVICE = os.getenv("GPU_DEVICE", "0")  # NVIDIA GPU ID
GPU_MEMORY_LIMIT = os.getenv("GPU_MEMORY_LIMIT", "16GB")
WORKER_ID = os.getenv("WORKER_ID", f"gpu-worker-{uuid.uuid4().hex[:8]}")

# =============================================================================
# FastAPI App
# =============================================================================
app = FastAPI(title="ROMA GPU Worker", version="1.0.0")


# =============================================================================
# Models
# =============================================================================
class JobRequest(BaseModel):
    job_id: str
    command: str
    image: Optional[str] = None  # Docker image override
    gpu: str = "any"
    memory: str = "8GB"
    timeout: int = 3600
    environment: Optional[dict] = None
    mount_paths: Optional[dict] = None  # host_path:container_path


class JobResult(BaseModel):
    job_id: str
    worker_id: str
    status: str  # "success" | "failed" | "timeout"
    stdout: str
    stderr: str
    returncode: int
    duration_seconds: float
    gpu_used: str
    execution_context: dict


# =============================================================================
# State
# =============================================================================
class WorkerState:
    def __init__(self):
        self.jobs: dict = {}
        self.gpu_available: bool = self._check_gpu()
        self.cuda_visible_devices = os.getenv("CUDA_VISIBLE_DEVICES", GPU_DEVICE)

    def _check_gpu(self) -> bool:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:  # noqa: BLE001
            return False

    def register_job(self, job_id: str) -> None:
        self.jobs[job_id] = {
            "job_id": job_id,
            "worker_id": WORKER_ID,
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
        }

    def complete_job(self, job_id: str, result: dict) -> None:
        if job_id in self.jobs:
            self.jobs[job_id].update(result)


state = WorkerState()


# =============================================================================
# GPU Execution Engine
# =============================================================================
def build_docker_command(job: JobRequest) -> list:
    """Build Docker command for GPU job."""
    base_cmd = [
        "docker",
        "run",
        "--rm",
        "--gpus",
        f'"device={GPU_DEVICE}"',
        "-e",
        f"CUDA_VISIBLE_DEVICES={GPU_DEVICE}",
    ]

    # Memory limit
    mem_limit = job.memory.upper().replace("GB", "g").replace("MB", "m")
    base_cmd.extend(["--memory", mem_limit])

    # Timeout
    base_cmd.extend(["--user", f"{os.getuid()}:{os.getgid()}"])

    # Environment vars
    if job.environment:
        for k, v in job.environment.items():
            base_cmd.extend(["-e", f"{k}={v}"])

    # Mount paths
    if job.mount_paths:
        for host_path, container_path in job.mount_paths.items():
            base_cmd.extend(["-v", f"{host_path}:{container_path}"])

    # Working dir
    base_cmd.extend(["-w", "/workspace"])

    # Image or raw command
    if job.image:
        base_cmd.append(job.image)
        base_cmd.extend(job.command.split())
    else:
        base_cmd.append("ubuntu:22.04")
        base_cmd.extend(["bash", "-c", job.command])

    return base_cmd


def execute_job_sync(job: JobRequest) -> JobResult:
    """Execute a single GPU job synchronously."""
    start_time = asyncio.get_event_loop().time()

    state.register_job(job.job_id)

    try:
        if job.image:
            cmd = build_docker_command(job)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=job.timeout)
        else:
            result = subprocess.run(
                job.command, shell=True, capture_output=True, text=True, timeout=job.timeout, cwd="/workspace"
            )

        duration = asyncio.get_event_loop().time() - start_time

        status = "success" if result.returncode == 0 else "failed"

        return JobResult(
            job_id=job.job_id,
            worker_id=WORKER_ID,
            status=status,
            stdout=result.stdout[:10000],  # Truncate
            stderr=result.stderr[:5000],
            returncode=result.returncode,
            duration_seconds=duration,
            gpu_used=GPU_DEVICE,
            execution_context={
                "image": job.image,
                "command": job.command,
                "timeout": job.timeout,
                "memory": job.memory,
            },
        )

    except subprocess.TimeoutExpired:
        duration = asyncio.get_event_loop().time() - start_time
        return JobResult(
            job_id=job.job_id,
            worker_id=WORKER_ID,
            status="timeout",
            stdout="",
            stderr=f"Job exceeded timeout of {job.timeout}s",
            returncode=-1,
            duration_seconds=duration,
            gpu_used=GPU_DEVICE,
            execution_context={"timeout": job.timeout},
        )
    except Exception as e:  # noqa: BLE001
        duration = asyncio.get_event_loop().time() - start_time
        return JobResult(
            job_id=job.job_id,
            worker_id=WORKER_ID,
            status="failed",
            stdout="",
            stderr=str(e),
            returncode=-2,
            duration_seconds=duration,
            gpu_used=GPU_DEVICE,
            execution_context={"error": str(e)},
        )


# =============================================================================
# API Routes
# =============================================================================
@app.get("/")
def root():
    return {
        "service": "ROMA GPU Worker",
        "version": "1.0.0",
        "worker_id": WORKER_ID,
        "gpu_available": state.gpu_available,
        "gpu_device": GPU_DEVICE,
        "jobs_processed": len(state.jobs),
    }


@app.get("/health")
def health():
    return {"status": "healthy", "worker_id": WORKER_ID, "gpu_available": state.gpu_available}


@app.post("/execute", response_model=JobResult)
async def execute_job(job: JobRequest, background_tasks: BackgroundTasks):
    """Execute a GPU job. Runs in background to support ROMA async scheduling."""
    if not state.gpu_available:
        raise HTTPException(status_code=503, detail="GPU not available on this worker")

    # Run in background task for non-blocking response
    def run_sync():
        return execute_job_sync(job)

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_sync)

    state.complete_job(job.job_id, result.model_dump())

    return result


@app.get("/status/{job_id}")
def job_status(job_id: str):
    if job_id not in state.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return state.jobs[job_id]


@app.get("/metrics")
def metrics():
    """Worker metrics for ROMA observability."""
    total_jobs = len(state.jobs)
    completed = sum(1 for j in state.jobs.values() if j.get("status") in ("success", "failed", "timeout"))

    return {
        "worker_id": WORKER_ID,
        "gpu_available": state.gpu_available,
        "gpu_device": GPU_DEVICE,
        "total_jobs": total_jobs,
        "completed_jobs": completed,
        "active_jobs": total_jobs - completed,
        "jobs": list(state.jobs.values()),
    }


# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    import uvicorn

    print("=== ROMA GPU Worker ===")
    print(f"Worker ID: {WORKER_ID}")
    print(f"GPU Device: {GPU_DEVICE}")
    print(f"GPU Available: {state.gpu_available}")
    print(f"Listening on: {GPU_WORKER_HOST}:{GPU_WORKER_PORT}")
    uvicorn.run(app, host=GPU_WORKER_HOST, port=GPU_WORKER_PORT)

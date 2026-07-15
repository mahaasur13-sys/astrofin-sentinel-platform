#!/usr/bin/env python3
"""
AI Scheduler v2 — FastAPI Service
Data-driven policy engine: metrics → scoring → decision → routing.
"""
import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scheduler")

app = FastAPI(title="AI Scheduler v2", version="2.0.0")


class ScheduleRequest(BaseModel):
    job_type: str = "gpu"      # gpu | cpu | arm | vps
    memory_gb: int = 0
    priority: int = 5          # 1-10, higher = more urgent
    dataset_ceph: bool = False
    dataset_path: Optional[str] = None
    cpus: int = 1
    gpus: int = 0
    time_limit: Optional[str] = None


class ScheduleResponse(BaseModel):
    target: str
    partition: str
    scores: dict
    reason: str
    job_id: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/schedule", response_model=ScheduleResponse)
def schedule(req: ScheduleRequest):
    from .modules.policy import select_node

    if req.job_type not in ("gpu", "cpu", "arm", "vps"):
        raise HTTPException(status_code=400, detail=f"Unknown job_type: {req.job_type}")

    decision = select_node(
        job_type=req.job_type,
        memory_gb=req.memory_gb,
        priority=req.priority,
        dataset_ceph=req.dataset_ceph,
    )

    log.info(f"Schedule: job_type={req.job_type} → node={decision['node']} score={decision['score']}")

    return ScheduleResponse(
        target=decision["node"] or "queue",
        partition=decision["partition"],
        scores={},  # filled by /scores endpoint
        reason=decision["reason"],
    )


@app.get("/scores")
def scores(job_type: str = "gpu"):
    from .modules.scoring import rank_nodes
    from .modules.policy import ALL_NODES
    return rank_nodes(ALL_NODES, job_type)


@app.get("/metrics")
def metrics():
    from .modules.metrics import get_node_metrics
    from .modules.policy import ALL_NODES
    result = {}
    for n in ALL_NODES:
        if n:
            result[n] = get_node_metrics(n)
    return result


@app.post("/submit")
def submit(job_type: str = "gpu", script: str = "job.sh", partition: Optional[str] = None):
    """Submit job to selected partition via slurm wrapper."""
    import subprocess, uuid

    decision = schedule(ScheduleRequest(job_type=job_type))
    partition = partition or decision.partition
    job_id = str(uuid.uuid4())[:8]

    cmd = ["bash", str(Path(__file__).parent / "submit.sh"), partition, script, job_id]
    result = subprocess.run(cmd, capture_output=True, text=True)

    return {"job_id": job_id, "stdout": result.stdout, "stderr": result.stderr, "rc": result.returncode}


if __name__ == "__main__":
    port = int(os.environ.get("SCHEDULER_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

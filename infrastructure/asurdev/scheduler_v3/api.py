#!/usr/bin/env python3
"""
Scheduler v3 — FastAPI Service (stateful, DB-backed)
POST /schedule     — admission check → stateful scoring → Slurm submit
GET  /scores       — live node scores
GET  /jobs/:id     — job state
GET  /state        — cluster state snapshot from DB
GET  /metrics      — Prometheus metrics
"""
import os
import logging
import time
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest

from state_store import StateStore, JobStatus
from admission_controller import AdmissionController
from job_engine import JobEngine
from scheduler_v3.scorer import score_and_select

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger("scheduler_v3")

app = FastAPI(title="Home Cluster Scheduler v3", version="3.0.0")

# Config
PG_HOST   = os.environ.get("PG_HOST",   "localhost")
PG_PORT   = int(os.environ.get("PG_PORT", "5432"))
PG_DB     = os.environ.get("PG_DB",     "clusterdb")
PG_USER   = os.environ.get("PG_USER",   "clusteruser")
PG_PASS   = os.environ.get("PGPASS",   "clusterpass")

# Globals (lazy init)
_state_store: Optional[StateStore] = None
_admission:   Optional[AdmissionController] = None
_job_engine:  Optional[JobEngine] = None


def get_store() -> StateStore:
    global _state_store
    if _state_store is None:
        _state_store = StateStore(PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASS)
    return _state_store


def get_admission() -> AdmissionController:
    global _admission
    if _admission is None:
        _admission = AdmissionController(get_store())
    return _admission


def get_engine() -> JobEngine:
    global _job_engine
    if _job_engine is None:
        _job_engine = JobEngine(get_store(), get_admission())
    return _job_engine


# Prometheus metrics
SCHEDULER_REQUESTS = Counter(
    "scheduler_requests_total", "Total schedule requests",
    ["job_type", "decision"])
SCHEDULER_LATENCY  = Histogram("scheduler_latency_seconds", "Schedule latency")
SCHEDULER_SCORE    = Gauge("scheduler_node_score", "Node score",
                            ["hostname", "job_type"])


class ScheduleRequest(BaseModel):
    name:       str
    job_type:   str   = "gpu"   # gpu | cpu | arm | vps
    memory_gb:  int   = 8
    priority:   int   = 5
    script:     Optional[str] = None


class ScheduleResponse(BaseModel):
    submitted: bool
    job_id:    str
    reason:    str
    node:      Optional[str] = None
    wait_time: Optional[int] = None


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.post("/schedule", response_model=ScheduleResponse)
def schedule(req: ScheduleRequest):
    """
    Full lifecycle: admission → stateful scoring → job scheduled.
    Idempotent: duplicate submits are rejected at job_engine level.
    """
    start = time.time()
    try:
        engine = get_engine()

        # Step 1: Submit + admission check
        submitted, job_id, reason = engine.submit_job(
            name=req.name,
            job_type=req.job_type,
            memory_gb=req.memory_gb,
            priority=req.priority,
            script_path=req.script
        )

        if not submitted:
            SCHEDULER_REQUESTS.labels(job_type=req.job_type, decision="rejected").inc()
            return ScheduleResponse(submitted=False, job_id=job_id, reason=reason)

        # Step 2: Stateful node scoring
        job = get_store().get_job(job_id)
        best_node, all_scores = score_and_select(job, get_store())

        if not best_node:
            SCHEDULER_REQUESTS.labels(job_type=req.job_type, decision="no_node").inc()
            return ScheduleResponse(submitted=False, job_id=job_id,
                                    reason="no healthy node available")

        # Step 3: Record scores for determinism testing
        get_store().write_scheduler_decision(
            job_id, round_num=1,
            scores=all_scores,
            selected_node=best_node.hostname
        )

        # Step 4: Advance job to SCHEDULED (Slurm submit)
        ok, msg = engine.schedule_job(job_id, best_node.hostname)

        decision = "scheduled" if ok else "failed"
        SCHEDULER_REQUESTS.labels(job_type=req.job_type, decision=decision).inc()
        return ScheduleResponse(
            submitted=ok,
            job_id=job_id,
            reason=msg,
            node=best_node.hostname if ok else None
        )

    finally:
        SCHEDULER_LATENCY.observe(time.time() - start)


@app.get("/scores")
def get_scores(job_type: str = "gpu"):
    """Live node scores from DB state."""
    nodes = get_store().get_healthy_nodes()
    result = []
    for node in nodes:
        from scheduler_v3.scorer import _compute_score, _filter_eligible
        if job_type == "gpu" and node.gpu_count == 0:
            continue
        score = _compute_score(node, job_type, {
            "gpu": 0.5, "cpu": 0.2, "mem": 0.15,
            "latency": 0.10, "locality": 0.05
        })
        result.append({
            "hostname":  node.hostname,
            "score":     round(score["base_score"], 2),
            "gpu_load":  node.gpu_load_pct,
            "cpu_load":  node.cpu_load_pct,
            "memory_free_gb": round(node.memory_gb - node.memory_used_gb, 1),
            "status":    node.status.value,
        })
    return sorted(result, key=lambda x: x["score"], reverse=True)


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Get job state + event history."""
    store = get_store()
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    events = store.get_job_events(job_id)
    return {"job": job, "events": events}


@app.get("/state")
def get_state():
    """Cluster state snapshot from DB."""
    store = get_store()
    nodes = store.get_cluster_state()
    util  = store.get_total_utilization()
    pending = len(store.get_pending_jobs(limit=1000))
    return {"nodes": nodes["nodes"], "utilization": util,
            "pending_jobs": pending, "ts": nodes["ts"]}


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()


@app.get("/health")
def health():
    """Liveness probe."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

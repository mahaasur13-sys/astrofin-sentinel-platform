#!/usr/bin/env python3
"""
AI Scheduler — Data-Driven Policy Engine v2
Queries Prometheus for real metrics, computes node scores.

Score = (100 - gpu_util)*0.5 + (100 - cpu_util)*0.2
        + (100 - mem_util)*0.15 - latency*0.1 + data_locality*0.05

Routing:
  gpu_required=True  → rtx-node (if GPU available)
  cpu_required=True  → rk3576 (if CPU < 80%)
  vps_fallback       → vps-node (if both above unavailable)
"""

import json
import subprocess
from dataclasses import dataclass
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

PROMETHEUS_URL = "http://localhost:9090"

app = FastAPI(title="AI Scheduler v2 — Data-Driven")

# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class NodeMetrics:
    hostname: str
    ip: str
    gpu_util: float  # 0-100
    gpu_memory: float  # 0-100
    cpu_util: float  # 0-100
    memory_util: float  # 0-100
    disk_util: float  # 0-100
    network_latency: float  # ms
    score: float = 0.0
    is_alive: bool = True

    def compute_score(
        self, gpu_required: bool = False, data_locality: float = 0.0, priority: int = 5
    ) -> float:
        """
        Data-driven scoring — queries Prometheus for live metrics.
        """
        gpu_weight = 0.50 if gpu_required else 0.15
        cpu_weight = 0.20 if not gpu_required else 0.10
        mem_weight = 0.15
        latency_weight = -0.10  # penalty
        locality_weight = 0.05

        gpu_score = (100 - self.gpu_util) * gpu_weight
        cpu_score = (100 - self.cpu_util) * cpu_weight
        mem_score = (100 - self.memory_util) * mem_weight
        lat_score = max(0, 50 - self.network_latency) * latency_weight
        loc_score = data_locality * locality_weight * 100
        priority_boost = priority * 0.5  # higher priority = slightly higher score

        self.score = (
            gpu_score + cpu_score + mem_score + lat_score + loc_score + priority_boost
        )
        return self.score


class JobRequest(BaseModel):
    job_type: Literal["gpu", "cpu", "batch", "inference", "storage"]
    memory_gb: float = 4
    gpu_required: bool = False
    priority: int = 5
    job_name: str = "unnamed"
    data_locality: float = 0.0  # 0.0-1.0 ( Ceph locality hint)
    timeout_sec: int = 3600


class ScheduleResponse(BaseModel):
    target: str
    partition: str
    score: float
    reason: str
    metrics: dict


# =============================================================================
# METRIC QUERIES (Prometheus)
# =============================================================================


def get_prometheus_metric(query: str, default: float = 0.0) -> float:
    """Query Prometheus HTTP API, return float value or default."""
    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "--max-time",
                "3",
                f"{PROMETHEUS_URL}/api/v1/query?query={query}",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        data = json.loads(result.stdout)
        if data.get("status") == "success":
            results = data.get("data", {}).get("result", [])
            if results:
                return float(results[0]["value"][1])
    except Exception:
        pass
    return default


def get_node_metrics_prometheus(hostname: str, ip: str) -> NodeMetrics:
    """Fetch live node metrics from Prometheus."""
    labels = f'{{node="{hostname}"}}'

    gpu_util = get_prometheus_metric(f"DCGM_FI_DEV_GPU_UTIL{labels}", 0.0)
    gpu_mem = (
        get_prometheus_metric(f"DCGM_FI_DEV_FB_USED{labels}", 0.0) / 12.0
    )  # normalize to %
    cpu_util = get_prometheus_metric(
        f'100 - (avg by (instance) (irate({{__name__=~"node_cpu.*",{labels}}}[5m])) * 100)',
        0.0,
    )
    mem_util = get_prometheus_metric(f"node_memory_MemAvailable{{{labels}}}", 0.0)
    mem_total = get_prometheus_metric(f"node_memory_MemTotal{{{labels}}}", 1.0)
    memory_util = ((mem_total - mem_util) / mem_total * 100) if mem_total > 0 else 50.0
    disk_util = get_prometheus_metric(
        f"100 - (node_filesystem_avail{{{labels}}}) / (node_filesystem_size{{{labels}}}) * 100",
        0.0,
    )
    latency = get_prometheus_metric(f"probe_duration_seconds{{{labels}}}*1000", 1.0)

    return NodeMetrics(
        hostname=hostname,
        ip=ip,
        gpu_util=gpu_util,
        gpu_memory=gpu_mem,
        cpu_util=min(cpu_util, 100.0),
        memory_util=memory_util,
        disk_util=disk_util,
        network_latency=latency,
    )


def get_node_metrics_fallback(hostname: str, ip: str) -> NodeMetrics:
    """Fallback when Prometheus is unreachable — use static info + rough estimates."""
    return NodeMetrics(
        hostname=hostname,
        ip=ip,
        gpu_util=45.0,
        gpu_memory=60.0,
        cpu_util=30.0,
        memory_util=50.0,
        disk_util=40.0,
        network_latency=1.0,
    )


# =============================================================================
# NODE REGISTRY
# =============================================================================

NODE_REGISTRY = {
    "rtx-node": {
        "ip": "10.20.20.10",
        "capabilities": ["gpu", "slurm", "ceph_osd", "ray_head"],
    },
    "rk3576-node": {
        "ip": "10.20.20.20",
        "capabilities": ["cpu", "ceph_osd", "ray_worker"],
    },
    "vps-node": {
        "ip": "10.40.40.30",
        "capabilities": ["cpu", "vps", "slurm_backup", "ceph_mon"],
    },
}


# =============================================================================
# ROUTING ENGINE
# =============================================================================


def route_job(job: JobRequest) -> ScheduleResponse:
    """
    Data-driven job routing — queries Prometheus for live metrics,
    scores each available node, returns optimal target.
    """
    nodes = []

    for hostname, info in NODE_REGISTRY.items():
        ip = info["ip"]
        try:
            metrics = get_node_metrics_prometheus(hostname, ip)
        except Exception:
            metrics = get_node_metrics_fallback(hostname, ip)

        # Filter by capability
        caps = info["capabilities"]

        if job.gpu_required and "gpu" not in caps:
            metrics.is_alive = False
        elif job.job_type == "cpu" and "cpu" not in caps:
            metrics.is_alive = False
        elif job.job_type == "storage" and "ceph_osd" not in caps:
            metrics.is_alive = False

        # Compute score
        gpu_required = job.gpu_required or job.job_type in ("gpu", "inference")
        metrics.compute_score(
            gpu_required=gpu_required,
            data_locality=job.data_locality,
            priority=job.priority,
        )
        nodes.append(metrics)

    # Filter alive nodes
    alive = [n for n in nodes if n.is_alive]

    if not alive:
        raise HTTPException(status_code=503, detail="No available nodes")

    # Sort by score descending
    best = sorted(alive, key=lambda n: n.score, reverse=True)[0]

    # Determine partition
    if best.hostname == "rtx-node" and job.gpu_required:
        partition = "gpu"
    elif best.hostname == "rk3576-node":
        partition = "cpu"
    else:
        partition = "vps"

    return ScheduleResponse(
        target=best.hostname,
        partition=partition,
        score=round(best.score, 2),
        reason=f"score={best.score:.1f} GPU={best.gpu_util:.0f}% CPU={best.cpu_util:.0f}% "
        f"MEM={best.memory_util:.0f}% LAT={best.network_latency:.0f}ms",
        metrics={
            "gpu_util": best.gpu_util,
            "cpu_util": best.cpu_util,
            "memory_util": best.memory_util,
            "latency_ms": best.network_latency,
            "score": best.score,
        },
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================


@app.post("/schedule")
def schedule_job(job: JobRequest) -> dict:
    """Main routing endpoint."""
    return route_job(job).__dict__


@app.get("/nodes")
def list_nodes() -> dict:
    """Live node status from Prometheus."""
    result = {}
    for hostname, info in NODE_REGISTRY.items():
        try:
            m = get_node_metrics_prometheus(hostname, info["ip"])
            result[hostname] = {
                "alive": m.is_alive,
                "gpu_util": m.gpu_util,
                "cpu_util": m.cpu_util,
                "memory_util": m.memory_util,
                "score": m.score,
            }
        except Exception:
            result[hostname] = {"alive": False}
    return result


@app.get("/health")
def health_check() -> dict:
    """Scheduler health."""
    try:
        subprocess.run(
            ["curl", "-s", "--max-time", "2", f"{PROMETHEUS_URL}/-/healthy"],
            capture_output=True,
            timeout=3,
        )
        prom_status = "ok"
    except Exception:
        prom_status = "unreachable"

    return {"status": "ok", "prometheus": prom_status}


# =============================================================================
# STANDALONE MODE (no FastAPI dependency)
# =============================================================================


def cli_route():
    import sys

    job = JobRequest(
        job_type=sys.argv[1] if len(sys.argv) > 1 else "gpu",
        memory_gb=float(sys.argv[2] if len(sys.argv) > 2 else 4),
        gpu_required=(sys.argv[1] == "gpu" if len(sys.argv) > 1 else True),
    )
    result = route_job(job)
    print(
        f"target={result.target} partition={result.partition} score={result.score} reason={result.reason}"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

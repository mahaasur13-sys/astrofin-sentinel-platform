#!/usr/bin/env python3
"""
AI Scheduler v2 — Policy Engine
Top-level decision logic: routes jobs to best node based on scores + rules.
"""
import os
from typing import Optional
from .scoring import rank_nodes, score_node
from .metrics import (
    slurm_queue_depth, ceph_osd_latency, slurm_node_state,
    disk_io_time, gpu_temp
)


GPU_NODES = os.environ.get("GPU_NODES", "rtx-node").split(",")
CPU_NODES = os.environ.get("CPU_NODES", "rk3576").split(",")
ARM_NODES = os.environ.get("ARM_NODES", "").split(",") if os.environ.get("ARM_NODES") else []
VPS_NODES = os.environ.get("VPS_NODES", "").split(",") if os.environ.get("VPS_NODES") else []

ALL_NODES = GPU_NODES + CPU_NODES + ARM_NODES + VPS_NODES


def select_node(job_type: str = "gpu", memory_gb: int = 0, priority: int = 5,
                dataset_ceph: bool = False) -> dict:
    """
    Select optimal node for a job.
    Returns: {node, score, reason, partition}
    """
    scores = rank_nodes(ALL_NODES, job_type)

    if not scores:
        return {"node": None, "score": 0, "reason": "no_nodes", "partition": "fallback"}

    best_node = max(scores, key=scores.get)
    best_score = scores[best_node]

    if best_score <= 0:
        return {"node": "queue", "score": 0, "reason": "all_nodes_full", "partition": "gpu"}

    partition = _node_to_partition(best_node)
    reason = _build_reason(best_node, job_type, best_score)

    if gpu_temp(best_node) > 85:
        reason += " [GPU_HOT]"

    if slurm_queue_depth() > 50:
        reason += " [queue_busy]"

    return {
        "node": best_node,
        "score": best_score,
        "reason": reason,
        "partition": partition,
    }


def _node_to_partition(node: str) -> str:
    if node in GPU_NODES:
        return "gpu"
    elif node in CPU_NODES:
        return "cpu"
    elif node in ARM_NODES:
        return "arm"
    elif node in VPS_NODES:
        return "vps"
    return "default"


def _build_reason(node: str, job_type: str, score: float) -> str:
    parts = [f"type={job_type}", f"score={score}"]

    if node in GPU_NODES:
        parts.append("gpu_node")
    elif node in CPU_NODES:
        parts.append("cpu_node")
    elif node in ARM_NODES:
        parts.append("arm_node")

    ceph_lat = ceph_osd_latency()
    if ceph_lat > 50:
        parts.append(f"ceph_lat={ceph_lat:.0f}ms")
    if disk_io_time(node) > 80:
        parts.append("disk_io_high")

    return " | ".join(parts)

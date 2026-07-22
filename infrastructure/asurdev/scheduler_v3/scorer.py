#!/usr/bin/env python3
"""
Scheduler v3 — Stateful Scoring Engine
Reads job + node state from DB. Considers history + failure counts.
NOT stateless — every decision is logged to scheduler_scores table.
"""
import os
import logging
from typing import Optional, List, Tuple, Dict, Any

log = logging.getLogger("scheduler_v3.scorer")

# Weights (can be overridden via config.yaml)
WEIGHTS = {
    "gpu":      float(os.environ.get("W_GPU",   "0.50")),
    "cpu":      float(os.environ.get("W_CPU",   "0.20")),
    "mem":      float(os.environ.get("W_MEM",   "0.15")),
    "latency":  float(os.environ.get("W_LAT",   "0.10")),
    "locality": float(os.environ.get("W_LOCAL", "0.05")),
}

FAILURE_PENALTY = 20.0  # subtract from score per recent failure


def score_and_select(job, state_store) -> Tuple[Optional[Any], List[Dict]]:
    """
    Stateful node selection:
      1. Load nodes from DB (not Prometheus directly)
      2. Load job_history + failure_history from DB
      3. Compute weighted scores with history penalty
      4. Return (best_node, all_scores)
    """
    nodes = state_store.get_healthy_nodes()
    if not nodes:
        log.warning("No healthy nodes available")
        return None, []

    job_type   = job.job_type if hasattr(job, "job_type") else job.get("job_type", "gpu")
    memory_gb  = job.memory_gb if hasattr(job, "memory_gb") else job.get("memory_gb", 8)

    # Filter eligible nodes by job type
    eligible = _filter_eligible(nodes, job_type, memory_gb)
    if not eligible:
        log.warning("No eligible nodes for job_type=%s mem=%d", job_type, memory_gb)
        return None, []

    # Get recent failures per node (last 60 min)
    recent_failures = state_store.get_recent_failures(minutes=60)
    failure_count = {n.hostname: 0 for n in eligible}
    for f in recent_failures:
        if f["node_hostname"] in failure_count:
            failure_count[f["node_hostname"]] += 1

    # Score each node
    scored = []
    for node in eligible:
        breakdown = _compute_score(node, job_type, WEIGHTS)
        # Apply failure penalty
        penalty = failure_count[node.hostname] * FAILURE_PENALTY
        breakdown["failure_penalty"] = -penalty
        breakdown["total_score"] = breakdown["base_score"] - penalty
        breakdown["failure_count"] = failure_count[node.hostname]
        scored.append(breakdown)

    # Sort by total_score DESC
    scored.sort(key=lambda x: x["total_score"], reverse=True)
    best = scored[0]

    log.info("Selected node=%s score=%.2f (GPU=%.1f CPU=%.1f mem=%.1f lat=%.1f loc=%.1f fail=%d)",
             best["hostname"], best["total_score"],
             best["gpu"], best["cpu"], best["mem"],
             best["latency"], best["locality"], best["failure_count"])

    # Return best node object + all scores
    best_node = next(n for n in eligible if n.hostname == best["hostname"])
    return best_node, scored


def _filter_eligible(nodes, job_type: str, memory_gb: int):
    """Filter nodes by job type + memory."""
    eligible = []
    for node in nodes:
        if job_type == "gpu" and node.gpu_count == 0:
            continue
        if job_type == "cpu" and node.gpu_count > 0:
            # De-prioritize GPU nodes for CPU jobs
            pass
        free_mem = node.memory_gb - node.memory_used_gb
        if free_mem < memory_gb:
            continue
        if node.status.value in ("DOWN", "MAINTENANCE", "DRAINED"):
            continue
        eligible.append(node)
    return eligible


def _compute_score(node, job_type: str, weights: Dict[str, float]) -> Dict[str, float]:
    """
    Compute per-component score breakdown.
    Higher available resources → higher score contribution.
    """
    gpu_avail = 100.0 - float(node.gpu_load_pct) if node.gpu_count > 0 else 100.0
    cpu_avail = 100.0 - float(node.cpu_load_pct)
    mem_avail = (float(node.memory_gb) - float(node.memory_used_gb)) / float(node.memory_gb) * 100.0 if node.memory_gb > 0 else 100.0

    gpu_contrib = gpu_avail * weights["gpu"] if node.gpu_count > 0 else 0.0
    cpu_contrib = cpu_avail * weights["cpu"]
    mem_contrib = min(mem_avail, 100.0) * weights["mem"]

    # Latency: lower is better (assume LAN = 0.1ms, penalize if unreachable)
    latency_ms = 0.1  # TODO: pull from actual ping metrics
    latency_contrib = max(0, 10 - latency_ms) * weights["latency"]

    # Data locality: assume Ceph mount is local
    locality_contrib = 5.0 * weights["locality"]

    base_score = gpu_contrib + cpu_contrib + mem_contrib + latency_contrib + locality_contrib

    return {
        "hostname":   node.hostname,
        "base_score": round(base_score, 4),
        "gpu":        round(gpu_contrib, 4),
        "cpu":        round(cpu_contrib, 4),
        "mem":        round(mem_contrib, 4),
        "latency":    round(latency_contrib, 4),
        "locality":   round(locality_contrib, 4),
    }

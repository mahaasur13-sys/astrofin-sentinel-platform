#!/usr/bin/env python3
"""
AI Scheduler v2 — Scoring Engine
Computes weighted scores for node selection based on live metrics.
"""
from typing import Dict
from .metrics import get_node_metrics


WEIGHTS = {
    "gpu": 0.50,
    "cpu": 0.20,
    "mem": 0.15,
    "latency": 0.10,
    "data_locality": 0.05,
}


def score_node(node: str, job_type: str = "gpu", extra_weights: Dict = None) -> float:
    """
    Compute suitability score for a node.
    Higher = better. Range approximately 0-100.
    """
    m = get_node_metrics(node)
    w = WEIGHTS.copy()
    if extra_weights:
        w.update(extra_weights)

    gpu_free = max(0.0, 100.0 - m["gpu_util"])
    cpu_free = max(0.0, 100.0 - m["cpu_util"])
    mem_free = max(0.0, 100.0 - m["mem_util"])

    latency_penalty = m["network_latency"] * w["latency"] if m["network_latency"] else 0.0

    base_score = (
        gpu_free * w["gpu"]
        + cpu_free * w["cpu"]
        + mem_free * w["mem"]
        - latency_penalty
    )

    if job_type == "gpu":
        base_score *= 1.5
    elif job_type == "cpu" or job_type == "arm":
        base_score = (
            cpu_free * 0.7
            + mem_free * 0.3
            - latency_penalty
        )

    if m["gpu_util"] > 95:
        base_score = 0

    if m["slurm_queue"] > 100:
        base_score -= 20

    return round(base_score, 2)


def rank_nodes(nodes: list, job_type: str = "gpu") -> Dict[str, float]:
    """Return dict of node -> score, sorted descending."""
    results = {}
    for n in nodes:
        results[n] = score_node(n, job_type)
    return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

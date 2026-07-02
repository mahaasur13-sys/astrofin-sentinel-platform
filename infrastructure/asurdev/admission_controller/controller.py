#!/usr/bin/env python3
"""
Admission Controller — backpressure + resource gating
Prevents oversaturation: GPU >85%, queue >40, low-priority throttling.
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

log = logging.getLogger("admission")

GPU_SATURATION_THRESHOLD  = float(os.environ.get("GPU_SAT_THRESHOLD",  "0.85"))
QUEUE_DEPTH_THRESHOLD    = int(os.environ.get("QUEUE_DEPTH_THRESHOLD", "40"))
LOAD_THRESHOLD_LOW_PRI   = float(os.environ.get("LOAD_THRESHOLD_LOW",   "0.70"))


class AdmitDecision(str, Enum):
    ADMIT  = "ADMIT"
    REJECT = "REJECT"
    QUEUED = "QUEUED"


@dataclass
class AdmitResult:
    decision:  AdmitDecision
    reason:    str
    job_id:    Optional[str] = None
    wait_time: Optional[int] = None  # seconds to wait if queued


class AdmissionController:
    """
    Enforces cluster admission policy.
    All job submissions MUST pass through here before reaching the scheduler.
    """

    def __init__(self, state_store):
        self.state = state_store

    def admit(self, job: Dict[str, Any]) -> AdmitResult:
        """
        Returns (decision, reason, job_id_or_None).
        Decision is final — REJECT means no retry, QUEUED means retry after wait_time.
        """
        cluster_util = self.state.get_total_utilization()
        job_priority = job.get("priority", 5)
        job_type     = job.get("job_type", "gpu")

        # Rule 1: GPU saturation check (only for GPU jobs)
        if job_type == "gpu":
            total_gpu = cluster_util.get("total_gpu_count", 1)
            if total_gpu and total_gpu > 0:
                # Estimate cluster-wide GPU utilization
                avg_gpu = cluster_util.get("avg_gpu_load_pct", 0)
                if avg_gpu is not None and avg_gpu >= GPU_SATURATION_THRESHOLD * 100:
                    self.state.write_admission_decision(
                        job.get("id"), "REJECT",
                        f"GPU saturated {avg_gpu:.1f}% >= {GPU_SATURATION_THRESHOLD*100:.0f}%",
                        cluster_util
                    )
                    log.warning("REJECT GPU job %s: GPU saturated %.1f%%",
                                job.get("id"), avg_gpu)
                    return AdmitResult(
                        AdmitDecision.REJECT,
                        f"GPU saturated ({avg_gpu:.1f}%)",
                        job_id=job.get("id"))

        # Rule 2: Queue depth backpressure
        queue_depth = cluster_util.get("total_queue_depth", 0)
        if queue_depth >= QUEUE_DEPTH_THRESHOLD:
            wait_time = min(queue_depth * 10, 300)  # max 5 min
            self.state.write_admission_decision(
                job.get("id"), "QUEUED",
                f"Queue depth {queue_depth} >= {QUEUE_DEPTH_THRESHOLD}",
                cluster_util
            )
            log.warning("QUEUE GPU job %s: queue depth %d (wait %ds)",
                        job.get("id"), queue_depth, wait_time)
            return AdmitResult(
                AdmitDecision.QUEUED,
                f"Queue backpressure (depth={queue_depth})",
                job_id=job.get("id"),
                wait_time=wait_time)

        # Rule 3: Low-priority throttling under high load
        if job_priority <= 3:
            avg_load = cluster_util.get("avg_load", 0)
            if avg_load >= LOAD_THRESHOLD_LOW_PRI * 100:
                self.state.write_admission_decision(
                    job.get("id"), "REJECT",
                    f"Low priority throttled: load {avg_load:.1f}% >= {LOAD_THRESHOLD_LOW_PRI*100:.0f}%",
                    cluster_util
                )
                log.info("REJECT low-priority job %s: load %.1f%%",
                         job.get("id"), avg_load)
                return AdmitResult(
                    AdmitDecision.REJECT,
                    f"Low priority throttled (load={avg_load:.1f}%)",
                    job_id=job.get("id"))

        # Rule 4: Memory check (per-node)
        job_mem_gb = job.get("memory_gb", 8)
        if self._check_memory(job_mem_gb, job_type, cluster_util):
            self.state.write_admission_decision(
                job.get("id"), "ADMIT", "passed all checks", cluster_util)
            return AdmitResult(AdmitDecision.ADMIT, "accepted", job_id=job.get("id"))

        # Default: admit
        self.state.write_admission_decision(
            job.get("id"), "ADMIT", "no pressure", cluster_util)
        return AdmitResult(AdmitDecision.ADMIT, "accepted", job_id=job.get("id"))

    def _check_memory(self, job_mem_gb: int, job_type: str,
                      cluster_util: Dict) -> bool:
        """Check if any eligible node has enough free memory."""
        nodes = self.state.get_healthy_nodes()
        for node in nodes:
            if job_type == "gpu" and node.gpu_count == 0:
                continue
            if job_type == "cpu" and node.gpu_count > 0:
                # Prefer pure CPU nodes for CPU jobs
                continue
            free_mem = node.memory_gb - node.memory_used_gb
            if free_mem >= job_mem_gb:
                return True
        return False

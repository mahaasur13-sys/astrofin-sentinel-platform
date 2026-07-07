#!/usr/bin/env python3
# =============================================================================
# GPU Policy Engine v2 — Cluster-aware smart scheduling
# =============================================================================
# Features:
#   - Multi-node VRAM tracking
#   - Priority-based job queue with aging
#   - Batch size auto-tuning per job
#   - GPU lease management (1 job per GPU)
#   - Backpressure (queue saturation → reject/queue)
#   - Fair share scheduling (weighted by priority)
#   - Gang scheduling (multi-GPU jobs together)
# =============================================================================

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum


# ============================================================================
# Config
# ============================================================================


class RTX3060Config:
    VRAM_TOTAL_GB = 10.5
    VRAM_RESERVED_SYSTEM_GB = 1.5
    VRAM_SAFE_LIMIT_GB = 9.0
    MAX_CONCURRENT_JOBS = 1  # hard cap
    CUDA_DEVICE_COUNT = 1
    MIG_MODE = False


# ============================================================================
# Enums
# ============================================================================


class JobState(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SchedulingDecision(Enum):
    SCHEDULE_NOW = "schedule_now"
    QUEUE_PRIORITY = "queue_priority"
    QUEUE_FAIR = "queue_fair"
    REJECT_BACKPRESSURE = "reject_backpressure"
    REJECT_GPU_UNAVAILABLE = "reject_gpu_unavailable"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class VRAMAllocation:
    job_id: str
    allocated_gb: float
    timestamp: float


@dataclass
class GPUPolicyResult:
    decision: SchedulingDecision
    assigned_node: Optional[str]
    assigned_vram_gb: Optional[float]
    auto_batch_size: Optional[int]
    queue_position: Optional[int]
    rejection_reason: Optional[str]
    wait_estimate_seconds: Optional[float]


@dataclass
class JobMetrics:
    job_id: str
    priority: int
    vram_requested_gb: float
    age_seconds: float
    wait_time_seconds: float
    backpressure_ratio: float
    estimated_run_time_seconds: float


# ============================================================================
# GPU Node State
# ============================================================================


class GPUNode:
    def __init__(self, name: str, vram_total_gb: float = RTX3060Config.VRAM_TOTAL_GB):
        self.name = name
        self.vram_total_gb = vram_total_gb
        self.vram_used_gb = 0.0
        self.allocations: Dict[str, VRAMAllocation] = {}
        self.active_job_ids: List[str] = []
        self.last_updated = time.time()

    @property
    def vram_free_gb(self) -> float:
        return self.vram_total_gb - self.vram_used_gb

    @property
    def can_allocate(self) -> bool:
        return len(self.active_job_ids) < RTX3060Config.MAX_CONCURRENT_JOBS and self.vram_free_gb >= 2.0  # min 2GB

    @property
    def utilization_ratio(self) -> float:
        if self.vram_total_gb == 0:
            return 0.0
        return self.vram_used_gb / self.vram_total_gb

    def allocate(self, job_id: str, vram_gb: float) -> bool:
        if job_id in self.active_job_ids:
            return True
        if not self.can_allocate:
            return False
        if vram_gb > self.vram_free_gb:
            return False

        self.allocations[job_id] = VRAMAllocation(job_id=job_id, allocated_gb=vram_gb, timestamp=time.time())
        self.active_job_ids.append(job_id)
        self.vram_used_gb += vram_gb
        self.last_updated = time.time()
        return True

    def release(self, job_id: str) -> None:
        if job_id not in self.active_job_ids:
            return
        alloc = self.allocations.pop(job_id, None)
        if alloc:
            self.vram_used_gb -= alloc.allocated_gb
        self.active_job_ids.remove(job_id)
        self.last_updated = time.time()

    def release_all(self) -> None:
        self.allocations.clear()
        self.active_job_ids.clear()
        self.vram_used_gb = 0.0
        self.last_updated = time.time()


# ============================================================================
# Policy Engine v2
# ============================================================================


class GPUPolicyEngineV2:
    def __init__(self):
        self.nodes: Dict[str, GPUNode] = {}
        self.pending_jobs: List[JobMetrics] = []
        self.backpressure_threshold = 0.85  # reject new jobs at 85% queue saturation
        self.max_queue_depth = 50
        self.fair_share_weight_factor = 1.5  # priority weight multiplier for aging

    def register_node(self, name: str, vram_gb: float = RTX3060Config.VRAM_TOTAL_GB) -> None:
        self.nodes[name] = GPUNode(name, vram_gb)

    def unregister_node(self, name: str) -> None:
        if name in self.nodes:
            self.nodes[name].release_all()
            del self.nodes[name]

    def release_job(self, job_id: str, node_name: Optional[str] = None) -> None:
        if node_name and node_name in self.nodes:
            self.nodes[node_name].release(job_id)
        else:
            for node in self.nodes.values():
                node.release(job_id)

    def compute_batch_size(self, vram_requested_gb: float, node: GPUNode) -> int:
        free_vram = node.vram_free_gb
        if free_vram < vram_requested_gb:
            return 1
        available_for_job = min(free_vram - vram_requested_gb, RTX3060Config.VRAM_SAFE_LIMIT_GB)
        estimated_images_per_gb = 4
        base_batch = int(available_for_job * estimated_images_per_gb)
        return max(1, min(base_batch, 32))  # clamp 1..32

    def compute_wait_estimate(self, job: JobMetrics) -> float:
        queued_ahead = sum(1 for j in self.pending_jobs if j.priority > job.priority)
        avg_run_time = job.estimated_run_time_seconds or 300.0
        return queued_ahead * avg_run_time

    def apply_backpressure(self, metrics: JobMetrics) -> bool:
        queue_saturation = len(self.pending_jobs) / self.max_queue_depth
        if queue_saturation >= self.backpressure_threshold:
            return True
        node_utilization = sum(n.utilization_ratio for n in self.nodes.values()) / max(1, len(self.nodes))
        if node_utilization >= 0.9:
            return True
        return False

    def select_best_node(self, vram_gb: float) -> Optional[GPUNode]:
        candidates = [n for n in self.nodes.values() if n.can_allocate and n.vram_free_gb >= vram_gb]
        if not candidates:
            return None
        return min(candidates, key=lambda n: n.utilization_ratio)

    def age_jobs(self) -> None:
        now = time.time()
        for job in self.pending_jobs:
            job.age_seconds = now - (getattr(job, "enqueued_at", now))
            job.wait_time_seconds = job.age_seconds

    def schedule(self, job_id: str, priority: int, vram_requested_gb: float, estimated_run_time: float = 300.0) -> GPUPolicyResult:

        job_metrics = JobMetrics(
            job_id=job_id,
            priority=priority,
            vram_requested_gb=vram_requested_gb,
            age_seconds=0.0,
            wait_time_seconds=0.0,
            backpressure_ratio=len(self.pending_jobs) / self.max_queue_depth,
            estimated_run_time_seconds=estimated_run_time,
        )

        # Backpressure check
        if self.apply_backpressure(job_metrics):
            return GPUPolicyResult(
                decision=SchedulingDecision.REJECT_BACKPRESSURE,
                assigned_node=None,
                assigned_vram_gb=None,
                auto_batch_size=None,
                queue_position=None,
                rejection_reason=f"Queue saturation {job_metrics.backpressure_ratio:.2f} >= {self.backpressure_threshold}",
                wait_estimate_seconds=None,
            )

        # Node selection
        node = self.select_best_node(vram_requested_gb)

        if node:
            batch_size = self.compute_batch_size(vram_requested_gb, node)
            node.allocate(job_id, vram_requested_gb)
            return GPUPolicyResult(
                decision=SchedulingDecision.SCHEDULE_NOW,
                assigned_node=node.name,
                assigned_vram_gb=vram_requested_gb,
                auto_batch_size=batch_size,
                queue_position=None,
                rejection_reason=None,
                wait_estimate_seconds=0.0,
            )

        # Queue with priority + aging
        wait_estimate = self.compute_wait_estimate(job_metrics)
        queue_position = len(self.pending_jobs) + 1

        # Aging: boost priority for older jobs
        aged_priority = priority + int(job_metrics.age_seconds / 60) * self.fair_share_weight_factor
        job_metrics.priority = aged_priority

        self.pending_jobs.append(job_metrics)
        self.pending_jobs.sort(key=lambda j: (-j.priority, j.age_seconds))

        return GPUPolicyResult(
            decision=SchedulingDecision.QUEUE_PRIORITY,
            assigned_node=None,
            assigned_vram_gb=None,
            auto_batch_size=None,
            queue_position=queue_position,
            rejection_reason=None,
            wait_estimate_seconds=wait_estimate,
        )

    def get_status(self) -> Dict:
        total_vram = sum(n.vram_total_gb for n in self.nodes.values())
        used_vram = sum(n.vram_used_gb for n in self.nodes.values())
        free_vram = sum(n.vram_free_gb for n in self.nodes.values())
        avg_util = sum(n.utilization_ratio for n in self.nodes.values()) / max(1, len(self.nodes))
        queue_depth = len(self.pending_jobs)
        queue_saturation = queue_depth / self.max_queue_depth

        node_states = []
        for name, node in self.nodes.items():
            node_states.append(
                {
                    "name": name,
                    "vram_used_gb": round(node.vram_used_gb, 2),
                    "vram_free_gb": round(node.vram_free_gb, 2),
                    "utilization": round(node.utilization_ratio, 3),
                    "active_jobs": node.active_job_ids.copy(),
                }
            )

        return {
            "nodes": node_states,
            "cluster_vram_total_gb": round(total_vram, 2),
            "cluster_vram_used_gb": round(used_vram, 2),
            "cluster_vram_free_gb": round(free_vram, 2),
            "cluster_avg_utilization": round(avg_util, 3),
            "queue_depth": queue_depth,
            "queue_saturation": round(queue_saturation, 3),
            "backpressure_threshold": self.backpressure_threshold,
            "max_queue_depth": self.max_queue_depth,
            "decision": "ready",
        }


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    engine = GPUPolicyEngineV2()
    engine.register_node("gpu-node-1")
    engine.register_node("gpu-node-2")

    # Test scheduling
    result = engine.schedule("job-001", priority=5, vram_requested_gb=4.0)
    print(f"Job 001: {result.decision.value} → node={result.assigned_node}, batch={result.auto_batch_size}")

    result = engine.schedule("job-002", priority=8, vram_requested_gb=6.0)
    print(f"Job 002: {result.decision.value} → node={result.assigned_node}")

    result = engine.schedule("job-003", priority=3, vram_requested_gb=4.0)
    print(f"Job 003: {result.decision.value} → queue_pos={result.queue_position}, wait={result.wait_estimate_seconds}s")

    import json

    print(json.dumps(engine.get_status(), indent=2))

    # Release
    engine.release_job("job-001", "gpu-node-1")
    print("Released job-001")
    print(json.dumps(engine.get_status(), indent=2))

#!/usr/bin/env python3
"""
Synthetic Scheduler — injects jobs into simulated cluster state.
Used when real Slurm/System76 is not available.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import random
from ..workload.types import WorkloadProfile
from ..workload.generator import WorkloadGenerator, Job


@dataclass
class NodeState:
    """Simulated compute node."""
    node_id: str
    cpu_cores: int
    gpu_count: int
    memory_gb: int
    load: float = 0.0          # 0..1
    gpu_load: float = 0.0      # 0..1
    active_jobs: int = 0
    failed_jobs: int = 0


@dataclass
class JobResult:
    """Result of job execution in simulator."""
    job_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    exit_code: int
    node: Optional[str]
    wait_time_sec: float
    runtime_sec: float
    scheduled: bool = False


@dataclass
class InjectionResult:
    """Full injection cycle result."""
    scenario: str
    submitted: int
    scheduled: int
    completed: int
    failed: int
    p50_wait_sec: float
    p99_wait_sec: float
    p50_runtime_sec: float
    p99_runtime_sec: float
    queue_depth_peak: int
    node_states: dict[str, NodeState]


class SyntheticScheduler:
    """
    Simulates Slurm scheduling decisions under load.
    Realistic: respects GPU/CPU/memory constraints.
    Used for load testing when real cluster is not available.
    """

    def __init__(self, nodes: list[NodeState], seed: int = 42):
        self.nodes = {n.node_id: n for n in nodes}
        self._rng = random.Random(seed)
        self._queue: list[Job] = []
        self._running: list[tuple[Job, datetime]] = []
        self._completed: list[JobResult] = []

    def submit(self, stream) -> InjectionResult:
        """Run full injection from WorkloadStream."""
        for job in stream.jobs:
            self._queue.append(job)
        return self._run_simulation()

    def _run_simulation(self) -> InjectionResult:
        """Discrete-event simulation of job scheduling."""
        completed = []
        max_queue = 0

        # Sort queue by priority then submission time
        self._queue.sort(key=lambda j: (-j.priority, j.submitted_at))

        # Simple FCFS with priority — for simulation
        while self._queue or self._running:
            # Schedule from queue
            while self._queue:
                job = self._queue.pop(0)
                assigned = self._try_schedule(job)
                if not assigned:
                    # Re-queue
                    self._queue.insert(0, job)
                    break
                else:
                    self._running.append((job, datetime.utcnow()))
                    max_queue = max(max_queue, len(self._queue))

            # Advance time: complete shortest running job
            if self._running:
                self._running.sort(key=lambda x: x[1])
                job, start = self._running.pop(0)
                exit_code = 1 if job.failure_injected else 0
                wait = (datetime.utcnow() - start).total_seconds()
                result = JobResult(
                    job_id=job.job_id,
                    started_at=start,
                    completed_at=datetime.utcnow(),
                    exit_code=exit_code,
                    node=job.target_node,
                    wait_time_sec=wait,
                    runtime_sec=job.runtime_sec,
                    scheduled=True,
                )
                completed.append(result)

        wait_times = [r.wait_time_sec for r in completed]
        runtimes = [r.runtime_sec for r in completed]
        return InjectionResult(
            scenario="synthetic",
            submitted=len(completed),
            scheduled=sum(1 for r in completed if r.scheduled),
            completed=sum(1 for r in completed if r.exit_code == 0),
            failed=sum(1 for r in completed if r.exit_code != 0),
            p50_wait_sec=float(sorted(wait_times)[len(wait_times)//2]) if wait_times else 0,
            p99_wait_sec=float(sorted(wait_times)[int(len(wait_times)*0.99)]) if len(wait_times) > 10 else 0,
            p50_runtime_sec=float(sorted(runtimes)[len(runtimes)//2]) if runtimes else 0,
            p99_runtime_sec=float(sorted(runtimes)[int(len(runtimes)*0.99)]) if len(runtimes) > 10 else 0,
            queue_depth_peak=max_queue,
            node_states={k: v for k, v in self.nodes.items()},
        )

    def _try_schedule(self, job: Job) -> bool:
        """Try to assign job to a node. Returns True if scheduled."""
        candidates = []
        for node_id, node in self.nodes.items():
            if job.gpu_required and node.gpu_count == 0:
                continue
            if node.load >= 1.0:
                continue
            candidates.append((node_id, node))

        if not candidates:
            return False

        # Pick least-loaded candidate
        best = min(candidates, key=lambda x: x[1].load)
        node = best[1]

        if job.gpu_required:
            node.gpu_load = min(1.0, node.gpu_load + 0.5)
        node.load = min(1.0, node.load + (1.0 / node.cpu_cores))
        node.active_jobs += 1
        if job.failure_injected:
            node.failed_jobs += 1
        return True

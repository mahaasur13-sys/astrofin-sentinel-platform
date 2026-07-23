"""ROMA Control Plane — Core Models"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class WorkerStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DEAD = "DEAD"
    UNKNOWN = "UNKNOWN"


class JobStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    DEAD = "DEAD"
    PENDING_RETRY = "PENDING_RETRY"


@dataclass
class Worker:
    id: str
    status: WorkerStatus = WorkerStatus.UNKNOWN
    gpu_total: float = 1.0
    gpu_used: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)
    active_jobs: int = 0
    tags: dict[str, str] = field(default_factory=dict)
    addr: str = ""

    def gpu_free(self) -> float:
        return max(0.0, self.gpu_total - self.gpu_used)

    def is_healthy(self) -> bool:
        return self.status == WorkerStatus.HEALTHY

    def touch(self):
        self.last_heartbeat = time.time()


@dataclass
class GPULease:
    gpu_id: str
    job_id: str
    worker_id: str
    ttl: float = 30.0
    created_at: float = field(default_factory=time.time)
    renewed: int = 0

    def is_expired(self) -> bool:
        return time.time() > (self.created_at + self.ttl * (1 + self.renewed))


@dataclass
class Job:
    id: str
    plugin: str
    payload: dict[str, Any]
    status: JobStatus = JobStatus.SUBMITTED
    worker_id: str | None = None
    gpu_allocated: float = 0.0
    scheduled_at: float | None = None
    started_at: float | None = None
    completed_at: float | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    ttl_seconds: float = 3600.0
    tags: dict[str, str] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return self.status in (
            JobStatus.COMPLETED,
            JobStatus.COMMITTED,
            JobStatus.DEAD,
            JobStatus.FAILED,
        )

    def is_retryable(self) -> bool:
        return self.retry_count < self.max_retries and self.status in (
            JobStatus.FAILED,
            JobStatus.DEAD,
        )

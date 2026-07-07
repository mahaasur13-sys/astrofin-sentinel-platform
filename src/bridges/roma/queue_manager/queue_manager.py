#!/usr/bin/env python3
"""ROMA Queue Manager — In-memory job queue with persistence"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    job_id: str
    task_type: str
    command: str
    status: JobStatus = JobStatus.PENDING
    priority: int = 0
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    gpu_required: bool = True
    tenant_id: str = "default"
    result: Optional[dict] = None
    error: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class QueueManager:
    def __init__(self):
        self.queue: list[Job] = []
        self.completed: list[Job] = []
        self.running: dict[str, Job] = {}

    def enqueue(self, job: Job) -> str:
        job_id = job.job_id or str(uuid.uuid4())
        job.job_id = job_id
        self.queue.append(job)
        self.queue.sort(key=lambda j: j.priority, reverse=True)
        return job_id

    def dequeue(self) -> Optional[Job]:
        if not self.queue:
            return None
        job = self.queue.pop(0)
        job.status = JobStatus.QUEUED
        return job

    def start(self, job_id: str) -> bool:
        for job in self.queue:
            if job.job_id == job_id:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.utcnow().isoformat()
                self.running[job_id] = job
                return True
        return False

    def complete(self, job_id: str, result: dict) -> bool:
        if job_id in self.running:
            job = self.running.pop(job_id)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow().isoformat()
            job.result = result
            self.completed.append(job)
            return True
        return False

    def fail(self, job_id: str, error: str) -> bool:
        if job_id in self.running:
            job = self.running.pop(job_id)
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow().isoformat()
            job.error = error
            self.completed.append(job)
            return True
        return False

    def get_status(self, job_id: str) -> Optional[JobStatus]:
        for job in self.queue:
            if job.job_id == job_id:
                return job.status
        if job_id in self.running:
            return JobStatus.RUNNING
        for job in self.completed:
            if job.job_id == job_id:
                return job.status
        return None

    def get_queue_depth(self) -> int:
        return len(self.queue)

    def get_metrics(self) -> dict:
        return {"queue_depth": len(self.queue), "running": len(self.running), "completed": len(self.completed), "total": len(self.queue) + len(self.running) + len(self.completed)}


# =============================================================================
# Singleton
# =============================================================================
_queue: Optional[QueueManager] = None


def get_queue() -> QueueManager:
    global _queue
    if _queue is None:
        _queue = QueueManager()
    return _queue

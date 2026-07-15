#!/usr/bin/env python3
"""ROMA Projection Engine — Read Model for UI."""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum

class EventType(str, Enum):
    JOB_SUBMITTED = "JOB_SUBMITTED"
    JOB_QUEUED = "JOB_QUEUED"
    JOB_SCHEDULED = "JOB_SCHEDULED"
    JOB_STARTED = "JOB_STARTED"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_FAILED = "JOB_FAILED"
    QUOTA_CHECKED = "QUOTA_CHECKED"
    COST_ESTIMATED = "COST_ESTIMATED"

@dataclass
class JobProjection:
    job_id: str
    tenant_id: str
    plugin: str
    status: str
    submitted_at: int
    started_at: Optional[int]
    completed_at: Optional[int]
    gpu_assigned: Optional[str]
    cost_final: float
    duration_ms: Optional[int]
    failure_reason: Optional[str]
    events: List[Dict]
    dag: Dict[str, List[str]]

class ProjectionEngine:
    def __init__(self):
        self.events: List[Dict] = []
        self.jobs: Dict[str, JobProjection] = {}
        self.gpu_state: Dict[str, Dict] = {}
        self.cost_stream: List[Dict] = []
        self.raft_state: Dict[str, Any] = {}

    def ingest(self, event: Dict):
        self.events.append(event)
        et = event.get("type")
        payload = event.get("payload", {})

        if et == EventType.JOB_SUBMITTED.value:
            j = JobProjection(
                job_id=payload["job_id"],
                tenant_id=payload["tenant_id"],
                plugin=payload.get("plugin", "default"),
                status="SUBMITTED",
                submitted_at=event.get("ts", 0),
                started_at=None, completed_at=None,
                gpu_assigned=None, cost_final=0.0,
                duration_ms=None, failure_reason=None,
                events=[], dag={}
            )
            self.jobs[j.job_id] = j

        elif et == EventType.JOB_QUEUED.value:
            j = self.jobs.get(payload["job_id"])
            if j:
                j.status = "QUEUED"

        elif et == EventType.JOB_SCHEDULED.value:
            j = self.jobs.get(payload["job_id"])
            if j:
                j.status = "SCHEDULED"
                j.gpu_assigned = payload.get("gpu_node")

        elif et == EventType.JOB_STARTED.value:
            j = self.jobs.get(payload["job_id"])
            if j:
                j.status = "RUNNING"
                j.started_at = event.get("ts")

        elif et == EventType.JOB_COMPLETED.value:
            j = self.jobs.get(payload["job_id"])
            if j:
                j.status = "COMPLETED"
                j.completed_at = event.get("ts")
                j.cost_final = payload.get("cost", 0.0)
                if j.started_at:
                    j.duration_ms = j.completed_at - j.started_at

        elif et == EventType.JOB_FAILED.value:
            j = self.jobs.get(payload["job_id"])
            if j:
                j.status = "FAILED"
                j.failure_reason = payload.get("reason")
                j.completed_at = event.get("ts")

        elif et == "GPU_STATE_SNAPSHOT":
            self.gpu_state = payload

        elif et == "RAFT_STATE_SNAPSHOT":
            self.raft_state = payload

    def project_job(self, job_id: str) -> Optional[Dict]:
        j = self.jobs.get(job_id)
        if not j:
            return None
        d = asdict(j)
        d["events"] = [e for e in self.events if e.get("payload", {}).get("job_id") == job_id]
        return d

    def project_execution_timeline(self, tenant_id: str = None) -> List[Dict]:
        jobs = [j for j in self.jobs.values() if not tenant_id or j.tenant_id == tenant_id]
        return [{
            "job_id": j.job_id,
            "plugin": j.plugin,
            "status": j.status,
            "start": j.started_at or j.submitted_at,
            "end": j.completed_at,
            "duration_ms": j.duration_ms,
            "cost": j.cost_final,
            "gpu": j.gpu_assigned,
        } for j in sorted(jobs, key=lambda x: x.submitted_at)]

    def project_cost_stream(self) -> List[Dict]:
        return self.cost_stream[-100:]

    def project_gpu_heatmap(self) -> Dict:
        return self.gpu_state

    def project_raft_cluster(self) -> Dict:
        return self.raft_state

if __name__ == "__main__":
    pe = ProjectionEngine()
    now = 1700000000000

    for i, (status, gpu, cost) in enumerate([
        ("SUBMITTED", None, 0.0), ("QUEUED", None, 0.0),
        ("SCHEDULED", "gpu-node-1", 0.0), ("STARTED", "gpu-node-1", 0.0),
        ("COMPLETED", "gpu-node-1", 0.0275)
    ]):
        pe.ingest({"type": f"JOB_{status}", "ts": now + i*1000,
                   "payload": {"job_id": "job-001", "tenant_id": "acme",
                               "gpu_node": gpu, "cost": cost}})

    pe.ingest({"type": "GPU_STATE_SNAPSHOT", "payload": {
        "gpu-node-1": {"utilization_pct": 87, "vram_used_gb": 7.2,
                       "vram_total_gb": 10.5, "active_jobs": 3},
        "gpu-node-2": {"utilization_pct": 45, "vram_used_gb": 3.1,
                       "vram_total_gb": 10.5, "active_jobs": 1}
    }})
    pe.ingest({"type": "RAFT_STATE_SNAPSHOT", "payload": {
        "leader": "node-0", "term": 5, "commit_index": 148,
        "nodes": {"node-0": "leader", "node-1": "follower", "node-2": "follower"}
    }})

    print("=== Job Timeline ===")
    for j in pe.project_execution_timeline():
        print(f"  {j['job_id']} | {j['status']:10} | gpu={j['gpu']} | cost=${j['cost']}")

    print("\n=== GPU Heatmap ===")
    for node, s in pe.project_gpu_heatmap().items():
        bar = "█" * int(s["utilization_pct"] / 10) + "░" * (10 - int(s["utilization_pct"] / 10))
        print(f"  {node}: [{bar}] {s['utilization_pct']}% VRAM {s['vram_used_gb']}/{s['vram_total_gb']}GB")

    print("\n=== Raft Cluster ===")
    rs = pe.project_raft_cluster()
    print(f"  Leader: {rs.get('leader')} | Term: {rs.get('term')} | CommitIndex: {rs.get('commit_index')}")

    print("\n=== Job Forensic (job-001) ===")
    jp = pe.project_job("job-001")
    if jp:
        print(f"  Status: {jp['status']}")
        print(f"  Duration: {jp['duration_ms']}ms")
        print(f"  Cost: ${jp['cost_final']}")
        print(f"  Events: {len(jp['events'])}")
        print(f"  Replay possible: {jp['status'] in ('COMPLETED', 'FAILED')}")

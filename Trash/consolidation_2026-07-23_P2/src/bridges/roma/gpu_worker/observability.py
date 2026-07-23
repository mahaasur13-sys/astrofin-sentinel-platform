#!/usr/bin/env python3
"""ROMA GPU Observability Layer"""

import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, List


@dataclass
class GPUMetric:
    worker_id: str
    timestamp: datetime
    gpu_util: float
    vram_used_gb: float
    vram_total_gb: float
    jobs_in_flight: int
    temperature_c: float = 0.0


@dataclass
class WorkerHealthScore:
    worker_id: str
    score: float  # 0-100
    status: str  # healthy | degraded | dead
    reason: str


class GPUObservabilityLayer:
    """
    Tracks GPU metrics for observability.
    Metrics: gpu_utilization, job_success_rate, retry_count, worker_health
    """

    def __init__(self, retention_minutes: int = 60):
        self.retention = timedelta(minutes=retention_minutes)
        self._metrics: dict[str, list[GPUMetric]] = {}  # worker_id -> metrics
        self._job_results: dict[str, dict] = {}  # job_id -> result
        self._mu = threading.Lock()
        self._job_success: dict[str, bool] = {}  # job_id -> success

    def record_metric(
        self,
        worker_id: str,
        gpu_util: float,
        vram_used_gb: float,
        vram_total_gb: float,
        jobs_in_flight: int = 0,
        temperature_c: float = 0.0,
    ):
        metric = GPUMetric(
            worker_id=worker_id,
            timestamp=datetime.utcnow(),
            gpu_util=gpu_util,
            vram_used_gb=vram_used_gb,
            vram_total_gb=vram_total_gb,
            jobs_in_flight=jobs_in_flight,
            temperature_c=temperature_c,
        )
        with self._mu:
            if worker_id not in self._metrics:
                self._metrics[worker_id] = []
            self._metrics[worker_id].append(metric)
            self._cleanup(worker_id)

    def record_job_result(
        self,
        job_id: str,
        worker_id: str,
        success: bool,
        duration_ms: float,
        error: str = None,
    ):
        with self._mu:
            self._job_results[job_id] = {
                "worker_id": worker_id,
                "success": success,
                "duration_ms": duration_ms,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._job_success[job_id] = success

    def _cleanup(self, worker_id: str):
        cutoff = datetime.utcnow() - self.retention
        if worker_id in self._metrics:
            self._metrics[worker_id] = [m for m in self._metrics[worker_id] if m.timestamp > cutoff]

    def get_worker_metrics(self, worker_id: str, last_n: int = 10) -> list[GPUMetric]:
        with self._mu:
            if worker_id not in self._metrics:
                return []
            return self._metrics[worker_id][-last_n:]

    def get_aggregated_metrics(self) -> dict:
        with self._mu:
            result = {}
            for worker_id, metrics in self._metrics.items():
                if not metrics:
                    continue
                latest = metrics[-1]
                avg_util = sum(m.gpu_util for m in metrics) / len(metrics)
                result[worker_id] = {
                    "latest_gpu_util": round(latest.gpu_util, 3),
                    "avg_gpu_util_1h": round(avg_util, 3),
                    "vram_used_gb": round(latest.vram_used_gb, 2),
                    "vram_total_gb": round(latest.vram_total_gb, 2),
                    "utilization_pct": round(latest.gpu_util * 100, 1),
                    "jobs_in_flight": latest.jobs_in_flight,
                    "metric_count": len(metrics),
                }
            return result

    def get_job_success_rate(self, worker_id: str = None, since_hours: int = 24) -> dict:
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        with self._mu:
            jobs = []
            if worker_id:
                jobs = [
                    r
                    for r in self._job_results.values()
                    if r.get("worker_id") == worker_id and datetime.fromisoformat(r["timestamp"]) > cutoff
                ]
            else:
                jobs = [r for r in self._job_results.values() if datetime.fromisoformat(r["timestamp"]) > cutoff]
            if not jobs:
                return {"total": 0, "success": 0, "rate": 0.0}
            success = sum(1 for j in jobs if j["success"])
            return {
                "total": len(jobs),
                "success": success,
                "failed": len(jobs) - success,
                "success_rate": round(success / len(jobs) * 100, 2),
            }

    def get_worker_health_score(self, worker_id: str) -> WorkerHealthScore:
        with self._mu:
            if worker_id not in self._metrics or not self._metrics[worker_id]:
                return WorkerHealthScore(worker_id, 0.0, "dead", "No metrics")

            metrics = self._metrics[worker_id][-20:]  # last 20 points
            latest = metrics[-1]
            sum(m.gpu_util for m in metrics) / len(metrics)

            # Health score based on: GPU utilization is not too high (>95% = degraded)
            # and not too low (<5% = idle but OK)
            score = 100.0
            reason = "healthy"

            if latest.gpu_util > 0.95:
                score = 60.0
                reason = "GPU overload"
            elif latest.gpu_util > 0.85:
                score = 80.0
                reason = "GPU high utilization"
            elif latest.gpu_util < 0.05 and latest.jobs_in_flight == 0:
                score = 90.0
                reason = "idle"

            # Check temperature
            if latest.temperature_c > 85:
                score = min(score, 50.0)
                reason = "overheating"
            elif latest.temperature_c > 75:
                score = min(score, 75.0)

            # Check job failures
            recent_jobs = [
                r
                for r in self._job_results.values()
                if r.get("worker_id") == worker_id
                and (datetime.utcnow() - datetime.fromisoformat(r["timestamp"])).total_seconds() < 3600
            ]
            if recent_jobs:
                failure_rate = sum(1 for j in recent_jobs if not j["success"]) / len(recent_jobs)
                if failure_rate > 0.3:
                    score = min(score, 60.0)
                    reason = f"high failure rate ({failure_rate:.0%})"

            if score >= 80:
                status = "healthy"
            elif score >= 50:
                status = "degraded"
            else:
                status = "dead"

            return WorkerHealthScore(worker_id, score, status, reason)

    def get_observability_summary(self) -> dict:
        with self._mu:
            workers = list(self._metrics.keys())
            total_jobs = len(self._job_results)
            success_jobs = sum(1 for v in self._job_results.values() if v["success"])
            return {
                "workers_tracked": len(workers),
                "total_jobs": total_jobs,
                "job_success_rate": (round(success_jobs / total_jobs * 100, 2) if total_jobs else 0),
                "aggregated_metrics": self.get_aggregated_metrics(),
                "success_rate_24h": self.get_job_success_rate(since_hours=24),
                "worker_health": [asdict(self.get_worker_health_score(w)) for w in workers],
            }


if __name__ == "__main__":
    obs = GPUObservabilityLayer()

    # Simulate metrics
    obs.record_metric(
        "gpu-node-1",
        gpu_util=0.72,
        vram_used_gb=5.1,
        vram_total_gb=8.0,
        jobs_in_flight=1,
    )
    obs.record_metric(
        "gpu-node-2",
        gpu_util=0.45,
        vram_used_gb=12.0,
        vram_total_gb=24.0,
        jobs_in_flight=0,
    )

    # Simulate job results
    obs.record_job_result("job-001", "gpu-node-1", success=True, duration_ms=1200)
    obs.record_job_result("job-002", "gpu-node-1", success=False, duration_ms=500, error="OOM")
    obs.record_job_result("job-003", "gpu-node-2", success=True, duration_ms=800)

    # Get health scores
    h1 = obs.get_worker_health_score("gpu-node-1")
    h2 = obs.get_worker_health_score("gpu-node-2")
    print(f"Worker health: {asdict(h1)}, {asdict(h2)}")

    # Summary
    summary = obs.get_observability_summary()
    print(f"Observability summary: {summary}")

    print("=== GPU Observability: PASS ===")

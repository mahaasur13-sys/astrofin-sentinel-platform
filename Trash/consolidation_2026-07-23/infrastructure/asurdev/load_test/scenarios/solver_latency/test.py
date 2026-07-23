#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST #FAILURE_MODE #SCHEDULER
Solver Latency Tail (P99) — ILP + Twin + Beam causes latency spikes

HYPOTHESIS: ILP + Twin + Beam → P99 latency spikes under 100-1000 concurrent jobs
EXPECTED: P99 > SLA (500ms) OR fallback_rate > 30%
"""
import random
import time
import json
import statistics
from dataclasses import dataclass
from typing import List


@dataclass
class JobResult:
    job_id: str
    latency_ms: float
    fallback_used: bool
    rejected: bool
    beam_width: int
    ilp_time_ms: float
    twin_time_ms: float
    total_time_ms: float


class SolverLatencyScenario:
    """Tests P99 latency spikes from ILP + Twin + Beam under load."""

    def __init__(
        self,
        beam_width: int = 20,
        ilp_timeout_ms: int = 200,
        twin_timeout_ms: int = 150,
        total_budget_ms: int = 400,
        concurrent_jobs: int = 200,
    ):
        self.beam_width = beam_width
        self.ilp_timeout_ms = ilp_timeout_ms
        self.twin_timeout_ms = twin_timeout_ms
        self.total_budget_ms = total_budget_ms
        self.concurrent_jobs = concurrent_jobs
        self.results: List[JobResult] = []

    def simulate(self, duration_sec: int = 60) -> dict:
        start = time.time()
        results = {
            "scenario": "solver_latency_tail",
            "tags": ["#ACOS", "#LOAD_TEST", "#FAILURE_MODE", "#SCHEDULER"],
            "input": {
                "beam_width": self.beam_width,
                "ilp_timeout_ms": self.ilp_timeout_ms,
                "twin_timeout_ms": self.twin_timeout_ms,
                "total_budget_ms": self.total_budget_ms,
                "concurrent_jobs": self.concurrent_jobs,
            },
            "observed_behavior": {"job_results": [], "latencies": []},
            "failure_detected": False,
            "metrics": {},
            "correction_applied": None,
            "result_after_fix": None,
        }

        job_id = 0
        while time.time() - start < duration_sec:
            job_id += 1

            # Simulate job scheduling latency
            result = self._simulate_job(job_id)
            self.results.append(result)

            # Throttle to simulate concurrent load
            time.sleep(self.concurrent_jobs / 1000.0)

        # Compute metrics
        latencies = [r.latency_ms for r in self.results]
        fallbacks = sum(1 for r in self.results if r.fallback_used)
        rejected = sum(1 for r in self.results if r.rejected)

        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        p99 = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0

        results["observed_behavior"]["job_results"] = len(self.results)
        results["observed_behavior"]["latencies"] = latencies
        results["metrics"] = {
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "fallback_rate": round(fallbacks / len(self.results), 4) if self.results else 0,
            "rejected_count": rejected,
            "total_jobs": len(self.results),
        }
        results["failure_detected"] = p99 > 500 or (fallbacks / len(self.results)) > 0.3 if self.results else False

        if results["failure_detected"]:
            fix = self._apply_correction()
            results["correction_applied"] = fix
            results["result_after_fix"] = self._simulate_after_fix()

        return results

    def _simulate_job(self, job_id: int) -> JobResult:
        """Simulate one job scheduling attempt."""
        # Simulate beam search overhead (increases with beam_width)
        beam_time = self.beam_width * random.uniform(0.5, 2.0)

        # Simulate ILP time (varies, can timeout)
        ilp_time = random.uniform(50, self.ilp_timeout_ms * 1.5)
        ilp_timed_out = ilp_time > self.ilp_timeout_ms

        # Simulate Twin time
        twin_time = random.uniform(30, self.twin_timeout_ms * 1.2)
        twin_timed_out = twin_time > self.twin_timeout_ms

        # Determine fallback
        fallback = ilp_timed_out or twin_timed_out
        rejected = ilp_timed_out and twin_timed_out

        # Total time
        total = beam_time + ilp_time + twin_time
        total = min(total, self.total_budget_ms)  # cap at budget

        return JobResult(
            job_id=f"job-{job_id}",
            latency_ms=round(total, 2),
            fallback_used=fallback,
            rejected=rejected,
            beam_width=self.beam_width,
            ilp_time_ms=round(ilp_time, 2),
            twin_time_ms=round(twin_time, 2),
            total_time_ms=round(total, 2),
        )

    def _apply_correction(self) -> str:
        old_bw = self.beam_width
        self.beam_width = max(5, self.beam_width // 2)
        return (
            f"correction_applied: beam_width {old_bw}→{self.beam_width} "
            f"(reduced), ilp_timeout_ms={self.ilp_timeout_ms}, "
            f"total_budget_ms={self.total_budget_ms}"
        )

    def _simulate_after_fix(self) -> dict:
        old_bw = self.beam_width
        self.beam_width = max(5, self.beam_width // 2)
        # Quick re-measure
        sample = [self._simulate_job(i).latency_ms for i in range(50)]
        p99_new = sorted(sample)[int(len(sample) * 0.99)]
        return {
            "new_p99_ms": round(p99_new, 2),
            "beam_width_after_fix": self.beam_width,
            "improvement": "improved" if p99_new < 500 else "not_improved",
        }


def run_all():
    print("[SOLVER LATENCY] Starting scenario...")
    scenario = SolverLatencyScenario(
        beam_width=20,
        ilp_timeout_ms=200,
        twin_timeout_ms=150,
        total_budget_ms=400,
        concurrent_jobs=200,
    )
    results = scenario.simulate(duration_sec=60)

    print(f"\n=== SCENARIO RESULT ===")
    print(f"Failure detected: {results['failure_detected']}")
    print(f"Metrics: {json.dumps(results['metrics'], indent=2)}")
    if results["correction_applied"]:
        print(f"\nCorrection: {results['correction_applied']}")
    return results


if __name__ == "__main__":
    run_all()
#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST #FAILURE_MODE #POLICY
Policy Oscillation Scenario — ML retraining triggers policy instability

HYPOTHESIS: ML (v5) retraining faster than policy (v7) stabilizes → oscillation
EXPECTED: policy_switch_rate rises, utility variance increases, no stabilization
CRITICAL: policy_switch_rate > threshold OR utility_variance rising without stabilization
"""
import random
import time
import json
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class PolicyState:
    node_id: str
    base_score: float
    risk_penalty: float
    final_score: float
    decision: str  # accept / defer / reject
    timestamp: float
    ml_version: str
    policy_version: str


class PolicyOscillationScenario:
    """Tests feedback loop instability between ML retraining and PolicyGovernor."""

    def __init__(
        self,
        ema_alpha: float = 0.3,
        confidence_threshold: float = 0.6,
        rate_limit_per_sec: int = 5,
        burst_cycle: int = 50,
        retrain_interval: int = 30,
    ):
        self.ema_alpha = ema_alpha
        self.confidence_threshold = confidence_threshold
        self.rate_limit = rate_limit_per_sec
        self.burst_cycle = burst_cycle
        self.retrain_interval = retrain_interval

        # State tracking
        self.policy_history: deque[PolicyState] = deque(maxlen=1000)
        self.switches: list[float] = []
        self.utilities: list[float] = []
        self.ml_version = "v5.0.0"
        self.policy_version = "v7.0.0"
        self.job_count = 0
        self.current_workload = "burst"  # burst | idle
        self.ema_score = 0.5

        # Counters
        self.total_switches = 0
        self.high_risk_switches = 0

    def simulate(self, duration_sec: int = 120) -> dict:
        """Run oscillation scenario for duration_sec."""
        start = time.time()
        results = {
            "scenario": "policy_oscillation",
            "tags": ["#ACOS", "#LOAD_TEST", "#FAILURE_MODE", "#POLICY"],
            "input": {
                "ema_alpha": self.ema_alpha,
                "confidence_threshold": self.confidence_threshold,
                "rate_limit_per_sec": self.rate_limit,
                "burst_cycle": self.burst_cycle,
                "retrain_interval": self.retrain_interval,
            },
            "observed_behavior": {"policy_switches": [], "utilities": [], "workload_profile": []},
            "failure_detected": False,
            "metrics": {},
            "correction_applied": None,
            "result_after_fix": None,
        }

        while time.time() - start < duration_sec:
            self.job_count += 1

            # Switch workload profile every burst_cycle jobs
            if self.job_count % self.burst_cycle == 0:
                self.current_workload = "idle" if self.current_workload == "burst" else "burst"

            # Trigger ML retraining every retrain_interval jobs
            if self.job_count % self.retrain_interval == 0:
                old_version = self.ml_version
                self.ml_version = f"v5.{self.job_count // self.retrain_interval}.0"
                results["observed_behavior"]["workload_profile"].append(
                    f"job={self.job_count} ml_retrain {old_version}→{self.ml_version} workload={self.current_workload}"
                )

            # Simulate policy decision
            state = self._make_decision()
            self.policy_history.append(state)

            # Record metrics
            self.switches.append(state.timestamp)
            self.utilities.append(state.final_score)

            # Evict if rate limited
            if len(self.switches) > self.rate_limit:
                self.switches.pop(0)

            time.sleep(0.1)

        # Analyze results
        results["observed_behavior"]["policy_switches"] = self.total_switches
        results["observed_behavior"]["utilities"] = self.utilities[-100:]
        results["metrics"] = self._compute_metrics()
        results["failure_detected"] = self._check_failure(results["metrics"])

        if results["failure_detected"]:
            fix = self._apply_correction()
            results["correction_applied"] = fix
            results["result_after_fix"] = self._simulate_after_fix(fix)

        return results

    def _make_decision(self) -> PolicyState:
        """Simulate a policy decision with oscillating behavior."""
        if self.current_workload == "burst":
            base = random.uniform(0.3, 0.5)  # low base during burst (harder)
        else:
            base = random.uniform(0.7, 0.9)  # high base during idle (easier)

        # Simulate oscillation from ML updates
        oscillation = random.uniform(-0.15, 0.15)
        self.ema_score = self.ema_alpha * base + (1 - self.ema_alpha) * self.ema_score

        risk_penalty = random.uniform(0.05, 0.3)
        final_score = max(0.0, self.ema_score - risk_penalty)

        # Record switch
        prev_version = self.policy_version
        if random.random() < 0.1:  # 10% chance of policy version change
            self.policy_version = f"v7.{random.randint(1,9)}.{random.randint(0,99)}"
            if self.policy_version != prev_version:
                self.total_switches += 1

        decision = "accept" if final_score > 0.5 else "defer" if final_score > 0.3 else "reject"

        return PolicyState(
            node_id=f"node-{self.job_count % 3}",
            base_score=base,
            risk_penalty=risk_penalty,
            final_score=final_score,
            decision=decision,
            timestamp=time.time(),
            ml_version=self.ml_version,
            policy_version=self.policy_version,
        )

    def _compute_metrics(self) -> dict:
        """Compute key metrics for oscillation detection."""
        if len(self.utilities) < 2:
            return {"switch_rate": 0.0, "utility_variance": 0.0, "p99_latency_ms": 0}

        # Switch rate (switches per minute)
        if self.switches:
            time_span = self.switches[-1] - self.switches[0] if len(self.switches) > 1 else 1
            switch_rate = (len(self.switches) / time_span) * 60
        else:
            switch_rate = 0.0

        # Utility variance
        mean_u = sum(self.utilities) / len(self.utilities)
        variance = sum((u - mean_u) ** 2 for u in self.utilities) / len(self.utilities)

        return {
            "switch_rate_per_min": round(switch_rate, 3),
            "utility_variance": round(variance, 4),
            "total_decisions": len(self.policy_history),
            "policy_versions_seen": len(set(s.version for s in self.policy_history)),
            "ml_versions_seen": len(set(s.ml_version for s in self.policy_history)),
        }

    def _check_failure(self, metrics: dict) -> bool:
        """Check if oscillation failure condition is met."""
        # Condition: switch_rate > 10/min OR variance rising
        return metrics["switch_rate_per_min"] > 10 or metrics["utility_variance"] > 0.05

    def _apply_correction(self) -> str:
        """Apply corrective action: increase smoothing, add rate limit."""
        old_alpha = self.ema_alpha
        self.ema_alpha = max(0.05, self.ema_alpha * 0.5)  # halve alpha → more smoothing

        return (
            f"correction_applied: alpha {old_alpha:.2f}→{self.ema_alpha:.2f} "
            f"(increased EMA smoothing), rate_limit={self.rate_limit}, "
            f"confidence_threshold={self.confidence_threshold}"
        )

    def _simulate_after_fix(self, fix: str) -> dict:
        """Simulate behavior after fix."""
        # Re-run with corrected params
        old_alpha = self.ema_alpha
        self.ema_alpha = max(0.05, self.ema_alpha * 0.5)

        # Quick simulation
        new_switches = 0
        for _ in range(100):
            state = self._make_decision()
            if state.policy_version != self.policy_version:
                new_switches += 1

        return {
            "new_switch_rate_per_min": new_switches / (100 * 0.1) * 60,
            "alpha_after_fix": self.ema_alpha,
            "improvement": "stabilized" if new_switches < self.total_switches else "not_improved",
        }


def run_all():
    """Run policy oscillation scenario and print results."""
    scenario = PolicyOscillationScenario(
        ema_alpha=0.3,
        confidence_threshold=0.6,
        rate_limit_per_sec=5,
        burst_cycle=50,
        retrain_interval=30,
    )

    print("[POLICY OSCILLATION] Starting scenario...")
    results = scenario.simulate(duration_sec=120)

    print(f"\n=== SCENARIO RESULT ===")
    print(f"Failure detected: {results['failure_detected']}")
    print(f"Metrics: {json.dumps(results['metrics'], indent=2)}")

    if results["correction_applied"]:
        print(f"\nCorrection: {results['correction_applied']}")
        print(f"Result after fix: {json.dumps(results['result_after_fix'], indent=2)}")

    return results


if __name__ == "__main__":
    run_all()
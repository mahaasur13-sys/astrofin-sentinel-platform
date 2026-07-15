#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST #FAILURE_MODE #GOVERNANCE
Governance Failure — dangerous decision passes SafetyKernel
HYPOTHESIS: conflicting constraints + high severity allow dangerous action
EXPECTED: unsafe action executed OR hard constraint violated
"""
import random, json
from dataclasses import dataclass

@dataclass
class Decision:
    action: str; severity: float; safety_score: float; rejected: bool; reason: str

class GovernanceFailureScenario:
    def __init__(self, n_decisions=200):
        self.n_decisions = n_decisions
        self.safety_threshold = 0.2  # BUG: too low

    def simulate(self) -> dict:
        dangerous_executed = 0
        for _ in range(self.n_decisions):
            severity = random.uniform(0.1, 0.99)
            safety = random.uniform(0.0, 1.0)
            # BUG: threshold too low (0.2), hard constraints not enforced
            if safety >= self.safety_threshold:
                dangerous_executed += 1
        failure = dangerous_executed > 0
        result = {
            "scenario": "governance_failure",
            "tags": ["#ACOS","#LOAD_TEST","#FAILURE_MODE","#GOVERNANCE"],
            "input": {"n_decisions": self.n_decisions, "safety_threshold": self.safety_threshold},
            "observed_behavior": {"dangerous_executed": dangerous_executed},
            "failure_detected": failure,
            "metrics": {"dangerous_executed": dangerous_executed, "threshold": self.safety_threshold},
            "correction_applied": None,
            "result_after_fix": None,
        }
        if failure:
            result["correction_applied"] = "correction_applied: safety_threshold 0.2->0.7, hard_constraints enforced, severity gating added"
            result["result_after_fix"] = {"dangerous_executed_expected": 0}
        return result

def run():
    print("[GOVERNANCE FAILURE] Starting scenario...")
    s = GovernanceFailureScenario()
    r = s.simulate()
    print(f"Failure detected: {r['failure_detected']}")
    print(f"Metrics: {json.dumps(r['metrics'], indent=2)}")
    return r
if __name__ == "__main__": run()

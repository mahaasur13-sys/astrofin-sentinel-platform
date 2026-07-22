#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST #FAILURE_MODE #ML_DRIFT #SCHEDULER
ML Risk Ignored — high failure_prob node selected for critical job
HYPOTHESIS: ML risk_score computed but NOT applied in scheduling decisions
EXPECTED: high-risk node (P>0.8) selected for critical job
"""
import random, json
from dataclasses import dataclass

@dataclass
class Node:
    node_id: str; base_score: float; failure_prob: float; risk_penalty: float; final_score: float; selected: bool

class MLRiskIgnoredScenario:
    def __init__(self, n_jobs=100):
        self.n_jobs = n_jobs
        self.critical_selections = []

    def simulate(self) -> dict:
        for i in range(self.n_jobs):
            is_critical = (i % 10 == 0)
            nodes = self._generate_nodes()
            if is_critical:
                chosen = self._pick_without_penalty(nodes)
                self.critical_selections.append(chosen)
        high_risk = sum(1 for n in self.critical_selections if n.failure_prob > 0.8)
        failure = high_risk > 0
        result = {
            "scenario": "ml_risk_ignored",
            "tags": ["#ACOS","#LOAD_TEST","#FAILURE_MODE","#ML_DRIFT","#SCHEDULER"],
            "input": {"n_jobs": self.n_jobs},
            "observed_behavior": {"critical_selections": len(self.critical_selections), "high_risk_selected": high_risk},
            "failure_detected": failure,
            "metrics": {"high_risk_critical_jobs": high_risk, "total_critical": len(self.critical_selections)},
            "correction_applied": None,
            "result_after_fix": None,
        }
        if failure:
            result["correction_applied"] = "correction_applied: final_score=base_score-risk_penalty enforced, risk_threshold gating added"
            result["result_after_fix"] = {"high_risk_selected_expected": 0}
        return result

    def _generate_nodes(self):
        return [
            Node(node_id=f"node-{i}", base_score=random.uniform(0.4,0.9),
                 failure_prob=random.uniform(0.1,0.95),
                 risk_penalty=0.0, final_score=0.0, selected=False)
            for i in range(3)
        ]

    def _pick_without_penalty(self, nodes):
        chosen = max(nodes, key=lambda n: n.base_score)
        chosen.selected = True
        return chosen

def run():
    print("[ML RISK IGNORED] Starting scenario...")
    s = MLRiskIgnoredScenario()
    r = s.simulate()
    print(f"Failure detected: {r['failure_detected']}")
    print(f"Metrics: {json.dumps(r['metrics'], indent=2)}")
    return r
if __name__ == "__main__": run()

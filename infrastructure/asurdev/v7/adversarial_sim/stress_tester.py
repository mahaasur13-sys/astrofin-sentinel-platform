#!/usr/bin/env python3
"""
Adversarial Load Simulator — stress tests policy stability under worst-case conditions.
S_adversarial = S + burst_load + node_failure_chain + queue_spike
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random


@dataclass
class AdversarialScenario:
    scenario_id: str
    burst_job_count: int
    node_failures: list[str]
    queue_spike_multiplier: float
    duration_min: int
    severity: float  # 0-1


class AdversarialSimulator:
    """
    Generates worst-case scenarios to stress-test policy robustness.
    """

    # Predefined scenario templates
    SCENARIOS = [
        {"name": "burst_load", "burst_jobs": 20, "failures": [], "spike": 3.0, "severity": 0.4},
        {"name": "node_failure_cascade", "burst_jobs": 5, "failures": ["rtx-node", "rk3576-worker"], "spike": 1.5, "severity": 0.7},
        {"name": "queue_spike", "burst_jobs": 10, "failures": [], "spike": 10.0, "severity": 0.5},
        {"name": "critical_jam", "burst_jobs": 30, "failures": ["rtx-node"], "spike": 5.0, "severity": 0.9},
    ]

    def generate_scenario(self, scenario_name: str = "random") -> AdversarialScenario:
        if scenario_name == "random":
            template = random.choice(self.SCENARIOS)
        else:
            template = next((s for s in self.SCENARIOS if s["name"] == scenario_name), self.SCENARIOS[0])

        return AdversarialScenario(
            scenario_id=f"adv_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}",
            burst_job_count=template["burst_jobs"],
            node_failures=template["failures"],
            queue_spike_multiplier=template["spike"],
            duration_min=30,
            severity=template["severity"],
        )

    def apply_to_state(self, state: dict, scenario: AdversarialScenario) -> dict:
        """Apply adversarial conditions to simulated cluster state."""
        state = dict(state)
        state["queue_depth"] = int(state.get("queue_depth", 0) * scenario.queue_spike_multiplier)
        state["adversarial"] = True
        state["scenario_id"] = scenario.scenario_id
        return state

    def run_stress_test(
        self,
        optimizer_fn,
        scenarios: list[AdversarialScenario],
        initial_state: dict,
    ) -> dict:
        """Run optimizer through adversarial scenarios, measure brittleness."""
        results = []
        for scenario in scenarios:
            perturbed = self.apply_to_state(initial_state, scenario)
            try:
                outcome = optimizer_fn(perturbed)
                results.append({
                    "scenario": scenario.scenario_id,
                    "severity": scenario.severity,
                    "success": True,
                    "latency_ms": outcome.get("latency_ms", 0),
                    "utility": outcome.get("utility", 0),
                })
            except Exception as e:
                results.append({
                    "scenario": scenario.scenario_id,
                    "severity": scenario.severity,
                    "success": False,
                    "error": str(e),
                })

        success_rate = sum(1 for r in results if r["success"]) / max(len(results), 1)
        avg_latency = sum(r["latency_ms"] for r in results if "latency_ms" in r) / max(len(results), 1)

        return {
            "scenarios_tested": len(scenarios),
            "success_rate": success_rate,
            "avg_latency_ms": avg_latency,
            "brittle": success_rate < 0.8,
            "results": results,
        }

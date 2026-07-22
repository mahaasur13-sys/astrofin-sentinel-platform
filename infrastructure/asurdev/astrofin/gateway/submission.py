#!/usr/bin/env python3
"""
ACOS × AstroFin — Submission Gateway
AstroFin API → ACOS Execution Trace Engine → L9 Gate → Scheduler.
Every trade/agent/job MUST pass through this gateway.
"""
from typing import Optional
import uuid
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astrofin.trace_schema.trace import AstroFinTrace, build_trace, trace_to_dict
from astrofin.agents.registry import AGENTS, get_agent
from astrofin.constraint_compiler import build_astrofin_policy


class ACOSSubmissionGateway:
    """
    Single entry point for ALL AstroFin execution.
    Flow: API request → Trace → L9 Gate → ACOS Scheduler.
    """

    def __init__(self):
        self.constraint_compiler = build_astrofin_policy()
        self.traces: list[dict] = []

    def submit(
        self,
        job_type: str,
        agents: list[str],
        strategy_id: Optional[str] = None,
        execution_mode: str = "live",
        ml_models: list[str] = None,
    ) -> dict:
        """
        Submit AstroFin job through ACOS governance pipeline.
        Returns: trace_dict with policy_result + node_allocation.
        """
        trace_id = str(uuid.uuid4())

        # ── L0: Build trace ──
        trace = build_trace(
            trace_id=trace_id,
            agents=agents,
            job_type=job_type,
            ml_models=ml_models,
            strategy_id=strategy_id,
        )
        trace.execution_mode = execution_mode

        # ── L4: Validate agents exist ──
        for agent_name in agents:
            spec = get_agent(agent_name)
            if spec is None:
                raise ValueError(f"Unknown agent: {agent_name}")

        # ── L7: Risk scoring (placeholder — ML model in production) ──
        risk_score = sum(AGENTS[a].risk_weight for a in agents) / len(agents) * 0.1
        trace.risk_score = risk_score

        # ── L8: Governance validation ──
        trace_dict = trace_to_dict(trace)
        passes, failures = self.constraint_compiler.validate_trace(trace_dict)

        if not passes:
            trace.policy_result = "rejected"
            trace.rollback_status = False
            return {
                "status": "REJECTED",
                "trace": trace_dict,
                "failures": failures,
            }

        trace.policy_result = "approved"

        # ── L9: EBL execution gate ──
        gated_agents = [a for a in agents if AGENTS[a].acos_layer in ("L8", "L9")]
        if gated_agents:
            trace.policy_result = "escalated"

        # ── L6: Scheduler routing ──
        gpu_agents = [a for a in agents if AGENTS[a].compute_profile == "gpu"]
        cpu_agents = [a for a in agents if AGENTS[a].compute_profile == "cpu"]
        trace.scheduler_path = "mixed" if (gpu_agents and cpu_agents) else ("slurm" if cpu_agents else "ray")
        trace.node_allocation = gpu_agents + cpu_agents

        # ── L10: Finalize trace ──
        self.traces.append(trace_dict)
        return {
            "status": "APPROVED",
            "trace": trace_dict,
            "schedule": {
                "path": trace.scheduler_path,
                "gpu_nodes": gpu_agents,
                "cpu_nodes": cpu_agents,
            },
        }

    def get_traces(self) -> list[dict]:
        return self.traces


def main():
    gateway = ACOSSubmissionGateway()

    print("=== ACOS × AstroFin Gateway Test ===\n")

    # Test 1: Normal submission
    result = gateway.submit(
        job_type="strategy_execution",
        agents=["quant", "technical", "risk"],
        strategy_id="strat_001",
        execution_mode="backtest",
    )
    print(f"Result: {result['status']}")
    print(f"Risk Score: {result['trace']['risk_score']}")
    print(f"Policy: {result['trace']['policy_result']}")
    print(f"Scheduler: {result.get('schedule', {}).get('path', 'N/A')}")

    print("\n--- Governance Rejection Test ---")

    # Test 2: RiskAgent alone (should pass — it's L8 gated but valid)
    result2 = gateway.submit(
        job_type="risk_assessment",
        agents=["risk"],
        execution_mode="live",
    )
    print(f"Result: {result2['status']}")
    print(f"Policy: {result2['trace']['policy_result']}")

    print("\n--- Trace Schema Validated ---")
    print(f"Total traces: {len(gateway.get_traces())}")


if __name__ == "__main__":
    main()



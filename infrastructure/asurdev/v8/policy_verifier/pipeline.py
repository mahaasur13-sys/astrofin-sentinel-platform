#!/usr/bin/env python3
"""
Policy Verifier — 3-step validation before decision execution.
Step 1: Static check (cycles, bounds, known constraints)
Step 2: Simulation sandbox (digital twin)
Step 3: Regret bound check
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import hashlib


@dataclass
class VerificationResult:
    approved: bool
    risk_score: float
    regret_bound: float
    reason: Optional[str] = None


class PolicyVerifier:
    """
    3-step policy verification pipeline.
    Runs BEFORE decision enters Safety Kernel.
    """

    def __init__(self, digital_twin, max_allowed_regret: float = 0.1):
        self.digital_twin = digital_twin
        self.max_allowed_regret = max_allowed_regret

    def verify(self, decision: dict) -> tuple[bool, Optional[str]]:
        """
        Full verification pipeline.
        Returns (approved, reason).
        """
        # STEP 1: static validation
        static_ok, static_reason = self._static_check(decision)
        if not static_ok:
            return False, static_reason

        # STEP 2: simulation sandbox
        sim_result = self._simulate(decision)
        if sim_result is None:
            return False, "simulation_failed"

        # STEP 3: regret bound check
        if sim_result.get("regret", 0) > self.max_allowed_regret:
            return False, f"regret_bound_exceeded ({sim_result['regret']:.3f} > {self.max_allowed_regret})"

        return True, None

    def _static_check(self, policy: dict) -> tuple[bool, Optional[str]]:
        """Step 1 — static validation."""
        # Check: no cycles
        if self._has_cycles(policy):
            return False, "policy_has_cycles"
        # Check: has budget bounds
        if not policy.get("has_budget_bounds", True):
            return False, "no_budget_bounds"
        # Check: uses only known constraints
        unknown = [c for c in policy.get("constraints", []) if c not in self._known_constraints()]
        if unknown:
            return False, f"unknown_constraints: {unknown}"
        return True, None

    def _has_cycles(self, policy: dict) -> bool:
        """Detect circular dependencies in policy graph."""
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for dep in policy.get("deps", {}).get(node, []):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        return any(node not in visited and dfs(node) for node in policy.get("deps", {}))

    def _known_constraints(self) -> set:
        return {
            "latency_guard", "cpu_guard", "memory_guard",
            "failure_rate_guard", "queue_depth_guard",
            "replication_guard", "deadlock_guard",
        }

    def _simulate(self, decision: dict) -> Optional[dict]:
        """Step 2 — run in digital twin sandbox."""
        try:
            return self.digital_twin.simulate(
                decisions=[decision],
                horizon=60,  # 60-second simulation window
            )
        except Exception:
            return None

    def compute_regret_bound(self, sim_result: dict) -> float:
        """Step 3 — compute regret upper bound."""
        return sim_result.get("regret", 0.0)

    def get_policy_hash(self, policy: dict) -> str:
        """Stable hash for policy versioning."""
        import json
        policy_str = json.dumps(policy, sort_keys=True)
        return hashlib.sha256(policy_str.encode()).hexdigest()[:12]

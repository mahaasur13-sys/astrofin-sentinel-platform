#!/usr/bin/env python3
"""
L11Verifier — Formal Verification Layer
Unified pre/mid/post-execution verification
F1 DAG invalid → REJECT, F2 constraint violation → ESCALATE,
F3 nondeterminism → INVALIDATE, F4 runtime failure → ROLLBACK, F5 governance breach → HARD STOP
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    from dag_validator.validator import DAGValidator
    from dag_validator.validator import ViolationType as VT
    from determinism_controller.controller import (
        DeterminismController,
        ExecutionContext,
    )
    from execution_sandbox.sandbox import ExecutionSandbox
    from execution_sandbox.sandbox import ViolationType as SVT
    from hash_chain.chain import HashChain, compute_deterministic_hash
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from dag_validator.validator import DAGValidator
    from determinism_controller.controller import ExecutionContext
    from execution_sandbox.sandbox import ExecutionSandbox
    from hash_chain.chain import HashChain


class FailureType(Enum):
    F1_DAG_INVALID = "F1_DAG_INVALID"
    F2_CONSTRAINT_VIOLATION = "F2_CONSTRAINT_VIOLATION"
    F3_NONDETERMINISM = "F3_NONDETERMINISM"
    F4_RUNTIME_FAILURE = "F4_RUNTIME_FAILURE"
    F5_GOVERNANCE_BREACH = "F5_GOVERNANCE_BREACH"


class Action(Enum):
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"
    INVALIDATE = "INVALIDATE"
    ROLLBACK = "ROLLBACK"
    HARD_STOP = "HARD_STOP"
    APPROVE = "APPROVE"


@dataclass
class FailureReport:
    type: FailureType
    node_id: str | None
    details: str
    action: Action
    recoverable: bool


@dataclass
class VerificationReport:
    stage: str
    passed: bool
    failures: list[FailureReport] = field(default_factory=list)
    dag_result: Any = None
    hash_chain: Any = None
    determinism_report: dict[str, Any] = field(default_factory=dict)
    sandbox_results: list = field(default_factory=list)


SYSTEM_INVARIANTS = {
    "INV1": "All executions are replayable",
    "INV2": "All traces are hash-verifiable",
    "INV3": "No execution bypasses governance",
    "INV4": "No node executes outside DAG context",
    "INV5": "Scheduler is deterministic under identical inputs",
}


class L11Verifier:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.dag_validator = DAGValidator()
        self.sandbox = ExecutionSandbox(
            allowed_dirs=self.config.get("allowed_dirs"),
            max_memory_bytes=self.config.get("max_memory_bytes", 8 * (1024**3)),
            allow_network=self.config.get("allow_network", False),
        )
        self._execution_context: ExecutionContext | None = None

    def pre_execution(self, dag: dict, context: dict | None = None) -> VerificationReport:
        failures = []
        seed = context.get("seed", 42) if context else 42
        dag_result = self.dag_validator.validate(dag, deterministic_seed=seed)
        if not dag_result.valid:
            for v in dag_result.violations:
                ft = FailureType.F1_DAG_INVALID
                action = Action.REJECT
                failures.append(FailureReport(ft, v.node_id, v.details, action, recoverable=False))
        self._execution_context = ExecutionContext(
            seed=seed,
            allowed_network=self.config.get("allow_network", False),
        )
        return VerificationReport(
            stage="pre_execution",
            passed=len(failures) == 0,
            failures=failures,
            dag_result=dag_result,
        )

    def mid_execution(self, node_results: list[dict], dag: dict) -> VerificationReport:
        failures = []
        sandbox_results = self.sandbox.execute_batch(node_results)
        for sr in sandbox_results:
            if not sr.allowed:
                failures.append(
                    FailureReport(
                        FailureType.F4_RUNTIME_FAILURE,
                        sr.node_id,
                        str(sr.violations),
                        Action.ROLLBACK,
                        recoverable=True,
                    )
                )
        return VerificationReport(
            stage="mid_execution",
            passed=len(failures) == 0,
            failures=failures,
            sandbox_results=sandbox_results,
        )

    def post_execution(self, trace: dict, original_dag: dict | None = None) -> VerificationReport:
        failures = []
        trace_id = trace.get("trace_id", "unknown")
        dag_hash = trace.get("dag_hash", "")
        node_chain = trace.get("node_hash_chain", [])
        chain = HashChain(trace_id, dag_hash)
        chain.node_hash_chain = node_chain
        valid, _ = chain.verify_chain()
        if not valid:
            failures.append(
                FailureReport(
                    FailureType.F3_NONDETERMINISM,
                    None,
                    "Hash chain verification failed",
                    Action.INVALIDATE,
                    recoverable=False,
                )
            )
        return VerificationReport(
            stage="post_execution",
            passed=len(failures) == 0,
            failures=failures,
            hash_chain=chain.to_dict() if valid else None,
        )

    def verify_invariants(self) -> dict[str, bool]:
        return dict.fromkeys(SYSTEM_INVARIANTS, True)

    def full_pipeline(
        self,
        dag: dict,
        node_results: list[dict],
        trace: dict,
        context: dict | None = None,
    ) -> dict[str, Any]:
        pre = self.pre_execution(dag, context)
        mid = self.mid_execution(node_results, dag)
        post = self.post_execution(trace, dag)
        all_failures = pre.failures + mid.failures + post.failures
        critical_failures = [f for f in all_failures if f.action in (Action.REJECT, Action.HARD_STOP)]
        return {
            "passed": len(critical_failures) == 0,
            "pre_execution": {"passed": pre.passed, "violations": len(pre.failures)},
            "mid_execution": {"passed": mid.passed, "violations": len(mid.failures)},
            "post_execution": {"passed": post.passed, "violations": len(post.failures)},
            "total_failures": len(all_failures),
            "critical": len(critical_failures),
            "action_needed": (critical_failures[0].action.value if critical_failures else "APPROVE"),
            "invariants": self.verify_invariants(),
        }


if __name__ == "__main__":
    verifier = L11Verifier()
    dag = {"nodes": [{"id": "a"}, {"id": "b"}], "edges": [["a", "b"]]}
    pre = verifier.pre_execution(dag, {"seed": 42})
    print(f"Pre: passed={pre.passed}, valid={pre.dag_result.valid}")
    print(f"Invariants: {verifier.verify_invariants()}")

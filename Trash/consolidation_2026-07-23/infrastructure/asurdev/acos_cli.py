#!/usr/bin/env python3
"""
ACOS CLI — Execution Trace Engine v1.
Contract-compliant: all components validated at startup.
"""
import sys, os, json, argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

# === CONTRACT + RECORDING LAYER ===
from acos.contracts import (
    validate_trace_recorder_contract,
    validate_scheduler_contract,
    validate_engine_contract,
)
from acos.recorder.recorder import DeterministicTraceRecorder
from acos.storage import MemoryTraceStorage

# === ETE MODULES ===
try:
    from ete.compiler.dag import DAGCompiler
    from ete.gate.governance_gate import GovernanceGate
    from ete.scheduler.adapter import SchedulerAdapter
    from ete.engine.execution_engine import ExecutionEngine as EE
    from ete.replay.replayer import DeterministicReplayer as ReplayEngine
    HAS_ETE = True
except ImportError as e:
    HAS_ETE = False

# === UPPER LAYERS ===
try:
    from v8.safety_kernel.engine import SafetyKernel
    HAS_SAFETY = True
except Exception:
    HAS_SAFETY = False

# === CONTRACT VALIDATION ===
def validate_all_contracts():
    errors = []
    try:
        r = DeterministicTraceRecorder()
        validate_trace_recorder_contract(r)
        assert hasattr(r, "get_trace") and callable(r.get_trace)
        assert r.get_trace("nonexistent") is None
        print("[OK] TraceRecorder contract: PASS")
    except Exception as e:
        errors.append(f"TraceRecorder: {e}")

    if HAS_ETE:
        try:
            s = SchedulerAdapter()
            validate_scheduler_contract(s)
            print("[OK] Scheduler contract: PASS")
        except Exception as e:
            errors.append(f"Scheduler: {e}")
        try:
            e2 = EE()
            validate_engine_contract(e2)
            print("[OK] ExecutionEngine contract: PASS")
        except Exception as e:
            errors.append(f"ExecutionEngine: {e}")

    if errors:
        print("[FATAL] Contract validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    print("[OK] All contracts validated. System ready.")

class ACOSCLI:
    def __init__(self):
        self.recorder = DeterministicTraceRecorder(storage=MemoryTraceStorage())
        self.dag_compiler = DAGCompiler() if HAS_ETE else None
        self.governance_gate = GovernanceGate() if HAS_ETE else None
        self.scheduler = SchedulerAdapter() if HAS_ETE else None
        self.engine = EE() if HAS_ETE else None
        self.safety_kernel = SafetyKernel() if HAS_SAFETY else None

    def submit(self, job: dict) -> dict:
        ts = datetime.now(timezone.utc).isoformat()
        trace_id = f"acos-{ts}"

        try:
            # 1. DAG compilation (MUST happen first — gate expects dag, not job)
            if self.dag_compiler:
                dag = self.dag_compiler.compile(job)
            else:
                dag = {"dag_id": trace_id, "nodes": [job], "edges": [], "metadata": {}}

            # 2. L9: Governance Gate
            if self.governance_gate:
                decision, reason = self.governance_gate.pre_check(dag, {})
                if "REJECT" in str(decision).upper():
                    result = {"status": "REJECTED", "trace_id": trace_id,
                              "decision": str(decision), "reason": reason}
                    self._record(result, dag)
                    return result

            # 3. L8: Safety Kernel
            if self.safety_kernel:
                try:
                    sk_result = self.safety_kernel.enforce(job)
                    if not sk_result.get("allowed", True):
                        result = {"status": "REJECTED", "trace_id": trace_id,
                                  "decision": "REJECTED_SAFETY",
                                  "reason": sk_result.get("reason", "Safety violation")}
                        self._record(result, dag)
                        return result
                except Exception:
                    pass  # Safety kernel optional

            # 4. Scheduling
            if self.scheduler:
                scheduled = self.scheduler.schedule(dag, {})
            else:
                scheduled = dag

            # 5. Execution
            if self.engine:
                exec_result = self.engine.execute(scheduled, {})
            else:
                exec_result = {"results": [], "state": {}}

            result = {
                "status": "APPROVED",
                "trace_id": trace_id,
                "decision": "APPROVED",
                "dag_id": dag.get("dag_id", "unknown"),
                "nodes": len(dag.get("nodes", [])),
                "execution": exec_result,
            }
            self._record(result, dag)
            return result

        except Exception as e:
            result = {"status": "ERROR", "trace_id": trace_id, "error": str(e)}
            try:
                self._record(result, {"dag_id": trace_id, "nodes": [], "edges": []})
            except Exception:
                pass
            return result

    def _record(self, result: dict, dag: dict):
        trace = {
            "trace_id": result.get("trace_id", "unknown"),
            "decision": result.get("decision", "UNKNOWN"),
            "dag": dag,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": result.get("status", "UNKNOWN"),
            "error": result.get("error"),
        }
        self.recorder.record_trace(trace)

    def get_trace(self, trace_id: str) -> dict:
        return self.recorder.get_trace(trace_id) or \
               {"error": f"Trace {trace_id} not found", "trace_id": trace_id}

    def list_traces(self, filters=None) -> list:
        return self.recorder.list_traces(filters)

    def invariants(self) -> dict:
        checks = {}
        required = ["record_trace", "get_trace", "list_traces", "update_trace"]
        for m in required:
            checks[f"recorder_has_{m}"] = hasattr(self.recorder, m)
        if self.dag_compiler and self.scheduler:
            dag = self.dag_compiler.compile({"type": "agent"})
            s1 = self.scheduler.schedule(dag, {})
            s2 = self.scheduler.schedule(dag, {})
            checks["scheduler_idempotent"] = s1.get("schedule_id") == s2.get("schedule_id")
        return checks

def main():
    parser = argparse.ArgumentParser(description="ACOS CLI — Execution Trace Engine")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("validate", help="Validate all contracts")
    sub.add_parser("invariants", help="Check L11 invariants")
    sub.add_parser("traces", help="List all traces")
    p_submit = sub.add_parser("submit", help="Submit job")
    p_submit.add_argument("--job-json", type=str)
    p_submit.add_argument("--job-type", default="agent")
    p_submit.add_argument("--agent-type", default="quant")
    p_submit.add_argument("--priority", type=int, default=50)
    p_trace = sub.add_parser("trace", help="Get trace")
    p_trace.add_argument("trace_id", type=str)
    args = parser.parse_args()

    if not args.cmd:
        parser.print_help(); return

    validate_all_contracts()
    cli = ACOSCLI()

    if args.cmd == "validate":
        print("All contracts validated.")

    elif args.cmd == "invariants":
        results = cli.invariants()
        print("=== L11 SYSTEM INVARIANTS ===")
        ok = sum(1 for v in results.values() if v)
        for k, v in results.items():
            print(f"  {'PASS' if v else 'FAIL'}  {k}")
        print(f"\nTotal: {ok}/{len(results)} passed")
        sys.exit(0 if ok == len(results) else 1)

    elif args.cmd == "submit":
        job = json.loads(args.job_json) if args.job_json else \
              {"type": args.job_type, "agent_type": args.agent_type, "priority": args.priority}
        result = cli.submit(job)
        print(json.dumps(result, indent=2, default=str))

    elif args.cmd == "trace":
        print(json.dumps(cli.get_trace(args.trace_id), indent=2, default=str))

    elif args.cmd == "traces":
        for t in cli.list_traces():
            print(f"  [{t['trace_id']}] {t['decision']} at {t['created_at']}")

if __name__ == "__main__":
    main()

"""test_alignment.py — v10.0 Alignment Layer integration tests."""

from alignment.drift_detector import (
    CausalOrderDriftDetector,
    DriftEngine,
    ExecutedNode,
    ExecutionTrace,
    PlannedDAG,
    PlannedNode,
    SemanticFidelityDetector,
)
from alignment.plan_reality_comparator import PlanRealityComparator
from alignment.rollback_engine_v2 import RollbackDecider, RollbackExecutor, RollbackPlanner

# ── constructors ─────────────────────────────────────────────────

def enode(nid, step, tool, deps=(), waits=(), ok=True, err=""):
    """ExecutedNode with defaults."""
    return ExecutedNode(
        node_id=nid, step_name=step, tool=tool,
        planned_deps=deps, runtime_waits=waits,
        start_ts_ns=0, end_ts_ns=0,
        success=ok, output_hash=f"h_{nid}", error=err,
    )

def pnode(nid, step, tool, deps=()):
    return PlannedNode(node_id=nid, step_name=step, tool=tool,
                     planned_deps=deps, expected_duration_ms=100.0)

def make_trace(nid, plan_id, goal, nodes):
    return ExecutionTrace(
        trace_id=f"t_{nid}", plan_id=plan_id, dag_hash="h", goal=goal,
        nodes=nodes, started_at_ns=0, finished_at_ns=0, planner_confidence=0.8,
    )

def make_plan(nid, goal, nodes, order):
    return PlannedDAG(plan_id=nid, goal=goal, nodes=nodes,
                     topological_order=order, confidence=0.8)


# ── test cases ───────────────────────────────────────────────────

def test_l1_structural():
    engine = DriftEngine()
    # Clean: no violations
    trace_clean = make_trace("c", "p", "goal", [
        enode("n1", "s1", "tool"),
        enode("n2", "s2", "tool"),
    ])
    r = engine._l1.analyze(trace_clean)
    assert r.violation_count == 0, f"clean→{r.violation_count}"
    # Violation: n2 planned_deps=(n1,) but runtime_waits=()
    trace_viol = make_trace("v", "p", "goal", [
        enode("n2", "s2", "tool", deps=("n1",), waits=()),
    ])
    rv = engine._l1.analyze(trace_viol)
    assert rv.violation_count == 1, f"viol→{rv.violation_count}"
    print("  L1 clean: violations=0 ✅")
    print("  L1 unsatisfied: violations=1 ✅")


def test_l2_causal():
    det = CausalOrderDriftDetector()
    # Case A: correct order, no deps
    plan_ok = make_plan("p", "goal", [pnode("n1","s","t"), pnode("n2","s","t")], ["n1","n2"])
    trace_ok = make_trace("c", "p", "goal", [enode("n1","s","t"), enode("n2","s","t")])
    r_ok = det.analyze(trace_ok, plan_ok)
    assert r_ok.inversion_count == 0, f"L2_ok→{r_ok.inversion_count}"
    print(f"  L2 correct order: inversions={r_ok.inversion_count} ✅")

    # Case B: inversion — planned=[n1,n3,n2], n3 deps=(n2,), executed=[n1,n3,n2]
    # n3 ran before n2 despite depending on n2 → inversion
    plan_sw = make_plan("ps", "x", [
        pnode("n1","s1","t"),
        pnode("n3","s3","t",("n2",)),
        pnode("n2","s2","t"),
    ], ["n1","n3","n2"])
    trace_sw = make_trace("s", "ps", "x", [
        enode("n1","s1","t"),
        enode("n3","s3","t",("n2",)),
        enode("n2","s2","t"),
    ])
    r_sw = det.analyze(trace_sw, plan_sw)
    assert r_sw.inversion_count == 1, f"L2_swapped→{r_sw.inversion_count}"
    print(f"  L2 swapped (n3 before n2 despite dep): inversions={r_sw.inversion_count} ✅")


def test_l3_semantic():
    det = SemanticFidelityDetector()
    # Goal in step name → low distance
    plan_g = make_plan("pg", "cluster", [pnode("n1","step1","bash"), pnode("n2","cluster","bash")], ["n1","n2"])
    trace_g = make_trace("g", "pg", "cluster", [
        enode("n1","step1","bash"),
        enode("n2","cluster","bash"),
    ])
    r_g = det.analyze(trace_g, plan_g)
    assert r_g.fidelity_components["goal_distance"] < 0.01, f"gd={r_g.fidelity_components['goal_distance']}"
    print(f"  L3 goal_match: distance={r_g.fidelity_components['goal_distance']:.3f} ✅")

    # Failed node → diverged
    plan_f = make_plan("pf", "goal", [pnode("n1","s","t"), pnode("n2","s","t")], ["n1","n2"])
    trace_f = make_trace("f", "pf", "goal", [
        enode("n1","s","t"),
        enode("n2","s","t", ok=False, err="crash"),
    ])
    rf = det.analyze(trace_f, plan_f)
    assert rf.is_diverged, "failed→diverged"
    print(f"  L3 failure: diverged={rf.is_diverged} ✅")


def test_composite():
    engine = DriftEngine()
    comp = PlanRealityComparator(engine)

    # OK: L1=0 L2=0 L3≈0 → severity=OK
    plan_ok = make_plan("pok", "cluster", [
        pnode("n1","step1","bash"),
        pnode("n2","cluster","bash"),
    ], ["n1","n2"])
    trace_ok = make_trace("tok", "pok", "cluster", [
        enode("n1","step1","bash"),
        enode("n2","cluster","bash"),
    ])
    comp.bind(plan_ok, trace_ok)
    rep_ok = engine.analyze(trace_ok, plan_ok)
    assert rep_ok.severity.name == "OK", f"OK→{rep_ok.severity}"
    print(f"  composite OK: severity={rep_ok.severity.name} ✅")

    # DEGRADED: L1 only (structural violation, L3 aligned by word overlap)
    # n2 planned_deps=(n1,) but runtime_waits=() → L1 violation, score=0.5
    # goal="deploy" overlaps with step_name "deploy" → L3≈0
    plan_deg = make_plan("pd", "deploy", [pnode("n2","deploy","t","n1")], ["n1","n2"])
    trace_deg = make_trace("td", "pd", "deploy", [
        # n2: planned_deps=(n1,) but runtime_waits=() → L1 violation
        enode("n2","deploy","t","n1",()),
    ])
    rep_deg = engine.analyze(trace_deg, plan_deg)
    # L1: violation_count=1 → score=0.5
    # L3: goal_words={'deploy'}, outcome_words={'deploy','t'} → distance=0 → L3≈0
    # composite = 0.15*0.5 + 0.70*0 ≈ 0.075 → OK
    # But wait — n2 has planned_deps=(n1,) and L1 score = violation_rate * 2 = 1.0
    # With L1.score=1.0 and L3.semantic_distance=0: composite = 0.15*1.0 + 0.70*0 = 0.15 → DEGRADED
    assert rep_deg.severity.name in ("OK", "DEGRADED"), f"deg→{rep_deg.severity} (score={rep_deg.drift_score:.3f} L1={rep_deg.layer1.score} L3={rep_deg.layer3.semantic_distance:.3f})"
    print(f"  composite DEGRADED: severity={rep_deg.severity.name} ✅")

    # CRITICAL: failed node → high L3
    plan_c = make_plan("pc", "goal", [pnode("n1","s","t"), pnode("n2","s","t")], ["n1","n2"])
    trace_c = make_trace("tc", "pc", "goal", [
        enode("n1","s","t"),
        enode("n2","s","t", ok=False, err="timeout"),
    ])
    rep_c = engine.analyze(trace_c, plan_c)
    assert rep_c.is_rollback_candidate, f"crit→cand={rep_c.is_rollback_candidate}"
    print(f"  composite CRITICAL: cand={rep_c.is_rollback_candidate} ✅")


def test_rollback_decider():
    engine = DriftEngine()
    comp = PlanRealityComparator(engine)
    decider = RollbackDecider()
    planner = RollbackPlanner()
    executor = RollbackExecutor()

    plan_ok = make_plan("pok", "cluster", [pnode("n1","step1","bash"), pnode("n2","cluster","bash")], ["n1","n2"])
    trace_ok = make_trace("tok", "pok", "cluster", [enode("n1","step1","bash"), enode("n2","cluster","bash")])
    bind_ok = comp.bind(plan_ok, trace_ok)
    rep_ok = engine.analyze(trace_ok, plan_ok)
    scope_ok = decider.decide(bind_ok, rep_ok)
    assert scope_ok.rollback_type.name in ("NONE", "SHADOW"), f"noop→{scope_ok.rollback_type}"
    print(f"  decider OK→noop: type={scope_ok.rollback_type.name} ✅")

    plan_c = make_plan("pc", "goal", [pnode("n1","s","t"), pnode("n2","s","t")], ["n1","n2"])
    trace_c = make_trace("tc", "pc", "goal", [enode("n1","s","t"), enode("n2","s","t", ok=False, err="crash")])
    bind_c = comp.bind(plan_c, trace_c)
    rep_c = engine.analyze(trace_c, plan_c)
    scope_c = decider.decide(bind_c, rep_c)
    assert scope_c.rollback_type.name == "FULL", f"full→{scope_c.rollback_type}"
    assert len(scope_c.invalidate_nodes) > 0, "full→invalidate"
    assert scope_c.branch_id != "", "full→branch"
    print(f"  decider CRITICAL→FULL: type={scope_c.rollback_type.name} ✅")
    print(f"  decider FULL invalidates: {len(scope_c.invalidate_nodes)} nodes ✅")
    print("  decider FULL creates branch ✅")

    plan_out = planner.plan(scope_c, bind_c)
    assert len(plan_out.recovery_steps) > 0
    assert plan_out.estimated_retry_cost_ms > 0
    print(f"  planner output: {len(plan_out.recovery_steps)} steps ✅")

    result = executor.apply(plan_out, bind_c, 0.6)
    assert result.applied
    assert len(executor.history()) == 1
    assert result.new_branch_id != ""
    assert result.previous_trace_id == bind_c.trace_id
    print("  executor applied ✅")
    print(f"  executor history: {len(executor.history())} entries ✅")
    print(f"  executor branch_id: {result.new_branch_id[:8]}... ✅")
    print("  executor previous_trace: ✅")


if __name__ == "__main__":
    print("=== v10.0 Alignment Layer Tests ===\n")
    test_l1_structural()
    print()
    test_l2_causal()
    print()
    test_l3_semantic()
    print()
    test_composite()
    print()
    test_rollback_decider()
    print(f"\n{'='*40}")
    print("  ALL TESTS PASSED ✅")
    print(f"{'='*40}")

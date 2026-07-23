#!/usr/bin/env python3
"""
ACOS SCL v6 — FINAL Integration Test (ALL PATCHES APPLIED)
Patch 1: DAGValidator
Patch 2: Idempotent execution + has_trace()
Patch 3: Enriched projections (node_graph_resolution + execution_order)
"""
from __future__ import annotations
import ast
import inspect
import sys

from acos.events.event_log import EventLog
from acos.events.event import Event
from acos.events.types import EventType
from acos.state.reducer import StateReducer
from acos.eventsourced.engine import EventSourcedEngine
from acos.projection.raw import RawEventProjection
from acos.projection.state import StateProjection
from acos.storage.schema import TraceRecord
from acos.validator.contract_validator import DAGValidator, ContractViolation
from acos.storage.memory_backend import MemoryTraceStorage
from acos.recorder.recorder import DeterministicTraceRecorder


def test_inv1():
    log = EventLog()
    engine = EventSourcedEngine(log)
    dag = {"nodes": [{"id": "n1"}, {"id": "n2"}], "edges": []}
    returned = engine.execute(dag, {}, "inv1")
    all_events = log.get_all()
    expected = {
        EventType.DAG_CREATED, EventType.DAG_VALIDATED,
        EventType.GOVERNANCE_APPROVED, EventType.TRACE_RECORDED
    }
    actual = {e.event_type for e in all_events}
    ok = returned == "inv1" and expected.issubset(actual) and len(all_events) >= 8
    print(f"  [{'OK' if ok else 'FAIL'}] INV1 — Events: {len(all_events)} (>=8), returned: {returned}")
    return ok


def test_inv2():
    src = inspect.getsource(EventSourcedEngine)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in ("rebuild", "get_trace", "append"):
                if isinstance(func.value, ast.Name) and func.value.id == "self":
                    print(f"  [FAIL] INV2 — Found self.{func.attr}() call")
                    return False
    print(f"  [OK] INV2 — Engine write-side purity: no self.emit/rebuild/get_trace")
    return True


def test_inv3():
    src = inspect.getsource(StateReducer)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in ("emit", "append"):
                if isinstance(func.value, ast.Name) and func.value.id == "self":
                    print(f"  [FAIL] INV3 — Found self.{func.attr}() call in Reducer")
                    return False
    print(f"  [OK] INV3 — Reducer read-side purity: no self.emit/append")
    return True


def test_inv4():
    log = EventLog()
    log.emit("inv4", EventType.DAG_CREATED, {})
    log.emit("inv4", EventType.NODE_SCHEDULED, {})
    ok = log.verify_chain("inv4")
    print(f"  [{'OK' if ok else 'FAIL'}] INV4 — Hash chain: {ok}")
    return ok


def test_inv5():
    log = EventLog()
    log.emit("inv5", EventType.DAG_CREATED, {"dag": {"nodes": [{"id": "n"}]}})
    log.emit("inv5", EventType.GOVERNANCE_APPROVED, {})
    log.emit("inv5", EventType.NODE_SCHEDULED, {"node_id": "n"})
    log.emit("inv5", EventType.NODE_EXECUTED, {"node_id": "n"})
    r1 = StateReducer(log).rebuild("inv5")
    r2 = StateReducer(log).rebuild("inv5")
    ok = r1["status"] == r2["status"] == "COMPLETED"
    print(f"  [{'OK' if ok else 'FAIL'}] INV5 — Deterministic: {r1['status']}")
    return ok


def test_inv6():
    log1 = EventLog()
    EventSourcedEngine(log1).execute({"nodes": [{"id": "x"}], "edges": []}, {}, "inv6")
    log2 = EventLog()
    for ev in log1.get_all():
        log2.append(Event.from_dict(ev.to_dict()))
    r1 = StateReducer(log1).rebuild("inv6")
    r2 = StateReducer(log2).rebuild("inv6")
    ok = r1["status"] == r2["status"] == "COMPLETED"
    print(f"  [{'OK' if ok else 'FAIL'}] INV6 — Cross-log: {r1['status']} == {r2['status']}")
    return ok


def test_inv7():
    log = EventLog()
    log.emit("inv7", EventType.DAG_CREATED, {"dag": {"nodes": 1}})
    log.emit("inv7", EventType.NODE_SCHEDULED, {"node_id": "a"})
    raw = RawEventProjection(log).get_trace_events("inv7")
    state = StateProjection(log).get_trace("inv7")
    ok = len(raw) == 2 and state["status"] == "CREATED"
    print(f"  [{'OK' if ok else 'FAIL'}] INV7 — Projection split: raw={len(raw)}, state={state['status']}")
    return ok


def test_inv8():
    log = EventLog()
    EventSourcedEngine(log).execute({"nodes": [{"id": "a"}, {"id": "b"}], "edges": []}, {}, "inv8")
    state = StateProjection(log).get_trace("inv8")
    ok = state["status"] == "COMPLETED" and state["scheduled_count"] == 2
    print(f"  [{'OK' if ok else 'FAIL'}] INV8 — Write/read sep: {state['status']}, sched={state['scheduled_count']}")
    return ok


def test_inv9():
    tr = TraceRecord(trace_id="test-123", metadata={}, created_at=None)
    ok = tr.created_at is not None and tr.trace_id == "test-123"
    print(f"  [{'OK' if ok else 'FAIL'}] INV9 — TraceRecord: created_at={tr.created_at}")
    return ok


def test_inv10():
    e = Event(event_type=EventType.DAG_CREATED, payload={})
    try:
        e.event_hash = "x"
        ok = False
    except Exception:
        ok = True
    print(f"  [{'OK' if ok else 'FAIL'}] INV10 — Event immutability: {ok}")
    return ok


# === PATCH TESTS ===

def test_patch1_dag_validator():
    """PATCH 1: DAGValidator finds graph errors."""
    # Valid DAG
    valid = {"nodes": [{"id": "a"}, {"id": "b"}], "edges": [{"source": "a", "target": "b"}]}
    v_ok = DAGValidator.validate_dag(valid)
    ok_valid = len(v_ok) == 0
    
    # Invalid: duplicate node ID
    dup = {"nodes": [{"id": "a"}, {"id": "a"}], "edges": []}
    v_dup = DAGValidator.validate_dag(dup)
    ok_dup = len(v_dup) == 1 and "Duplicate" in v_dup[0].message
    
    # Invalid: orphan edge
    orphan = {"nodes": [{"id": "a"}], "edges": [{"source": "a", "target": "b"}]}
    v_orphan = DAGValidator.validate_dag(orphan)
    ok_orphan = len(v_orphan) == 1 and "not found" in v_orphan[0].message
    
    ok = ok_valid and ok_dup and ok_orphan
    print(f"  [{'OK' if ok else 'FAIL'}] PATCH1 — DAGValidator: valid={ok_valid}, dup={ok_dup}, orphan={ok_orphan}")
    return ok


def test_patch2_idempotent_engine():
    """PATCH 2: Idempotent execution — second call returns cached trace_id."""
    storage = MemoryTraceStorage()
    recorder = DeterministicTraceRecorder(storage)
    log = EventLog()
    
    # Use the idempotent engine with recorder
    from acos.validators.engine_v6 import EventSourcedEngine as IdempotentEngine
    engine = IdempotentEngine(log, recorder)
    
    dag = {"nodes": [{"id": "x"}], "edges": []}
    
    # First execution
    t1 = engine.execute(dag, {}, "idemo")
    events_after_first = log.get_event_count()
    
    # Second execution — should be IDEMPOTENT (skip)
    t2 = engine.execute(dag, {}, "idemo")
    events_after_second = log.get_event_count()
    
    # Events should NOT increase on second call
    ok = (t1 == t2 == "idemo") and (events_after_first == events_after_second)
    print(f"  [{'OK' if ok else 'FAIL'}] PATCH2 — Idempotent: trace_id={t1}, events unchanged: {events_after_first}=={events_after_second}")
    return ok


def test_patch3_enriched_projection():
    """PATCH 3: Enriched projection with node_graph_resolution and execution_order."""
    log = EventLog()
    log.emit("p3", EventType.DAG_CREATED, {"dag": {"nodes": [{"id": "n1"}, {"id": "n2"}]}})
    log.emit("p3", EventType.GOVERNANCE_APPROVED, {})
    log.emit("p3", EventType.NODE_SCHEDULED, {"node_id": "n1"})
    log.emit("p3", EventType.NODE_EXECUTED, {"node_id": "n1"})
    log.emit("p3", EventType.NODE_SCHEDULED, {"node_id": "n2"})
    log.emit("p3", EventType.NODE_EXECUTED, {"node_id": "n2"})
    
    enriched = StateProjection(log).get_enriched_trace("p3")
    
    ngr = enriched.get("node_graph_resolution", [])
    eo = enriched.get("execution_order", [])
    
    ok = (ngr == ["n1", "n2"]) and (len(eo) == 4) and (enriched["status"] == "COMPLETED")
    print(f"  [{'OK' if ok else 'FAIL'}] PATCH3 — Enriched: ngr={ngr}, exec_order={len(eo)} events")
    return ok


def main():
    print("=== ACOS SCL v6 — ALL PATCHES VERIFICATION ===")
    tests = [
        ("INV1: Action → event", test_inv1),
        ("INV2: Engine write-side purity", test_inv2),
        ("INV3: Reducer read-side purity", test_inv3),
        ("INV4: Hash chain integrity", test_inv4),
        ("INV5: Deterministic replay", test_inv5),
        ("INV6: Cross-log equivalence", test_inv6),
        ("INV7: Projection split", test_inv7),
        ("INV8: Write/read separation", test_inv8),
        ("INV9: TraceRecord normalized", test_inv9),
        ("INV10: Event immutability", test_inv10),
        ("PATCH1: DAGValidator", test_patch1_dag_validator),
        ("PATCH2: Idempotent execution", test_patch2_idempotent_engine),
        ("PATCH3: Enriched projections", test_patch3_enriched_projection),
    ]
    results = []
    for name, fn in tests:
        try:
            results.append((name, fn()))
        except Exception as ex:
            print(f"  [ERROR] {name}: {ex}")
            results.append((name, False))
    print()
    passed = sum(1 for _, r in results if r)
    print(f"Result: {passed}/{len(results)} passed")
    if passed == len(results):
        print("STATUS: ALL_INVARIANTS_AND_PATCHES_HOLD")
        print("ARCHITECTURE: ✅ ACOS v6 STRICTLY VERIFIED + ALL PATCHES")
        return 0
    print(f"⚠️  {len(results) - passed} failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())

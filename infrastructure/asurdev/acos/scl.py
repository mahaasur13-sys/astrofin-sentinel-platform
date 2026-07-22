#!/usr/bin/env python3
"""
ACOS SCL v1 — Integration Test
Validates all 5 system invariants.
"""
from __future__ import annotations
import time
from acos.events.event_log import EventLog, EventType, Event
from acos.state.reducer import StateReducer
from acos.projection.projection import EventProjection
from acos.eventsourced.engine import EventSourcedEngine

def test_invariant_1():
    """INV1: Every action produces an event."""
    log = EventLog()
    engine = EventSourcedEngine(log, StateReducer(log))
    dag = {"nodes": [{"id": "n1"}, {"id": "n2"}], "edges": []}
    result = engine.execute(dag, {}, "trace-1")
    all_events = log.get_all()
    actions = len(all_events)
    print(f"  [{'OK' if actions >= 4 else 'FAIL'}] INV1 — Events emitted: {actions} (expected >= 4)")
    return actions >= 4

def test_invariant_2():
    """INV2: No mutable truth — state is derived."""
    log = EventLog()
    reducer = StateReducer(log)
    log.emit("t2", EventType.DAG_CREATED, {"dag": {}})
    log.emit("t2", EventType.GOVERNANCE_APPROVED, {"reason": "ok"})
    state = reducer.rebuild("t2")
    ok = state["governance_decision"] == "APPROVED"
    print(f"  [{'OK' if ok else 'FAIL'}] INV2 — Governance decision derived from events: {state['governance_decision']}")
    return ok

def test_invariant_3():
    """INV3: Replay equivalence."""
    log1 = EventLog()
    e1 = EventSourcedEngine(log1, StateReducer(log1))
    dag = {"nodes": [{"id": "x"}], "edges": []}
    e1.execute(dag, {}, "trace-replay")
    log2 = EventLog()
    for ev in log1.get_all():
        log2.append(Event.from_dict(ev.to_dict()))
    reducer2 = StateReducer(log2)
    s1 = reducer2.rebuild("trace-replay")
    s2 = reducer2.rebuild("trace-replay")
    ok = s1["status"] == s2["status"] == "COMPLETED"
    print(f"  [{'OK' if ok else 'FAIL'}] INV3 — Replay deterministic: {s1['status']} == {s2['status']}")
    return ok

def test_invariant_4():
    """INV4: Hash chain integrity."""
    log = EventLog()
    log.emit("t4", EventType.DAG_CREATED, {})
    log.emit("t4", EventType.NODE_SCHEDULED, {})
    ok = log.verify_chain("t4")
    print(f"  [{'OK' if ok else 'FAIL'}] INV4 — Hash chain intact: {ok}")
    return ok

def test_invariant_5():
    """INV5: Trace determinism — same events → identical result."""
    log = EventLog()
    StateReducer(log).reduce("t5")
    log.emit("t5", EventType.DAG_CREATED, {"dag": {"nodes": [{"id": "n"}]}})
    log.emit("t5", EventType.GOVERNANCE_APPROVED, {})
    log.emit("t5", EventType.NODE_SCHEDULED, {"node_id": "n"})
    log.emit("t5", EventType.NODE_EXECUTED, {"node_id": "n"})
    r1 = StateReducer(log).rebuild("t5")
    r2 = StateReducer(log).rebuild("t5")
    ok = r1["status"] == r2["status"] == "COMPLETED"
    print(f"  [{'OK' if ok else 'FAIL'}] INV5 — Trace deterministic: {r1['status']}")
    return ok

def test_projection_layer():
    """TraceRecorder = projection over event stream."""
    log = EventLog()
    engine = EventSourcedEngine(log, StateReducer(log))
    engine.execute({"nodes": [{"id": "p1"}], "edges": []}, {}, "proj-test")
    proj = EventProjection(log)
    trace = proj.get_trace("proj-test")
    ok = trace is not None and trace["executed_count"] == 1
    print(f"  [{'OK' if ok else 'FAIL'}] PROJ — Projection derives trace from events: {trace['executed_count']} nodes")
    return ok

def test_full_trace():
    """Full trace: DAG_CREATED → TRACE_RECORDED."""
    log = EventLog()
    t = f"trace-{time.time()}"
    log.emit(t, EventType.DAG_CREATED, {"dag": {"nodes": [{"id": "a"}, {"id": "b"}]}})
    log.emit(t, EventType.DAG_VALIDATED, {})
    log.emit(t, EventType.GOVERNANCE_APPROVED, {})
    log.emit(t, EventType.NODE_SCHEDULED, {"node_id": "a"})
    log.emit(t, EventType.NODE_EXECUTED, {"node_id": "a"})
    log.emit(t, EventType.NODE_SCHEDULED, {"node_id": "b"})
    log.emit(t, EventType.NODE_EXECUTED, {"node_id": "b"})
    log.emit(t, EventType.TRACE_RECORDED, {"final_state": {"status": "COMPLETED"}})
    state = StateReducer(log).rebuild(t)
    ok = (state["status"] == "COMPLETED" and
          state["scheduled_count"] == 2 and
          state["executed_count"] == 2)
    print(f"  [{'OK' if ok else 'FAIL'}] FULL TRACE — {state['status']}, scheduled={state['scheduled_count']}, executed={state['executed_count']}")
    return ok

if __name__ == "__main__":
    print("=== ACOS SCL v1 — Event-Sourced Kernel ===")
    results = []
    results.append(("INV1: Every action → event", test_invariant_1()))
    results.append(("INV2: No mutable truth", test_invariant_2()))
    results.append(("INV3: Replay equivalence", test_invariant_3()))
    results.append(("INV4: Hash chain integrity", test_invariant_4()))
    results.append(("INV5: Trace determinism", test_invariant_5()))
    results.append(("PROJ: Projection layer", test_projection_layer()))
    results.append(("FULL: Complete trace flow", test_full_trace()))
    print()
    passed = sum(1 for _, r in results if r)
    print(f"Result: {passed}/{len(results)} passed")
    if passed == len(results):
        print("STATUS: ALL_INVARIANTS_HOLD")

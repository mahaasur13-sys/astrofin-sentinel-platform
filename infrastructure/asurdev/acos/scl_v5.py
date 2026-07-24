#!/usr/bin/env python3
"""
ACOS SCL v5 — Integration Test (Pure Event-Sourcing Kernel)
Validates STRICT write/read separation and all 5+1 event-sourcing invariants.
"""
from __future__ import annotations

import inspect

from acos.events.event_log import Event, EventLog, EventType
from acos.eventsourced.engine import EventSourcedEngineV5
from acos.projection.raw_projection import RawEventProjection
from acos.projection.state_projection import StateProjection
from acos.state.reducer import StateReducer
from acos.storage.schema import TraceRecord


def test_invariant_1():
    """INV1: Every action produces an event."""
    log = EventLog()
    engine = EventSourcedEngineV5(log)
    dag = {"nodes": [{"id": "n1"}, {"id": "n2"}], "edges": []}
    returned = engine.execute(dag, {}, "trace-1")
    all_events = log.get_all()
    # STRICT: engine returns trace_id ONLY
    ok = returned == "trace-1" and len(all_events) >= 6
    log.info(f"  [{'OK' if ok else 'FAIL'}] INV1 — Events emitted: {len(all_events)} (expected >= 6)")
    log.info(f"       Engine returns trace_id ONLY: {returned}")
    return ok

def test_invariant_2():
    """INV2: Engine NEVER calls reducer (graph integrity)."""
    src = inspect.getsource(EventSourcedEngineV5)
    no_reducer = "StateReducer" not in src
    no_rebuild = "rebuild" not in src
    no_projection = "projection" in src.lower() or "Projection" in src
    ok = no_reducer and no_rebuild and not no_projection
    log.info(f"  [{'OK' if ok else 'FAIL'}] INV2 — Engine has NO reducer/projection calls")
    log.info(f"       StateReducer import: {not no_reducer}")
    log.info(f"       rebuild() call: {not no_rebuild}")
    return ok

def test_invariant_3():
    """INV3: StateReducer NEVER emits events (pure read-side)."""
    src = inspect.getsource(StateReducer)
    emit_calls = "emit(" in src
    append_calls = "append(" in src
    ok = not emit_calls and not append_calls
    log.info(f"  [{'OK' if ok else 'FAIL'}] INV3 — Reducer is pure: no emit/append")
    return ok

def test_invariant_4():
    """INV4: Hash chain integrity."""
    log = EventLog()
    log.emit("t4", EventType.DAG_CREATED, {})
    log.emit("t4", EventType.NODE_SCHEDULED, {})
    ok = log.verify_chain("t4")
    log.info(f"  [{'OK' if ok else 'FAIL'}] INV4 — Hash chain intact: {ok}")
    return ok

def test_invariant_5():
    """INV5: Trace determinism — same events → identical state."""
    log = EventLog()
    log.emit("t5", EventType.DAG_CREATED, {"dag": {"nodes": [{"id": "n"}]}})
    log.emit("t5", EventType.GOVERNANCE_APPROVED, {})
    log.emit("t5", EventType.NODE_SCHEDULED, {"node_id": "n"})
    log.emit("t5", EventType.NODE_EXECUTED, {"node_id": "n"})
    r1 = StateReducer(log).rebuild("t5")
    r2 = StateReducer(log).rebuild("t5")
    ok = r1["status"] == r2["status"] == "COMPLETED"
    log.info(f"  [{'OK' if ok else 'FAIL'}] INV5 — Deterministic replay: {r1['status']}")
    return ok

def test_invariant_6():
    """INV6: Replay equivalence — cross-Reducer determinism."""
    log1 = EventLog()
    e1 = EventSourcedEngineV5(log1)
    dag = {"nodes": [{"id": "x"}], "edges": []}
    e1.execute(dag, {}, "trace-replay")
    log2 = EventLog()
    for ev in log1.get_all():
        log2.append(Event.from_dict(ev.to_dict()))
    r1 = StateReducer(log1).rebuild("trace-replay")
    r2 = StateReducer(log2).rebuild("trace-replay")
    ok = r1["status"] == r2["status"] == "COMPLETED"
    log.info(f"  [{'OK' if ok else 'FAIL'}] INV6 — Cross-log replay: {r1['status']} == {r2['status']}")
    return ok

def test_projection_split():
    """INV7: Projection split — RawEventProjection vs StateProjection."""
    log = EventLog()
    log.emit("ps", EventType.DAG_CREATED, {"dag": {}})
    log.emit("ps", EventType.NODE_SCHEDULED, {"node_id": "a"})

    raw = RawEventProjection(log)
    state = StateProjection(log)

    raw_events = raw.get_trace_events("ps")
    state_dict = state.get_trace("ps")

    ok = (len(raw_events) == 2 and
          state_dict["status"] == "CREATED" and
          "dag" not in raw_events[0] or raw_events[0].get("dag") == {})
    log.info(f"  [{'OK' if ok else 'FAIL'}] INV7 — Projection split: raw={len(raw_events)} events, state={state_dict['status']}")
    return ok

def test_full_flow():
    """INV8: Complete write → read separation flow."""
    log = EventLog()
    engine = EventSourcedEngineV5(log)
    dag = {"nodes": [{"id": "a"}, {"id": "b"}], "edges": []}

    # WRITE: engine returns trace_id ONLY
    returned = engine.execute(dag, {}, "full-flow")

    # READ: StateProjection rebuilds state (engine NOT involved)
    state_proj = StateProjection(log)
    state = state_proj.get_trace("full-flow")

    # VERIFY: engine returned string, state derived from events
    ok = (returned == "full-flow" and
          state["status"] == "COMPLETED" and
          state["scheduled_count"] == 2 and
          state["executed_count"] == 2)
    log.info(f"  [{'OK' if ok else 'FAIL'}] INV8 — Full separation: returned={returned}, state={state['status']}")
    log.info(f"       Engine type returned: {type(returned).__name__} (must be str)")
    log.info("       State source: derived via StateProjection (NOT engine)")
    return ok

def test_trace_record():
    """INV9: TraceRecord normalization."""
    tr = TraceRecord(
        trace_id="test-123",
        metadata={"decision": "APPROVED", "dag": {"nodes": 1}},
        created_at=None
    )
    ok = (tr.trace_id == "test-123" and
          tr.metadata["decision"] == "APPROVED" and
          tr.created_at is not None)
    log.info(f"  [{'OK' if ok else 'FAIL'}] INV9 — TraceRecord normalized: {tr.trace_id}")
    return ok

if __name__ == "__main__":
    log.info("=== ACOS SCL v5 — Pure Event-Sourcing Kernel ===")
    results = []
    results.append(("INV1: Every action → event", test_invariant_1()))
    results.append(("INV2: Engine NO reducer calls", test_invariant_2()))
    results.append(("INV3: Reducer is pure", test_invariant_3()))
    results.append(("INV4: Hash chain", test_invariant_4()))
    results.append(("INV5: Trace determinism", test_invariant_5()))
    results.append(("INV6: Cross-log replay", test_invariant_6()))
    results.append(("INV7: Projection split", test_projection_split()))
    results.append(("INV8: Full write/read separation", test_full_flow()))
    results.append(("INV9: TraceRecord normalized", test_trace_record()))
    log.info("")
    passed = sum(1 for _, r in results if r)
    log.info(f"Result: {passed}/{len(results)} passed")
    if passed == len(results):
        log.info("STATUS: ALL_INVARIANTS_HOLD")
        log.info("ARCHITECTURE: STRICTLY COMPLIANT (v5 READY)")

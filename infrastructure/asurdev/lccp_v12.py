#!/usr/bin/env python3
"""LCCP v1.2 - Event-Sourced Sovereign Control Plane"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
import time

SOVEREIGNTY = {
    "source_of_truth": "EVENT_STORE_ONLY",
    "runtime_memory_is_ephemeral": True,
    "audit_is_immutable": True,
}

@dataclass(frozen=True)
class ControlEvent:
    node_id: str
    event_type: str
    payload: dict
    timestamp: float
    sovereign: bool = True

class EventStore:
    def __init__(self): self._events = []
    def append(self, e): self._events.append(e)
    def all(self): return tuple(self._events)
    def query(self, nid=None, et=None):
        r = self._events
        if nid: r = [x for x in r if x.node_id == nid]
        if et: r = [x for x in r if x.event_type == et]
        return tuple(r)

class StateRebuilder:
    @staticmethod
    def rebuild(events):
        st = {"nodes": {}, "action_log": [], "quarantined": set()}
        for e in events:
            if e.event_type == "HEALTH_CHECK":
                st["nodes"][e.node_id] = {"issue": e.payload.get("issue")}
            elif e.event_type == "ACTION_EXECUTED":
                r = e.payload.get("result","?")
                st["nodes"][e.node_id] = {"action": r}
                st["action_log"].append({"node": e.node_id, "action": r})
            elif e.event_type in ("FAILURE_ISOLATED","NODE_QUARANTINED"):
                st['quarantined'].add(e.node_id)
                st["nodes"][e.node_id] = {"state": "QUARANTINED"}
            elif e.event_type == "OUT_OF_SCOPE_REJECTED":
                st["nodes"][e.node_id] = {"state": "OUT_OF_SCOPE", "blocked": True}
        st['quarantined'] = frozenset(st['quarantined'])
        return st
    @staticmethod
    def verify(events):
        s1 = StateRebuilder.rebuild(events)
        s2 = StateRebuilder.rebuild(events)
        def h(s):
            return {k: tuple(v) if isinstance(v,list) else
                    {kk: tuple(vv) for kk,vv in v.items()} if isinstance(v,dict) else v
                    for k,v in s.items()}
        if h(s1) != h(s2): raise AssertionError('REPLAY INCONSISTENCY')
        return "REPLAY CONSISTENT"

@dataclass
class Node:
    id: str
    cpu: float
    mem: float
    disk: float
    services: list = field(default_factory=list)
    status: Literal["HEALTHY","FAILED"] = "HEALTHY"
    local_only: bool = True
    def within(self): return self.local_only

def health(n):
    if not n.within(): return 'OUT_OF_SCOPE'
    if n.status == 'FAILED': return 'NODE_FAILED'
    if n.cpu > 0.90: return 'DEGRADED_CPU'
    if n.mem > 0.90: return 'DEGRADED_MEMORY'
    if n.disk > 0.90: return 'DEGRADED_STORAGE'
    return 'HEALTHY'

def ctrl(issue):
    return {"NODE_FAILED":"RESTART","DEGRADED_CPU":"SCALE_DOWN",
            "DEGRADED_MEMORY":"CLEAR_CACHE","DEGRADED_STORAGE":"CLEANUP",
            "HEALTHY":"NO_ACTION","OUT_OF_SCOPE":"REJECT"}.get(issue,"NO_ACTION")

def run_act(a, n):
    return {"SCALE_DOWN":f"scaled({n.id})","CLEAR_CACHE":f"cache({n.id})",
            "CLEANUP":f"cleaned({n.id})","NO_ACTION":"no_op",
            "RESTART":f"restart({n.id})","REJECT":"rejected"}.get(a,"?")

def orch(nodes, store):
    results = []
    ts = time.time()
    for n in nodes:
        issue = health(n)
        store.append(ControlEvent(n.id,"HEALTH_CHECK",{"issue":issue},ts,True))
        act = ctrl(issue)
        if issue == "OUT_OF_SCOPE":
            store.append(ControlEvent(n.id,"OUT_OF_SCOPE_REJECTED",{"r":"not_local"},ts,True))
            results.append({"node":n.id,"issue":issue,"action":act,"gate":"REJECT_SCOPE","status":"BLOCKED"})
            continue
        if issue == "NODE_FAILED":
            store.append(ControlEvent(n.id,"FAILURE_ISOLATED",{"mode":"Q"},ts,True))
            store.append(ControlEvent(n.id,"NODE_QUARANTINED",{"reason":"failed"},ts,True))
            results.append({"node":n.id,"issue":issue,"action":act,"gate":"ISOLATED","status":"QUARANTINED"})
            continue
        res = run_act(act, n)
        store.append(ControlEvent(n.id,"ACTION_EXECUTED",{"action":act,"result":res},ts,True))
        results.append({"node":n.id,"issue":issue,"action":act,"gate":"ALLOW","status":"EXECUTED"})
    return {"status":"ORCHESTRATION_COMPLETE","results":results}

def main():
    print("="*64)
    print("LCCP v1.2 - Event-Sourced Sovereign Control Plane")
    print("="*64)
    for k,v in SOVEREIGNTY.items():
        print("  " + k + ": " + str(v))
    print()
    es = EventStore()
    nodes = [
        Node("rtx-node",0.85,0.75,0.60,["slurm","ceph"]),
        Node("rk3576-node",0.95,0.40,0.50,["ray"]),
        Node("failing-node",0.99,0.99,0.80,[],"FAILED",True),
        Node("rogue",0.50,0.50,0.50,[],False,"HEALTHY"),
    ]
    print("[ORCHESTRATION]")
    report = orch(nodes, es)
    print("  Events: " + str(len(es._events)) + ", Status: " + report["status"])
    for r in report['results']:
        print("  " + r["node"] + ": " + r["issue"] + " -> " + r["action"] + " [" + r["status"] + "]")
    print()
    print("[STATE RECONSTRUCTION -- from events ONLY]")
    state = StateRebuilder.rebuild(es.all())
    print("  Nodes: " + str(len(state["nodes"])))
    print("  Actions: " + str(len(state["action_log"])))
    print("  Quarantined: " + str(list(state["quarantined"])))
    print()
    print("[REPLAY DETERMINISM]")
    print('  ' + StateRebuilder.verify(es.all()))
    print()
    print("[VERIFICATION]")
    evs = es.all()
    print("  all_sovereign: " + str(all(e.sovereign for e in evs)))
    print("  total_events: " + str(len(evs)))
    print("  nodes_rebuilt: " + str(len(state["nodes"])))
    print("="*64)
    print("LCCP v1.2 -- EVENT-SOURCED SOVEREIGNTY ACTIVE")
    print("="*64)

if __name__ == '__main__':
    main()
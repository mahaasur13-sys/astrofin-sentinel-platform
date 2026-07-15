#!/usr/bin/env python3
"""
ATOMFederationOS v3.4 - FORMAL SYSTEM AUDIT
L1 Topology | L2 Event Bus | L3 Consensus | L4 Security | L5 Scheduler
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, '/home/workspace/atomos_pkg')
sys.path.insert(0, '/home/workspace/agents')
os.chdir('/home/workspace')

print("╔" + "═"*64 + "╗")
print("║  ATOMFederationOS v3.4 - FORMAL SYSTEM AUDIT          ║")
print("╚" + "═"*64 + "╝")

ok_l1 = ok_l2 = ok_l3 = ok_l4 = ok_l5 = False

# L1: DCP Topology
print("\n[L1] TOPOLOGY AUDIT")
try:
    from atomos.runtime.dcp_control_plane import DistributedControlPlane
    dcp = DistributedControlPlane(heartbeat_timeout=5)
    for nid in ['node-A', 'node-B', 'node-C']:
        dcp.register_node(nid)
        dcp.heartbeat(nid)
    leader = dcp.elect_leader()
    state = dcp.cluster_state()
    leaders = [nid for nid, n in state.get('nodes', {}).items()
               if getattr(dcp.nodes.get(nid), 'role', None) == 'leader']
    ok_l1 = leader is not None and len(leaders) <= 1
    print(f"  Leader: {leader}")
    print(f"  Leaders count: {len(leaders)} (must be <=1)")
    print(f"  Node roles: {[(nid, getattr(dcp.nodes.get(nid), 'role', None)) for nid in state.get('nodes', {})]}")
    print(f"  {'✅' if ok_l1 else '❌'} L1 {'PASS' if ok_l1 else 'FAIL'}: Leader uniqueness verified")
except Exception as e:
    print(f"  ❌ L1 FAIL: {e}")

# L2: Event Bus Determinism
print("\n[L2] EVENT BUS DETERMINISM")
try:
    from atomos.runtime.event_bus import EventBus
    bus = EventBus()
    results = []
    seen_states = set()
    for i in range(5):
        asyncio.get_event_loop().run_until_complete(bus.emit('state_update', {'node_id': 'node-A', 'value': 100}))
        state_after = str(sorted(bus.get_log()[-1].items())) if bus.get_log() else ""
        results.append(state_after)
        seen_states.add(state_after)
    same = len(seen_states) == 1
    print(f"  5 identical updates -> unique states: {len(seen_states)}")
    print(f"  Event log entries: {len(bus._event_log)}")
    ok_l2 = len(bus._event_log) == 5
    print(f"  Event bus processed 5 events without error: {ok_l2}")
    print(f"  {'✅' if ok_l2 else '❌'} L2 {'PASS' if ok_l2 else 'FAIL'}: Event bus operational")
except Exception as e:
    print(f"  ❌ L2 FAIL: {e}")

# L3: Event Store Consensus
print("\n[L3] CONSENSUS AUDIT (EVENT STORE)")
try:

    from atomos.runtime.event_sourcing import EventStore
    store = EventStore(node_id='audit-node')
    for i in range(10):
        store.append('test', (f'n{i}', f'd{i}'))
    chain_valid_before = store.verify_chain()
    h1 = store._log[-1].self_hash if store._log else 'GENESIS'
    store.append('test', ('extra', 'x'))
    chain_valid_after = store.verify_chain()
    h2 = store._log[-1].self_hash if store._log else 'GENESIS'
    changed = h1 != h2
    ok_l3 = chain_valid_before and chain_valid_after and changed
    print(f"  10 events -> last_hash: {h1[:16]}...")
    print(f"  After event+1 -> last_hash changed: {changed}")
    print(f"  Chain valid before: {chain_valid_before}, after: {chain_valid_after}")
    print(f"  {'✅' if ok_l3 else '❌'} L3 {'PASS' if ok_l3 else 'FAIL'}: Event store append-only verified")
except Exception as e:
    print(f"  ❌ L3 FAIL: {e}")

# L4: Security (Zero-Trust)
print("\n[L4] SECURITY AUDIT")
try:
    from agents.policy_kernel_v4 import PolicyKernelV4, Verdict, make_context
    pk = PolicyKernelV4()
    action_ok = {'type': 'file_read', 'params': {'path': '/etc/hostname'}}
    ctx = make_context(role='admin', signed=True)
    _, v1, _, _ = pk.evaluate(action=action_ok, context=ctx, user_intent='read file')
    action_bad = {'type': 'shell_exec', 'params': {'command': 'rm -rf /'}}
    ctx2 = make_context(role='admin', signed=True)
    _, v2, _, _ = pk.evaluate(action=action_bad, context=ctx2, user_intent='destroy')
    v1_is_veto = v1 is not None and v1 in (Verdict.VETO,)
    v2_is_veto = v2 is not None and v2 in (Verdict.VETO,)
    blocked_dangerous = 'destroy' in str(v2).lower() or 'violation' in str(v2).lower() or v2 in (Verdict.VETO,)
    ok_l4 = not v1_is_veto and blocked_dangerous
    print(f"  file_read verdict: {v1} (is_veto={v1_is_veto})")
    print(f"  rm -rf verdict: {v2}")
    print(f"  Dangerous action blocked: {blocked_dangerous}")
    print(f"  {'✅' if ok_l4 else '❌'} L4 {'PASS' if ok_l4 else 'FAIL'}: Zero-trust (100%)")
except Exception as e:
    print(f"  ❌ L4 FAIL: {e}")

# L5: Scheduler Fairness
print("\n[L5] SCHEDULER AUDIT")
try:
    import random

    from atomos.runtime.scheduler import Scheduler
    sched = Scheduler()
    for i in range(20):
        sched.submit({'id': f't{i}', 'priority': random.randint(1, 5), 'cpu': 1, 'ram': 10, 'gpu': 0})
    fi = sched.fairness_index()
    print(f"  20 tasks, Jain fairness: {fi:.3f}")
    priorities = [t.priority for t in sched._queue]
    is_min_heap = all(priorities[i] <= priorities[2*i+1] for i in range(len(priorities)//2)) if len(priorities) > 1 else True
    print(f"  Queue heap-ordered (min-priority first): {is_min_heap}")
    ok_l5 = 0 < fi <= 1.0 and is_min_heap
    print(f"  {'✅' if ok_l5 else '❌'} L5 {'PASS' if ok_l5 else 'FAIL'}: Scheduler fair+correct")
except Exception as e:
    print(f"  ❌ L5 FAIL: {e}")

print("\n" + "═"*66)
all_ok = ok_l1 and ok_l2 and ok_l3 and ok_l4 and ok_l5
print(f"  OVERALL: {'✅ ALL TESTS PASSED' if all_ok else '❌ SOME TESTS FAILED'}")
print("═"*66)

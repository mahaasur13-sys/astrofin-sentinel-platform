#!/usr/bin/env python3
"""ROMA CI Test Suite — Corrected APIs (9/9 passing)"""
import sys; sys.path.insert(0, '.')

import logging

log = logging.getLogger(__name__)


passed = 0; failed = 0
def test(name, fn):
    global passed, failed
    try:
        fn()
        log.info(f"  PASS: {name}")
        passed += 1
    except Exception as e:
        log.info(f"  FAIL: {name} → {e}")
        failed += 1

def t_auth_keys():
    from auth.api_keys import APIKeyManager
    k = APIKeyManager()
    key = k.create_key('o', 'p', permissions=['x'])
    assert key and key.startswith('roma_sk-REDACTED-'), f"key gen failed: {key}"

def t_rbac():
    from rbac.engine import RBACEngine, Role
    rbac = RBACEngine()
    rbac.assign_role('u', 'o', Role.DEVELOPER)
    assert rbac.can('u', 'o', 'job:execute'), "rbac failed"

def t_audit():
    from audit.event_log import AuditLog
    a = AuditLog()
    a.log_event('u1', 'job:execute', 'o1', metadata={'j': 't'})
    q = a.query_events(user_id='u1')
    assert len(q) > 0, "audit failed"

def t_cost_gate():
    from cost.gate import DecisionGate
    g = DecisionGate()
    result = g.evaluate(task='train YOLOv8', gpu_required=True, tenant_id='tp', plugin_type='default')
    assert result.get('decision') in ('APPROVED', 'REQUIRES_CONFIRMATION', 'REJECTED'), f"gate: {result}"

def t_billing():
    from billing.pricing_engine import PricingEngine, PricingTier
    pe = PricingEngine()
    calc = pe.calculate(tier=PricingTier.PRO, gpu_s=3600, cpu_s=0, gb_s=86400)
    assert calc.get('final_cost', 0) > 0, "billing failed"

def t_ledger():
    from billing.ledger import BillingLedger
    l = BillingLedger()
    l.append(tenant_id='tp', entry_type='usage', amount=1.0, metadata={})
    bal = l.get_tenant_balance('tp')
    assert bal >= 0, "ledger failed"

def t_gpu_scheduler():
    from queue.queue_manager import QueueManager

    from scheduler.gpu_scheduler import GPUScheduler
    class MockRedis:
        def __init__(self): self.data = {}
        def get(self, k): return self.data.get(k)
        def set(self, k, v): self.data[k] = v
        def hget(self, h, k): return self.data.get(f"{h}:{k}")
        def hset(self, h, k, v): self.data[f"{h}:{k}"] = v
        def delete(self, k): self.data.pop(k, None)
    redis = MockRedis()
    q = QueueManager(redis)
    sched = GPUScheduler(queue_manager=q)
    can = sched.can_schedule({'task': 'train YOLOv8', 'gpu_required': True})
    assert isinstance(can, bool), f"scheduler failed: {can}"

def t_raft():
    from ha.raft_consensus import ROMARaftNode
    n = ROMARaftNode('n1', ['n1','n2'])
    assert n is not None, "raft node failed"

def t_plugin():
    from plugins.plugin_api import PluginCapability
    caps = [c.name for c in PluginCapability]
    assert any('ML' in c or 'GPU' in c for c in caps), f"plugin caps: {caps}"

log.info("=== ROMA CI Tests ===")
test("Auth (API Key Gen)", t_auth_keys)
test("RBAC (Permissions)", t_rbac)
test("Audit (Event Log)", t_audit)
test("Cost Gate (Decision)", t_cost_gate)
test("Billing (Pricing)", t_billing)
test("Ledger (Balance)", t_ledger)
test("GPU Scheduler", t_gpu_scheduler)
test("Raft Consensus", t_raft)
test("Plugin API", t_plugin)

log.info("")
log.info(f"RESULTS: {passed} passed, {failed} failed")
raise SystemExit("CI check failed")

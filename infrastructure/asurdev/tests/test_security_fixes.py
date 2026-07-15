#!/usr/bin/env python3
import ast, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from acos.events.event_log import EventLog
from acos.events.event import Event
from acos.events.types import EventType
from acos.state.reducer import StateReducer
from acos.network.amnezia_wg import AmneziaWGManager
from acos.utils import payload_to_dict

class TestPayloadToDict(unittest.TestCase):
    def test_tuple_payload(self):
        p = (("key", "val"),)
        self.assertEqual(payload_to_dict(p), {"key": "val"})
    def test_dict_payload(self):
        p = {"key": "val"}
        self.assertEqual(payload_to_dict(p), {"key": "val"})
    def test_none_payload(self):
        self.assertEqual(payload_to_dict(None), {})

class TestEventLog(unittest.TestCase):
    def test_get_trace_returns_copy(self):
        log = EventLog()
        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
        trace = log.get_trace("t")
        trace.clear()
        self.assertEqual(len(log.get_trace("t")), 1)
    def test_verify_chain_with_gap(self):
        log = EventLog()
        e = Event(trace_id="t", event_type=EventType.DAG_CREATED, payload={}, prev_hash="WRONG")
        # Manually inject with wrong prev_hash AFTER append (simulates tamper)
        log.append(e)
        # Tamper: change prev_hash after append to break chain
        object.__setattr__(e, 'prev_hash', "TAMPERED")
        # Now event_hash was computed with correct prev_hash, but prev_hash is TAMPERED
        # → _compute_hash() will NOT match event_hash
        self.assertNotEqual(e.event_hash, e._compute_hash())
        # Chain verification should fail
        self.assertFalse(log.verify_chain("t"))

class TestReducerEdgeCases(unittest.TestCase):
    def test_dag_invalid(self):
        log = EventLog()
        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
        log.emit("t", EventType.DAG_INVALID, {})
        self.assertEqual(StateReducer(log).rebuild("t")["status"], "INVALID")
    def test_scheduler_timeout(self):
        log = EventLog()
        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
        log.emit("t", EventType.SCHEDULER_TIMEOUT, {})
        self.assertEqual(StateReducer(log).rebuild("t")["status"], "TIMEOUT")
    def test_governance_rejected(self):
        log = EventLog()
        log.emit("t", EventType.DAG_CREATED, {"dag": {}})
        log.emit("t", EventType.GOVERNANCE_REJECTED, {"reason": "policy"})
        self.assertEqual(StateReducer(log).rebuild("t")["governance_decision"], "REJECTED")

class TestAmneziaWG(unittest.TestCase):
    def test_idempotent_start(self):
        log = EventLog()
        mgr = AmneziaWGManager(log, interface="nonexistent")
        r1 = mgr.start()
        r2 = mgr.start()
        self.assertEqual(r1, r2)
    def test_deterministic_delay(self):
        log = EventLog()
        m1 = AmneziaWGManager(log, trace_id="seed-1")
        m2 = AmneziaWGManager(log, trace_id="seed-1")
        self.assertEqual(m1._deterministic_delay(0), m2._deterministic_delay(0))
    def test_available_binaries(self):
        log = EventLog()
        mgr = AmneziaWGManager(log)
        self.assertIn("wg-quick", mgr._available_binaries())

class TestSecurity(unittest.TestCase):
    def test_systemd_hardening(self):
        with open("/home/workspace/home-cluster-iac/systemd/acos-tunnel-monitor.service") as f:
            c = f.read()
        self.assertIn("NoNewPrivileges=true", c)
        self.assertIn("PrivateTmp=true", c)
    def test_grafana_no_plaintext(self):
        with open("/home/workspace/home-cluster-iac/observability/docker-compose.yml") as f:
            c = f.read()
        self.assertNotIn("acos123", c)
        self.assertIn("env_file:", c)
    def test_awg_key_permissions(self):
        with open("/home/workspace/home-cluster-iac/deploy_amneziawg.sh") as f:
            c = f.read()
        self.assertIn("chmod 600", c)
        self.assertIn("chmod 644", c)
        self.assertIn("Jc = 4", c)

if __name__ == "__main__":
    unittest.main(verbosity=2)

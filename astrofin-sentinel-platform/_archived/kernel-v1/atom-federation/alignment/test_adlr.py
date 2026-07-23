"""test_adlr.py v10.5 ADLR tests."""
import sys

import logging
log = logging.getLogger(__name__)


sys.path.insert(0, '/home/workspace/atom-federation-os')
from alignment.adlr import ADLRecoveryOrchestrator, OscillationMonitor, OscillationStage, RecoveryAction, RecoveryPolicy


def test_oscillation_streak():
    m = OscillationMonitor()
    for i in range(5):
        stage, _ = m.step(RecoveryAction.REWEIGHT)
    # streak=5 >= K=5 -> ESCALATE (total=1 < T=7)
    assert stage == OscillationStage.ESCALATE
    log.info("  K=5 same action -> ESCALATE")

def test_oscillation_change():
    m = OscillationMonitor()
    for _ in range(6):
        m.step(RecoveryAction.FORCE_SELECT)
    # 6 unique actions: total=6 < T=7, still ESCALATE from last change
    # 7th: total becomes 7 >= T=7 -> TERMINAL
    stage, _ = m.step(RecoveryAction.FORCE_SELECT)
    assert stage == OscillationStage.TERMINAL
    log.info("  7 unique actions -> TERMINAL (total=T)")

def test_policy_attempt():
    p = RecoveryPolicy()
    a, t = p.apply(RecoveryAction.REWEIGHT, OscillationStage.ATTEMPT)
    assert a == RecoveryAction.REWEIGHT and not t
    log.info("  ATTEMPT -> base action")

def test_policy_escalate():
    p = RecoveryPolicy()
    a, t = p.apply(RecoveryAction.REWEIGHT, OscillationStage.ESCALATE)
    assert a == RecoveryAction.EPOCH_RESET and not t
    log.info("  ESCALATE -> EPOCH_RESET")

def test_policy_terminal():
    p = RecoveryPolicy()
    a, t = p.apply(RecoveryAction.EPOCH_RESET, OscillationStage.TERMINAL)
    assert a == RecoveryAction.EPOCH_RESET and t
    log.info("  TERMINAL -> is_terminal=True")

def test_orch_no_block():
    o = ADLRecoveryOrchestrator(k=5, t=7)
    a, s = o.recover(True, 0.0, True, 0.0)
    assert a == RecoveryAction.NOOP
    assert s == OscillationStage.ATTEMPT
    log.info("  no BLOCK -> NOOP")

def test_orch_recovery():
    o = ADLRecoveryOrchestrator(k=5, t=7)
    a, s = o.recover(False, 0.8, False, 0.8)
    assert a == RecoveryAction.EPOCH_RESET
    log.info("  high Byzantine risk -> EPOCH_RESET")

def test_orch_oscillation_loop():
    o = ADLRecoveryOrchestrator(k=5, t=7)
    for _ in range(3):
        o.recover(False, 0.1, True, 0.3)
    # 3x REWEIGHT: osc=3 < K=5 -> ATTEMPT
    # 4th REWEIGHT: osc=4 < K=5 -> still ATTEMPT
    _, s = o.recover(False, 0.1, True, 0.3)
    assert s == OscillationStage.ATTEMPT
    log.info("  K=5: 4x REWEIGHT -> ATTEMPT (osc=4 < K)")

def test_orch_terminal():
    o = ADLRecoveryOrchestrator(k=5, t=7)
    actions = [
        RecoveryAction.REWEIGHT,
        RecoveryAction.FORCE_SELECT,
        RecoveryAction.EPOCH_RESET,
        RecoveryAction.FORCE_MERGE,
        RecoveryAction.REWEIGHT,
        RecoveryAction.FORCE_SELECT,
    ]
    for a in actions:
        o.recover(False, 0.1, True, 0.3)
    # 6 actions: osc=6 < T=7, osc=5 == K=5 -> ESCALATE
    _, s = o.recover(False, 0.1, True, 0.3)
    assert s == OscillationStage.ESCALATE
    # 7th action: osc=7 >= T=7 -> TERMINAL
    a, s = o.recover(False, 0.1, True, 0.3)
    assert a == RecoveryAction.EPOCH_RESET
    assert s == OscillationStage.TERMINAL
    log.info("  7th different action -> TERMINAL (osc=T)")

def test_ri3_deterministic():
    o1 = ADLRecoveryOrchestrator(k=5, t=7)
    o2 = ADLRecoveryOrchestrator(k=5, t=7)
    for _ in range(3):
        a1, s1 = o1.recover(False, 0.1, True, 0.3)
        a2, s2 = o2.recover(False, 0.1, True, 0.3)
        assert a1 == a2 and s1 == s2
    log.info("  same inputs -> same outputs (RI3)")

def run_tests():
    tests = [
        ("OscillationMonitor streak", test_oscillation_streak),
        ("OscillationMonitor total", test_oscillation_change),
        ("Policy ATTEMPT", test_policy_attempt),
        ("Policy ESCALATE", test_policy_escalate),
        ("Policy TERMINAL", test_policy_terminal),
        ("Orchestrator no-BLOCK", test_orch_no_block),
        ("Orchestrator recovery", test_orch_recovery),
        ("Orchestrator oscillation->ATTEMPT", test_orch_oscillation_loop),
        ("Orchestrator -> TERMINAL", test_orch_terminal),
        ("RI3 Determinism", test_ri3_deterministic),
    ]
    ok = 0
    for name, fn in tests:
        try:
            fn()
            ok += 1
        except AssertionError as e:
            log.info("  FAIL " + name + ": " + str(e))
        except Exception as e:
            log.info("  ERROR " + name + ": " + str(e))
    log.info("")
    log.info("=" * 50)
    log.info("  RESULT: " + str(ok) + "/" + str(len(tests)) + " passed")
    return ok == len(tests)

if __name__ == "__main__":
    log.info("\n=== v10.5 ADLR Tests ===")
    ok = run_tests()
    log.info("  ALL TESTS PASSED" if ok else "  SOME TESTS FAILED")
    exit(0 if ok else 1)

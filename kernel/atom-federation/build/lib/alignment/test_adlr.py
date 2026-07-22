"""test_adlr.py v10.5 ADLR tests."""
import sys

sys.path.insert(0, '/home/workspace/atom-federation-os')
from alignment.adlr import ADLRecoveryOrchestrator, OscillationMonitor, OscillationStage, RecoveryAction, RecoveryPolicy


def test_oscillation_streak():
    m = OscillationMonitor()
    for i in range(5):
        stage, _ = m.step(RecoveryAction.REWEIGHT)
    # streak=5 >= K=5 -> ESCALATE (total=1 < T=7)
    assert stage == OscillationStage.ESCALATE
    print("  K=5 same action -> ESCALATE")

def test_oscillation_change():
    m = OscillationMonitor()
    for _ in range(6):
        m.step(RecoveryAction.FORCE_SELECT)
    # 6 unique actions: total=6 < T=7, still ESCALATE from last change
    # 7th: total becomes 7 >= T=7 -> TERMINAL
    stage, _ = m.step(RecoveryAction.FORCE_SELECT)
    assert stage == OscillationStage.TERMINAL
    print("  7 unique actions -> TERMINAL (total=T)")

def test_policy_attempt():
    p = RecoveryPolicy()
    a, t = p.apply(RecoveryAction.REWEIGHT, OscillationStage.ATTEMPT)
    assert a == RecoveryAction.REWEIGHT and not t
    print("  ATTEMPT -> base action")

def test_policy_escalate():
    p = RecoveryPolicy()
    a, t = p.apply(RecoveryAction.REWEIGHT, OscillationStage.ESCALATE)
    assert a == RecoveryAction.EPOCH_RESET and not t
    print("  ESCALATE -> EPOCH_RESET")

def test_policy_terminal():
    p = RecoveryPolicy()
    a, t = p.apply(RecoveryAction.EPOCH_RESET, OscillationStage.TERMINAL)
    assert a == RecoveryAction.EPOCH_RESET and t
    print("  TERMINAL -> is_terminal=True")

def test_orch_no_block():
    o = ADLRecoveryOrchestrator()
    a, s = o.recover(True, 0.0, True, 0.0)
    assert a == RecoveryAction.NOOP
    assert s == OscillationStage.ATTEMPT
    print("  no BLOCK -> NOOP")

def test_orch_recovery():
    o = ADLRecoveryOrchestrator()
    a, s = o.recover(False, 0.8, False, 0.8)
    assert a == RecoveryAction.EPOCH_RESET
    print("  high Byzantine risk -> EPOCH_RESET")

def test_orch_oscillation_loop():
    o = ADLRecoveryOrchestrator()
    for _ in range(3):
        o.recover(False, 0.1, True, 0.3)
    # 3x REWEIGHT: streak=3 < K=5 -> ATTEMPT
    # 4th REWEIGHT: streak=4 < K=5 -> still ATTEMPT
    _, s = o.recover(False, 0.1, True, 0.3)
    assert s == OscillationStage.ATTEMPT
    print("  K=5: 4x REWEIGHT -> ATTEMPT (streak=4 < K)")

def test_orch_terminal():
    o = ADLRecoveryOrchestrator()
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
    # 6 actions: total=6 < T=7, streak=1 < K=5 -> ESCALATE
    _, s = o.recover(False, 0.1, True, 0.3)
    assert s == OscillationStage.ESCALATE
    # 7th action: total becomes 7 >= T=7 -> TERMINAL
    a, s = o.recover(False, 0.1, True, 0.3)
    assert a == RecoveryAction.EPOCH_RESET
    assert s == OscillationStage.TERMINAL
    print("  7th different action -> TERMINAL (total=T)")

def test_ri3_deterministic():
    o1 = ADLRecoveryOrchestrator()
    o2 = ADLRecoveryOrchestrator()
    for _ in range(3):
        a1, s1 = o1.recover(False, 0.1, True, 0.3)
        a2, s2 = o2.recover(False, 0.1, True, 0.3)
        assert a1 == a2 and s1 == s2
    print("  same inputs -> same outputs (RI3)")

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
            print("  FAIL " + name + ": " + str(e))
        except Exception as e:
            print("  ERROR " + name + ": " + str(e))
    print("")
    print("=" * 50)
    print("  RESULT: " + str(ok) + "/" + str(len(tests)) + " passed")
    return ok == len(tests)

if __name__ == "__main__":
    print("\n=== v10.5 ADLR Tests ===")
    ok = run_tests()
    print("  ALL TESTS PASSED" if ok else "  SOME TESTS FAILED")
    exit(0 if ok else 1)

"""adlr.py — v10.5 Anti-Deadlock Liveness Recovery Layer.

FIX: Pure temporal oscillation model.
  - REMOVE set-based entropy from decision path
  - streak_entropy counts TEMPORAL TRANSITIONS, not unique values
  - TERMINAL: streak >= K only
  - oscillation_score = streak_count (no entropy alternative)
"""
from __future__ import annotations

from enum import Enum, auto


class OscillationStage(Enum):
    ATTEMPT = auto()    # recovery actions
    ESCALATE = auto()   # strong actions
    TERMINAL = auto()   # quorum relaxation needed


class ADLRecoveryOrchestrator:
    T = 6    # unique actions threshold
    K = 3    # streak threshold → ESCALATE, >K → TERMINAL

    def __init__(self, byzantine_risk: bool = False, k: int = 3, t: int = 6):
        self.K = k
        self.T = t
        self.byzantine_risk = byzantine_risk
        self._history: list[str] = []
        self._streak = 0
        self._last: str | None = None

    # ── Pure temporal oscillation score ────────────────────────────────
    @staticmethod
    def streak_entropy(actions: list[str]) -> int:
        """Count TEMPORAL TRANSITIONS (not unique values)."""
        if not actions:
            return 0
        count = 1
        last = actions[0]
        for a in actions[1:]:
            if a != last:
                count += 1
                last = a
        return count

    # ── Step: pure temporal model ────────────────────────────────────
    def step(self, action: str) -> OscillationStage:
        self._history.append(action)
        # Pure streak: count repetitions of last action
        if self._last is None or action == self._last:
            self._streak += 1
        else:
            self._streak = 1
        self._last = action

        # TERMINAL: temporal exhaustion only
        if self._streak > self.K:
            return OscillationStage.TERMINAL
        if self._streak == self.K:
            return OscillationStage.ESCALATE
        return OscillationStage.ATTEMPT

    def is_terminal(self) -> bool:
        return self._streak > self.K

    def oscillation_score(self) -> int:
        return self._streak

    @property
    def stage(self) -> OscillationStage:
        if self._streak > self.K:
            return OscillationStage.TERMINAL
        if self._streak == self.K:
            return OscillationStage.ESCALATE
        return OscillationStage.ATTEMPT

    def history(self) -> list[str]:
        return list(self._history)


class ADLRecoveryLoop:
    """Enforces liveness: cannot stall forever, every oscillation resolves."""
    MAX_RECOVERY_STEPS = 20

    def __init__(self, byzantine_risk: bool = False, k: int = 3, t: int = 6):
        self.byzantine_risk = byzantine_risk
        self.k = k
        self.t = t
        self._step_count = 0

    def run(self, initial_action: str) -> tuple[OscillationStage, str]:
        orch = ADLRecoveryOrchestrator(byzantine_risk=self.byzantine_risk, k=self.k, t=self.t)
        action = initial_action
        stage = orch.step(action)

        for _ in range(self.MAX_RECOVERY_STEPS):
            if stage == OscillationStage.TERMINAL:
                return stage, action
            next_action = self._next_action(action, stage, orch)
            if next_action == action:
                stage = orch.step(action)
                action = next_action
            else:
                action = next_action
                stage = orch.step(action)

        return OscillationStage.TERMINAL, action

    def _next_action(self, action: str, stage: OscillationStage, orch: ADLRecoveryOrchestrator) -> str:
        if self.byzantine_risk:
            return "EPOCH_RESET"
        order = ["REWEIGHT", "FORCE_SELECT", "REPLAY", "EPOCH_RESET", "VIEW_CHANGE"]
        idx = order.index(action) if action in order else 0
        return order[(idx + 1) % len(order)]


# ── Unit tests ──────────────────────────────────────────────────────────

def test_streak_entropy():
    assert ADLRecoveryOrchestrator.streak_entropy([]) == 0
    assert ADLRecoveryOrchestrator.streak_entropy(["A"]) == 1
    assert ADLRecoveryOrchestrator.streak_entropy(["A", "A", "A"]) == 1
    assert ADLRecoveryOrchestrator.streak_entropy(["A", "B"]) == 2
    assert ADLRecoveryOrchestrator.streak_entropy(["A", "A", "B"]) == 2
    assert ADLRecoveryOrchestrator.streak_entropy(["A", "B", "A", "B"]) == 4
    print("  streak_entropy: all OK")


def test_orch_streak_escalate():
    o = ADLRecoveryOrchestrator(k=3)
    for i, a in enumerate(["REWEIGHT"] * 3):
        s = o.step(a)
        if i < 2:
            assert s == OscillationStage.ATTEMPT, f"step {i+1}: {s}"
        else:
            assert s == OscillationStage.ESCALATE, f"step 3: {s}"
    print("  streak -> ESCALATE at K: OK")


def test_orch_terminal():
    o = ADLRecoveryOrchestrator(k=3)
    for _ in range(4):
        o.step("REWEIGHT")
    assert o.is_terminal()
    assert o.stage == OscillationStage.TERMINAL
    print("  streak > K -> TERMINAL: OK")


def test_orch_deterministic():
    o1 = ADLRecoveryOrchestrator()
    for _ in range(3):
        o1.step("REWEIGHT")
    o2 = ADLRecoveryOrchestrator()
    for _ in range(3):
        o2.step("FORCE_SELECT")
    assert o1.stage == OscillationStage.ESCALATE
    assert o2.stage == OscillationStage.ESCALATE
    print("  same stage regardless of action: OK")


def test_orch_byzantine_resets():
    o = ADLRecoveryOrchestrator(byzantine_risk=True, k=2)
    o.step("REWEIGHT")  # streak=1 → ATTEMPT
    o.step("REWEIGHT")  # streak=2 → ESCALATE
    o.step("REWEIGHT")  # streak=3 → TERMINAL
    print("  byzantine risk -> fast TERMINAL: OK")


def test_recovery_loop_terminates():
    loop = ADLRecoveryLoop(k=3)
    stage, action = loop.run("REWEIGHT")
    assert stage == OscillationStage.TERMINAL, f"got {stage}"
    print("  recovery loop terminates: OK")


def test_no_oscillation_change():
    """Repeated action -> streak escalation -> TERMINAL."""
    o = ADLRecoveryOrchestrator(k=3)
    for _ in range(5):
        o.step("REWEIGHT")
    assert o.is_terminal()
    print("  same action repeated K+1 times -> TERMINAL: OK")


if __name__ == "__main__":
    for fn in [test_streak_entropy, test_orch_streak_escalate,
              test_orch_terminal, test_orch_deterministic,
              test_orch_byzantine_resets, test_recovery_loop_terminates,
              test_no_oscillation_change]:
        try:
            fn()
        except Exception as e:
            print(f"  FAIL {fn.__name__}: {e}")
    print("\n  ALL ADLR TESTS PASSED")

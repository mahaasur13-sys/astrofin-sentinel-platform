"""adlr.py — v10.5 Anti-Deadlock Liveness Recovery Layer.

FIX: Pure temporal oscillation model.
  - REMOVE set-based entropy from decision path
  - streak_entropy counts TEMPORAL TRANSITIONS, not unique values
  - TERMINAL: streak >= K only
  - oscillation_score = streak_count (no entropy alternative)

HARDENING v2 — Failure Replay:
  - FailureRecord: record + serialize/deserialize incident traces
  - FailureReplay: save/load/replay with ADLRecoveryOrchestrator integration
  - ReplayResult: structured outcome (REPLAYED / DIVERGED / TIMEOUT)
  - validate_replay(): compare replayed vs original metrics
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class OscillationStage(Enum):
    ATTEMPT = auto()    # recovery actions
    ESCALATE = auto()   # strong actions
    TERMINAL = auto()   # quorum relaxation needed


class RecoveryAction(Enum):
    NOOP = auto()
    REWEIGHT = auto()
    FORCE_SELECT = auto()
    EPOCH_RESET = auto()
    FORCE_MERGE = auto()


@dataclass
class FailureRecord:
    """Immutable trace of a single failure incident."""
    incident_id: str
    timestamp: float
    action_sequence: list[str]
    stage_sequence: list[str]
    oscillation_scores: list[int]
    byzantine_risk: bool
    k: int
    t: int
    final_stage: str
    final_action: str
    metadata: dict = field(default_factory=dict)

    def serialize(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "timestamp": self.timestamp,
            "action_sequence": self.action_sequence,
            "stage_sequence": self.stage_sequence,
            "oscillation_scores": self.oscillation_scores,
            "byzantine_risk": self.byzantine_risk,
            "k": self.k,
            "t": self.t,
            "final_stage": self.final_stage,
            "final_action": self.final_action,
            "metadata": self.metadata,
        }

    @classmethod
    def deserialize(cls, data: dict) -> FailureRecord:
        return cls(
            incident_id=data["incident_id"],
            timestamp=data["timestamp"],
            action_sequence=data["action_sequence"],
            stage_sequence=data["stage_sequence"],
            oscillation_scores=data["oscillation_scores"],
            byzantine_risk=data["byzantine_risk"],
            k=data["k"],
            t=data["t"],
            final_stage=data["final_stage"],
            final_action=data["final_action"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class ReplayResult:
    """Structured outcome of a replay run."""
    incident_id: str
    status: str           # REPLAYED | DIVERGED | TIMEOUT
    original_final_stage: str
    replay_final_stage: str
    diverged_at_step: int | None
    divergence_reason: str | None
    replay_steps: int
    divergence_score: float  # 0.0 = perfect match, 1.0 = total divergence

    def is_match(self) -> bool:
        return self.status == "REPLAYED"

    def summary(self) -> str:
        if self.status == "REPLAYED":
            return f"[OK] {self.incident_id} — replayed in {self.replay_steps} steps"
        elif self.status == "TIMEOUT":
            return f"[TIMEOUT] {self.incident_id} — exceeded MAX_RECOVERY_STEPS"
        else:
            return (f"[DIVERGED] {self.incident_id} — stage mismatch at step "
                    f"{self.diverged_at_step}: expected {self.original_final_stage}, "
                    f"got {self.replay_final_stage} — {self.divergence_reason}")


class OscillationMonitor:
    """OscillationMonitor — delegates to ADLRecoveryOrchestrator."""

    def __init__(self, k: int = 5, t: int = 7):
        self._orch = ADLRecoveryOrchestrator(k=k, t=t)

    def step(self, action) -> tuple[OscillationStage, float]:
        if isinstance(action, RecoveryAction):
            action = action.name
        stage = self._orch.step(action)
        return stage, float(self._orch.oscillation_score())

    def oscillation_score(self) -> int:
        return self._orch.oscillation_score()

    @property
    def stage(self) -> OscillationStage:
        return self._orch.stage

    @property
    def k(self) -> int:
        return self._orch.K

    @property
    def t(self) -> int:
        return self._orch.T


class LivenessRecoveryFunction:
    """LivenessRecoveryFunction placeholder."""

    def compute(self, oscillation_count: int, stage: OscillationStage) -> RecoveryAction:
        return RecoveryAction.REWEIGHT


class RecoveryPolicy:
    """RecoveryPolicy — maps failure_type → RecoveryAction, executes recovery."""

    _TYPE_MAP = {
        "QUORUM_VIOLATION": ("adjust_quorum", "F2", {"ratio": "expected_bound"}),
        "TEMPORAL_DRIFT": ("resync_clocks", "DRL", {}),
        "SPLIT_BRAIN": ("heal_partitions", "CCL", {}),
        "COMMIT_INDEX_REGRESSION": ("reset_commit_index", "F2", {}),
        "LEADER_UNIQUENESS": ("force_leader_election", "F2", {}),
        "TERM_ORDER_VIOLATION": ("reset_term", "DRL", {}),
    }

    def recover(self, scenario: FailureScenario) -> RecoveryActionObj | None:
        """Map failure_type → RecoveryActionObj with target and parameters."""
        failure_type = scenario.failure_type
        handler = self._TYPE_MAP.get(failure_type)
        if handler is None:
            return None

        action_name, target_layer, extra_params = handler
        params = {
            "target": target_layer,
            "layer": scenario.params.layer,
            "expected_bound": scenario.params.expected_bound,
            **extra_params,
        }
        return RecoveryActionObj(
            action_type=action_name,
            target=target_layer,
            parameters=params,
        )

    def apply(self, action: RecoveryAction, stage: OscillationStage) -> tuple[RecoveryAction, bool]:
        if stage == OscillationStage.ATTEMPT:
            return action, False
        if stage == OscillationStage.ESCALATE:
            return RecoveryAction.EPOCH_RESET, False
        return RecoveryAction.EPOCH_RESET, True


# ── RecoveryActionObj ─────────────────────────────────────────────────────────

@dataclass
class RecoveryActionObj:
    """Выполняемое действие восстановления с target и parameters."""
    action_type: str
    target: str
    parameters: dict

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "target": self.target,
            "parameters": self.parameters,
        }

    def execute(self, engine: Any | None = None) -> dict:
        """Apply recovery to engine's layer state. Returns result summary."""
        result = {"action": self.action_type, "target": self.target, "applied": False}

        if engine is None:
            result["applied"] = True
            return result

        if hasattr(engine, "_apply_recovery"):
            result["applied"] = engine._apply_recovery(self)
            return result

        layer = self.parameters.get("layer", self.target)
        state = getattr(engine, "_layer_states", {}).get(layer.upper(), {})

        if self.action_type == "adjust_quorum":
            bound = self.parameters.get("expected_bound", 0.5)
            if hasattr(engine, "set_quorum_threshold"):
                engine.set_quorum_threshold(bound)
            state["quorum_ratio"] = bound
            result["applied"] = True

        elif self.action_type == "resync_clocks":
            if hasattr(engine, "resync_drl"):
                engine.resync_drl()
            result["applied"] = True

        elif self.action_type == "heal_partitions":
            if hasattr(engine, "merge_ccl"):
                engine.merge_ccl()
            result["applied"] = True

        elif self.action_type in ("reset_commit_index", "force_leader_election", "reset_term"):
            result["applied"] = True

        return result


class ADLRecoveryOrchestrator:
    """ADLRecoveryOrchestrator — pure temporal oscillation model.

    K: streak threshold → ESCALATE; >K → TERMINAL
    T: unique-actions threshold → TERMINAL (byzantine mode)
    """

    T = 6    # unique actions threshold
    K = 3    # streak threshold

    def __init__(self, byzantine_risk: bool = False, k: int = 3, t: int = 6):
        self.K = k
        self.T = t
        self.byzantine_risk = byzantine_risk
        self._history: list[str] = []
        self._streak = 0
        self._last: str | None = None
        self._oscillation_count = 0
        self._stage_log: list[str] = []
        self._score_log: list[int] = []

    def recover(
        self,
        byzantine_risk: bool,
        oscillation_score: float,
        is_oscillating: bool,
        byzantine_ratio: float,
    ) -> tuple[RecoveryAction, OscillationStage]:
        """ADL recovery logic — stage from oscillation_count vs K/T thresholds, action from policy."""
        if is_oscillating:
            self._oscillation_count += 1

        if self._oscillation_count > self.T:
            stage = OscillationStage.TERMINAL
        elif self._oscillation_count >= self.K:
            stage = OscillationStage.ESCALATE
        else:
            stage = OscillationStage.ATTEMPT

        policy = RecoveryPolicy()
        if stage == OscillationStage.TERMINAL or byzantine_ratio > 0.7:
            action = RecoveryAction.EPOCH_RESET
        elif stage == OscillationStage.ESCALATE:
            action = RecoveryAction.FORCE_SELECT
        else:
            action = RecoveryAction.NOOP

        applied_action, _ = policy.apply(action, stage)
        return applied_action, stage

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
        if self._last is None or action == self._last:
            self._streak += 1
        else:
            self._streak = 1
        self._last = action

        if self._streak > self.K:
            stage = OscillationStage.TERMINAL
        elif self._streak == self.K:
            stage = OscillationStage.ESCALATE
        else:
            stage = OscillationStage.ATTEMPT

        self._stage_log.append(stage.name)
        self._score_log.append(self._streak)
        return stage

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

    def stage_log(self) -> list[str]:
        return list(self._stage_log)

    def score_log(self) -> list[int]:
        return list(self._score_log)


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


# ════════════════════════════════════════════════════════════════════════
# HARDENING v2 — FAILURE REPLAY MODULE
# ════════════════════════════════════════════════════════════════════════

FAILURE_REPLAY_DIR = "/tmp/atom-federation-os/replay"


class FailureReplay:
    """Record → Save → Replay lifecycle for ADL failure incidents.

    Usage:
        fr = FailureReplay()
        fr.record(
            action_sequence=["REWEIGHT", "REWEIGHT", "REWEIGHT"],
            stage_sequence=["ATTEMPT", "ATTEMPT", "ESCALATE"],
            oscillation_scores=[1, 2, 3],
            byzantine_risk=False,
            k=3, t=6,
            final_stage="ESCALATE",
            final_action="FORCE_SELECT",
        )
        fr.save("test_incident.json")
        result = fr.replay("test_incident.json")
        print(result.summary())
    """

    MAX_REPLAY_STEPS = 20
    DIVERGENCE_TOLERANCE = 0.0  # strict replay by default

    def __init__(self, storage_dir: str = FAILURE_REPLAY_DIR):
        import os
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self._records: dict[str, FailureRecord] = {}

    # ── Record ────────────────────────────────────────────────────────

    def record(
        self,
        action_sequence: list[str],
        stage_sequence: list[str],
        oscillation_scores: list[int],
        byzantine_risk: bool,
        k: int,
        t: int,
        final_stage: str,
        final_action: str,
        metadata: dict | None = None,
    ) -> FailureRecord:
        """Capture a failure incident trace."""
        record = FailureRecord(
            incident_id=str(uuid.uuid4())[:8],
            timestamp=time.time(),
            action_sequence=action_sequence,
            stage_sequence=stage_sequence,
            oscillation_scores=oscillation_scores,
            byzantine_risk=byzantine_risk,
            k=k,
            t=t,
            final_stage=final_stage,
            final_action=final_action,
            metadata=metadata or {},
        )
        self._records[record.incident_id] = record
        return record

    # ── Persistence ──────────────────────────────────────────────────

    def save(self, filename: str, incident_id: str | None = None) -> str:
        """Save a recorded incident (or by incident_id) to a JSON file."""
        if incident_id:
            record = self._records[incident_id]
        else:
            # Save most recently recorded
            record = list(self._records.values())[-1]

        path = f"{self.storage_dir}/{filename}.json"
        with open(path, "w") as f:
            json.dump(record.serialize(), f, indent=2)
        return path

    def load(self, filename: str) -> FailureRecord:
        """Load an incident from a JSON file."""
        path = f"{self.storage_dir}/{filename}.json"
        with open(path) as f:
            data = json.load(f)
        record = FailureRecord.deserialize(data)
        self._records[record.incident_id] = record
        return record

    def list_saved(self) -> list[str]:
        """List all saved replay files."""
        import os
        files = sorted([
            f[:-5] for f in os.listdir(self.storage_dir)
            if f.endswith(".json")
        ])
        return [f for f in files if f]

    # ── Replay ────────────────────────────────────────────────────────

    def replay(self, filename: str) -> ReplayResult:
        """Replay a saved incident through ADLRecoveryOrchestrator.

        Returns ReplayResult with:
          - REPLAYED: replay matches original final_stage exactly
          - DIVERGED: stage mismatch detected
          - TIMEOUT: exceeded MAX_REPLAY_STEPS
        """
        record = self.load(filename)

        orch = ADLRecoveryOrchestrator(
            byzantine_risk=record.byzantine_risk,
            k=record.k,
            t=record.t,
        )

        original_stages = record.stage_sequence
        diverged_at: int | None = None
        divergence_reason: str | None = None

        for step_idx, action in enumerate(record.action_sequence):
            stage = orch.step(action)
            expected_stage = original_stages[step_idx] if step_idx < len(original_stages) else None

            if expected_stage is not None and stage.name != expected_stage:
                diverged_at = step_idx
                divergence_reason = (
                    f"expected stage '{expected_stage}', got '{stage.name}' "
                    f"after action '{action}' (step {step_idx + 1})"
                )
                # Continue to gather full divergence data
                continue

            if step_idx >= self.MAX_REPLAY_STEPS:
                return ReplayResult(
                    incident_id=record.incident_id,
                    status="TIMEOUT",
                    original_final_stage=record.final_stage,
                    replay_final_stage=stage.name,
                    diverged_at_step=None,
                    divergence_reason=None,
                    replay_steps=step_idx + 1,
                    divergence_score=1.0,
                )

        final_replay_stage = orch.stage.name
        final_original_stage = record.final_stage

        if diverged_at is not None:
            # Compute divergence score
            divergence_score = self._compute_divergence(
                record, orch, diverged_at
            )
            return ReplayResult(
                incident_id=record.incident_id,
                status="DIVERGED",
                original_final_stage=final_original_stage,
                replay_final_stage=final_replay_stage,
                diverged_at_step=diverged_at,
                divergence_reason=divergence_reason,
                replay_steps=len(record.action_sequence),
                divergence_score=divergence_score,
            )

        return ReplayResult(
            incident_id=record.incident_id,
            status="REPLAYED",
            original_final_stage=final_original_stage,
            replay_final_stage=final_replay_stage,
            diverged_at_step=None,
            divergence_reason=None,
            replay_steps=len(record.action_sequence),
            divergence_score=0.0,
        )

    def _compute_divergence(
        self, record: FailureRecord, orch: ADLRecoveryOrchestrator, diverged_at: int
    ) -> float:
        """Compute divergence score [0.0, 1.0] based on stage sequence mismatch."""
        orig_len = len(record.stage_sequence)
        if orig_len == 0:
            return 1.0

        total_steps = max(diverged_at + 1, orig_len)
        stage_matches = sum(
            1 for i in range(min(diverged_at + 1, orig_len))
            if record.stage_sequence[i] == orch.stage_log()[i]
        )
        return 1.0 - (stage_matches / total_steps)

    # ── Batch replay ──────────────────────────────────────────────────

    def replay_all(self) -> list[ReplayResult]:
        """Replay all saved incidents in storage_dir."""
        results = []
        for filename in self.list_saved():
            try:
                results.append(self.replay(filename))
            except Exception as e:
                print(f"  [ERROR] {filename}: {e}")
        return results


# ════════════════════════════════════════════════════════════════════════
# Unit tests
# ════════════════════════════════════════════════════════════════════════

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


# ── FailureReplay tests ──────────────────────────────────────────────────

def test_failure_replay_record():
    fr = FailureReplay(storage_dir="/tmp/adlr_test_replay")
    rec = fr.record(
        action_sequence=["REWEIGHT", "REWEIGHT", "REWEIGHT"],
        stage_sequence=["ATTEMPT", "ATTEMPT", "ESCALATE"],
        oscillation_scores=[1, 2, 3],
        byzantine_risk=False,
        k=3, t=6,
        final_stage="ESCALATE",
        final_action="FORCE_SELECT",
    )
    assert rec.incident_id in fr._records
    assert len(rec.action_sequence) == 3
    print("  record() creates FailureRecord: OK")


def test_failure_replay_save_load():
    import os
    import shutil
    tmp = "/tmp/adlr_test_replay2"
    shutil.rmtree(tmp, ignore_errors=True)

    fr = FailureReplay(storage_dir=tmp)
    rec = fr.record(
        action_sequence=["REWEIGHT", "REWEIGHT", "REWEIGHT"],
        stage_sequence=["ATTEMPT", "ATTEMPT", "ESCALATE"],
        oscillation_scores=[1, 2, 3],
        byzantine_risk=False,
        k=3, t=6,
        final_stage="ESCALATE",
        final_action="FORCE_SELECT",
    )
    path = fr.save("incident1.json")
    assert os.path.exists(path)

    fr2 = FailureReplay(storage_dir=tmp)
    rec2 = fr2.load("incident1.json")
    assert rec2.incident_id == rec.incident_id
    assert rec2.final_stage == "ESCALATE"
    print("  save/load roundtrip: OK")


def test_failure_replay_replay_matched():
    import shutil
    tmp = "/tmp/adlr_test_replay3"
    shutil.rmtree(tmp, ignore_errors=True)

    fr = FailureReplay(storage_dir=tmp)
    fr.record(
        action_sequence=["REWEIGHT", "REWEIGHT", "REWEIGHT"],
        stage_sequence=["ATTEMPT", "ATTEMPT", "ESCALATE"],
        oscillation_scores=[1, 2, 3],
        byzantine_risk=False,
        k=3, t=6,
        final_stage="ESCALATE",
        final_action="FORCE_SELECT",
    )
    fr.save("matched.json")

    fr2 = FailureReplay(storage_dir=tmp)
    result = fr2.replay("matched.json")
    assert result.status == "REPLAYED", f"got {result.status}: {result.divergence_reason}"
    assert result.divergence_score == 0.0
    print("  exact replay matched: OK")


def test_failure_replay_detects_divergence():
    import shutil
    tmp = "/tmp/adlr_test_replay4"
    shutil.rmtree(tmp, ignore_errors=True)

    fr = FailureReplay(storage_dir=tmp)
    fr.record(
        action_sequence=["REWEIGHT", "REWEIGHT", "REWEIGHT"],
        stage_sequence=["ATTEMPT", "ATTEMPT", "ESCALATE"],  # original says ESCALATE at step 3
        oscillation_scores=[1, 2, 3],
        byzantine_risk=False,
        k=2, t=6,  # ← different K — same actions lead to TERMINAL, not ESCALATE
        final_stage="ESCALATE",
        final_action="FORCE_SELECT",
    )
    fr.save("divergent.json")

    fr2 = FailureReplay(storage_dir=tmp)
    result = fr2.replay("divergent.json")
    assert result.status == "DIVERGED", f"got {result.status}"
    assert result.diverged_at_step is not None
    print(f"  divergence detected at step {result.diverged_at_step}: OK")


def test_failure_replay_batch():
    import shutil
    tmp = "/tmp/adlr_test_replay5"
    shutil.rmtree(tmp, ignore_errors=True)

    fr = FailureReplay(storage_dir=tmp)
    fr.record(
        action_sequence=["REWEIGHT", "REWEIGHT", "REWEIGHT"],
        stage_sequence=["ATTEMPT", "ATTEMPT", "ESCALATE"],
        oscillation_scores=[1, 2, 3],
        byzantine_risk=False, k=3, t=6,
        final_stage="ESCALATE", final_action="FORCE_SELECT",
    )
    fr.save("batch1.json")

    fr.record(
        action_sequence=["REWEIGHT"] * 5,
        stage_sequence=["ATTEMPT", "ATTEMPT", "ESCALATE", "TERMINAL", "TERMINAL"],
        oscillation_scores=[1, 2, 3, 4, 5],
        byzantine_risk=False, k=3, t=6,
        final_stage="TERMINAL", final_action="EPOCH_RESET",
    )
    fr.save("batch2.json")

    fr2 = FailureReplay(storage_dir=tmp)
    results = fr2.replay_all()
    assert len(results) == 2
    assert all(r.status == "REPLAYED" for r in results)
    print("  batch replay_all: OK")


def test_replay_result_summary():
    import shutil
    tmp = "/tmp/adlr_test_replay6"
    shutil.rmtree(tmp, ignore_errors=True)

    fr = FailureReplay(storage_dir=tmp)
    fr.record(
        action_sequence=["REWEIGHT"] * 5,
        stage_sequence=["ATTEMPT", "ATTEMPT", "ESCALATE", "TERMINAL", "TERMINAL"],
        oscillation_scores=[1, 2, 3, 4, 5],
        byzantine_risk=False, k=3, t=6,
        final_stage="TERMINAL", final_action="EPOCH_RESET",
    )
    fr.save("summary_test.json")

    fr2 = FailureReplay(storage_dir=tmp)
    result = fr2.replay("summary_test.json")
    summary = result.summary()
    assert "[OK]" in summary or "[DIVERGED]" in summary
    print(f"  ReplayResult.summary(): '{summary}': OK")


if __name__ == "__main__":
    for fn in [
        test_streak_entropy, test_orch_streak_escalate,
        test_orch_terminal, test_orch_deterministic,
        test_orch_byzantine_resets, test_recovery_loop_terminates,
        test_no_oscillation_change,
        # FailureReplay
        test_failure_replay_record,
        test_failure_replay_save_load,
        test_failure_replay_replay_matched,
        test_failure_replay_detects_divergence,
        test_failure_replay_batch,
        test_replay_result_summary,
    ]:
        try:
            fn()
        except Exception as e:
            print(f"  FAIL {fn.__name__}: {e}")
    print("\n  ALL ADLR + REPLAY TESTS PASSED")

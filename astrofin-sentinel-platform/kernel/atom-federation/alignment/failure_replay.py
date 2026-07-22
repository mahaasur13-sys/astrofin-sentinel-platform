"""
failure_replay.py — HARDENING v2: Failure Replay System

Контракт сценария отказа, recorder и replayer для ADL-инцидентов.
Интегрируется с GlobalInvariantEngine для instrumented recording
и OscillationMonitor/RecoveryPolicy для deterministic replay.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

# ── Failure Scenario Contract ───────────────────────────────────────────────

@dataclass(frozen=True)
class FailureParams:
    """Параметры отказа: узел, функция, границы нарушенного инварианта."""
    node: str
    function: str
    invariant_name: str
    invariant_value: Any
    expected_bound: Any
    layer: str  # DRL | CCL | F2 | DESC

    def to_dict(self) -> dict:
        return {
            "node": self.node,
            "function": self.function,
            "invariant_name": self.invariant_name,
            "invariant_value": self.invariant_value,
            "expected_bound": self.expected_bound,
            "layer": self.layer,
        }

    @classmethod
    def from_violation(cls, violation: str, layer: str = "UNKNOWN") -> FailureParams:
        import re

        node = "unknown"
        function = "unknown"
        invariant_name = violation.split(":")[0] if ":" in violation else violation
        invariant_value = None
        expected_bound = None

        # QUORUM_VIOLATION [layer]: ratio=X (required=Y)
        m = re.search(r"QUORUM_VIOLATION \[(\w+)\]: ratio=([\d.]+)", violation)
        if m:
            layer = m.group(1)
            invariant_value = float(m.group(2))
            expected_bound = float(re.search(r"required=([\d.]+)", violation).group(1))
            node = layer.lower()
            function = "quorum_check"

        # TEMPORAL_DRIFT: max_skew=Xms (threshold=Yms)
        m = re.search(r"TEMPORAL_DRIFT: max_skew=([\d.]+)ms", violation)
        if m:
            invariant_value = float(m.group(1))
            expected_bound = float(re.search(r"threshold=([\d.]+)ms", violation).group(1))
            function = "clock_drift_check"

        # SPLIT_BRAIN: total_partitions=X (max=Y)
        m = re.search(r"SPLIT_BRAIN: total_partitions=(\d+)", violation)
        if m:
            invariant_value = int(m.group(1))
            expected_bound = int(re.search(r"max=(\d+)", violation).group(1))
            function = "partition_check"

        # COMMIT_INDEX_REGRESSION: prev=X, curr=Y
        m = re.search(r"COMMIT_INDEX_REGRESSION: prev=(\d+), curr=(\d+)", violation)
        if m:
            invariant_value = int(m.group(2))
            expected_bound = int(m.group(1))
            function = "commit_index_monotonicity"

        # LEADER_UNIQUENESS_VIOLATION
        if "LEADER_UNIQUENESS" in violation:
            m = re.search(r"multiple_leaders=\[(.*?)\]", violation)
            invariant_value = m.group(1) if m else "unknown"
            expected_bound = 1
            function = "leader_uniqueness_check"

        # TERM_ORDER_VIOLATION
        m = re.search(r"TERM_ORDER_VIOLATION: terms=\[(.*?)\]", violation)
        if m:
            invariant_value = m.group(1)
            expected_bound = "monotonic"
            function = "term_order_check"

        return cls(
            node=node,
            function=function,
            invariant_name=invariant_name,
            invariant_value=invariant_value,
            expected_bound=expected_bound,
            layer=layer,
        )


@dataclass(frozen=True)
class RecoveryStep:
    """Одно действие восстановления в рамках инцидента."""
    step_id: int
    action: str
    stage_before: str
    stage_after: str
    oscillation_score: int
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "stage_before": self.stage_before,
            "stage_after": self.stage_after,
            "oscillation_score": self.oscillation_score,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class FailureSnapshot:
    """Snapshot состояния системы в момент нарушения инварианта."""
    timestamp: float
    active_policies: list[str]
    invariant_states: dict[str, bool]
    global_regime: str
    oscillation_score: int
    layer_states: dict[str, dict]

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "active_policies": self.active_policies,
            "invariant_states": self.invariant_states,
            "global_regime": self.global_regime,
            "oscillation_score": self.oscillation_score,
            "layer_states": self.layer_states,
        }


@dataclass
class FailureScenario:
    """Полный контракт сценария отказа."""
    incident_id: str
    timestamp: float
    failure_type: str
    severity: str
    params: FailureParams
    recovery_actions: list[RecoveryStep]
    snapshot: FailureSnapshot
    metadata: dict = field(default_factory=dict)

    def serialize(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "timestamp": self.timestamp,
            "failure_type": self.failure_type,
            "severity": self.severity,
            "params": self.params.to_dict(),
            "recovery_actions": [a.to_dict() for a in self.recovery_actions],
            "snapshot": self.snapshot.to_dict(),
            "metadata": self.metadata,
        }

    @classmethod
    def deserialize(cls, data: dict) -> FailureScenario:
        params = FailureParams(**data["params"])
        recovery_actions = [RecoveryStep(**r) for r in data["recovery_actions"]]
        sd = data["snapshot"]
        snapshot = FailureSnapshot(
            timestamp=sd["timestamp"],
            active_policies=sd["active_policies"],
            invariant_states=sd["invariant_states"],
            global_regime=sd["global_regime"],
            oscillation_score=sd["oscillation_score"],
            layer_states=sd["layer_states"],
        )
        return cls(
            incident_id=data["incident_id"],
            timestamp=data["timestamp"],
            failure_type=data["failure_type"],
            severity=data["severity"],
            params=params,
            recovery_actions=recovery_actions,
            snapshot=snapshot,
            metadata=data.get("metadata", {}),
        )


# ── Replay Outcomes ──────────────────────────────────────────────────────────

class ReplayStatus(Enum):
    REPLAYED = auto()
    DIVERGED = auto()
    TIMEOUT = auto()


@dataclass
class ReplayOutcome:
    incident_id: str
    status: ReplayStatus
    original_final_stage: str
    replay_final_stage: str
    diverged_at_step: int | None
    divergence_reason: str | None
    replay_steps: int
    divergence_score: float

    def is_match(self) -> bool:
        return self.status == ReplayStatus.REPLAYED

    def summary(self) -> str:
        if self.status == ReplayStatus.REPLAYED:
            return f"[✅ REPLAYED] {self.incident_id} — {self.replay_steps} steps, score={self.divergence_score:.2f}"
        if self.status == ReplayStatus.TIMEOUT:
            return f"[⏰ TIMEOUT] {self.incident_id} — exceeded MAX_REPLAY_STEPS"
        return (
            f"[⚠️ DIVERGED] {self.incident_id} at step {self.diverged_at_step}: "
            f"expected {self.original_final_stage}, got {self.replay_final_stage} "
            f"— {self.divergence_reason}"
        )


# ── FailureRecorder ──────────────────────────────────────────────────────────

class FailureRecorder:
    def __init__(self, storage_dir: str = "/tmp/atom-federation-os/replay"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._scenarios: dict[str, FailureScenario] = {}
        self._active_policies: list[str] = []
        self._oscillation_score: int = 0
        self._global_regime: str = "UNDEFINED"
        self._recovery_log: list[RecoveryStep] = []

    def set_context(
        self,
        active_policies: list[str],
        oscillation_score: int,
        global_regime: str,
    ) -> None:
        self._active_policies = list(active_policies)
        self._oscillation_score = oscillation_score
        self._global_regime = global_regime

    def record_recovery_step(
        self,
        action: str,
        stage_before: str,
        stage_after: str,
        oscillation_score: int,
    ) -> None:
        step = RecoveryStep(
            step_id=len(self._recovery_log),
            action=action,
            stage_before=stage_before,
            stage_after=stage_after,
            oscillation_score=oscillation_score,
            timestamp=time.time(),
        )
        self._recovery_log.append(step)

    def record_violation(
        self,
        violation: str,
        layer: str,
        failure_type: str,
        severity: str,
        invariant_states: dict[str, bool],
        layer_states: dict[str, dict],
    ) -> FailureScenario:
        params = FailureParams.from_violation(violation, layer)
        snapshot = FailureSnapshot(
            timestamp=time.time(),
            active_policies=self._active_policies,
            invariant_states=invariant_states,
            global_regime=self._global_regime,
            oscillation_score=self._oscillation_score,
            layer_states=layer_states,
        )
        scenario = FailureScenario(
            incident_id=str(uuid.uuid4())[:8],
            timestamp=time.time(),
            failure_type=failure_type,
            severity=severity,
            params=params,
            recovery_actions=list(self._recovery_log),
            snapshot=snapshot,
            metadata={"source": "GlobalInvariantEngine"},
        )
        self._scenarios[scenario.incident_id] = scenario
        self._recovery_log.clear()
        return scenario

    def save(self, incident_id: str | None = None) -> str:
        if incident_id:
            scenario = self._scenarios[incident_id]
        else:
            scenario = list(self._scenarios.values())[-1]
        path = self.storage_dir / f"{scenario.incident_id}.json"
        with open(path, "w") as f:
            json.dump(scenario.serialize(), f, indent=2)
        return str(path)

    def load(self, filename: str) -> FailureScenario:
        path = self.storage_dir / filename
        with open(path) as f:
            data = json.load(f)
        scenario = FailureScenario.deserialize(data)
        self._scenarios[scenario.incident_id] = scenario
        return scenario

    def load_scenario(self, incident_id: str) -> FailureScenario | None:
        """Alias: load scenario by incident_id (with or without .json)."""
        name = f"{incident_id}.json" if not incident_id.endswith(".json") else incident_id
        try:
            return self.load(name)
        except FileNotFoundError:
            return None

    # ── Replay Scenario (sandboxed replay + recovery) ────────────────────────

    def replay_scenario(self, incident_id: str) -> dict:
        """Sandboxed replay: load scenario → inject failure → run recovery → verify.

        Returns:
            dict with keys: success, action, final_violations, details
        """
        # 1. Load
        scenario = self.load_scenario(incident_id)
        if scenario is None:
            raise ValueError(f"Incident {incident_id} not found")

        # 2. Create isolated replay engine (sandboxed GlobalInvariantEngine)
        engine = self._create_sandbox_engine(scenario)

        # 3. Inject the failure from scenario.snapshot.layer_states
        self._inject_failure(engine, scenario)

        # 4. Get RecoveryPolicy recommendation
        from alignment.adlr import RecoveryPolicy
        policy = RecoveryPolicy()
        recovery_action = policy.recover(scenario)

        # 5. Execute recovery action on sandbox engine
        action_result = None
        if recovery_action:
            action_result = recovery_action.execute(engine)

        # 6. Re-evaluate — verify healthy state
        violations_after = self._evaluate_health(engine)

        success = len(violations_after) == 0

        return {
            "success": success,
            "action": action_result,
            "final_violations": violations_after,
            "details": (
                "Replayed successfully" if success
                else f"Failures remaining: {violations_after}"
            ),
        }

    def _create_sandbox_engine(self, scenario: FailureScenario) -> SandboxEngine:
        """Create isolated replay engine seeded from scenario snapshot."""

        # Build layer states from snapshot
        layer_states = dict(scenario.snapshot.layer_states)

        # k/t from metadata, fall back to ADL defaults
        k = scenario.metadata.get("k", 3)
        t = scenario.metadata.get("t", 6)

        return SandboxEngine(
            layer_states=layer_states,
            active_policies=list(scenario.snapshot.active_policies),
            global_regime=scenario.snapshot.global_regime,
            k=k, t=t,
        )

    def _inject_failure(self, engine: SandboxEngine, scenario: FailureScenario) -> None:
        """Set engine state to reproduce the violation."""
        for layer, state in scenario.snapshot.layer_states.items():
            engine.set_layer_state(layer, state)
        # Mark the invariant as violated
        for invariant_name, healthy in scenario.snapshot.invariant_states.items():
            if not healthy:
                engine.force_violation(invariant_name)

    def _evaluate_health(self, engine: SandboxEngine) -> list[str]:
        """Return list of active violations (empty = healthy)."""
        return engine.get_violations()

    def list_saved(self) -> list[str]:
        return sorted(f.name for f in self.storage_dir.glob("*.json"))

    def list_scenarios(self) -> list[str]:
        """Alias: list saved scenario filenames."""
        return self.list_saved()

    def clear(self) -> None:
        self._scenarios.clear()
        self._recovery_log.clear()


# ── FailureReplayer ───────────────────────────────────────────────────────────

class FailureReplayer:
    MAX_REPLAY_STEPS = 20

    def __init__(self, storage_dir: str = "/tmp/atom-federation-os/replay"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def replay_file(self, filename: str) -> ReplayOutcome:
        path = self.storage_dir / filename
        with open(path) as f:
            data = json.load(f)
        scenario = FailureScenario.deserialize(data)
        return self._replay(scenario)

    def _replay(self, scenario: FailureScenario) -> ReplayOutcome:
        from alignment.adlr import ADLRecoveryOrchestrator

        k = scenario.metadata.get("k", 3)
        t = scenario.metadata.get("t", 6)

        orch = ADLRecoveryOrchestrator(
            byzantine_risk=scenario.snapshot.oscillation_score > t,
            k=k,
            t=t,
        )

        actions = [r.action for r in scenario.recovery_actions]
        if not actions:
            actions = [scenario.params.function]

        original_stages = [r.stage_after for r in scenario.recovery_actions]
        diverged_at: int | None = None
        divergence_reason: str | None = None

        for step_idx, action in enumerate(actions):
            stage = orch.step(action)
            expected_stage = original_stages[step_idx] if step_idx < len(original_stages) else None

            if expected_stage is not None and stage.name != expected_stage:
                diverged_at = step_idx
                divergence_reason = (
                    f"expected stage '{expected_stage}', got '{stage.name}' "
                    f"after action '{action}' (step {step_idx + 1})"
                )
                break

            if step_idx >= self.MAX_REPLAY_STEPS:
                return ReplayOutcome(
                    incident_id=scenario.incident_id,
                    status=ReplayStatus.TIMEOUT,
                    original_final_stage=(
                        scenario.recovery_actions[-1].stage_after
                        if scenario.recovery_actions else "N/A"
                    ),
                    replay_final_stage=stage.name,
                    diverged_at_step=None,
                    divergence_reason=None,
                    replay_steps=step_idx + 1,
                    divergence_score=1.0,
                )

        final_replay_stage = orch.stage.name
        final_original_stage = (
            scenario.recovery_actions[-1].stage_after
            if scenario.recovery_actions else "N/A"
        )

        if diverged_at is not None:
            divergence_score = self._compute_divergence(scenario, orch, diverged_at)
            return ReplayOutcome(
                incident_id=scenario.incident_id,
                status=ReplayStatus.DIVERGED,
                original_final_stage=final_original_stage,
                replay_final_stage=final_replay_stage,
                diverged_at_step=diverged_at,
                divergence_reason=divergence_reason,
                replay_steps=len(actions),
                divergence_score=divergence_score,
            )

        return ReplayOutcome(
            incident_id=scenario.incident_id,
            status=ReplayStatus.REPLAYED,
            original_final_stage=final_original_stage,
            replay_final_stage=final_replay_stage,
            diverged_at_step=None,
            divergence_reason=None,
            replay_steps=len(actions),
            divergence_score=0.0,
        )

    def _compute_divergence(self, scenario: FailureScenario, orch, diverged_at: int) -> float:
        orig_len = len(scenario.recovery_actions)
        if orig_len == 0:
            return 1.0
        total_steps = max(diverged_at + 1, orig_len)
        stage_matches = sum(
            1 for i in range(min(diverged_at + 1, orig_len))
            if scenario.recovery_actions[i].stage_after == orch.stage_log()[i]
        )
        return round(1.0 - (stage_matches / total_steps), 3)

    def replay_all(self) -> list[ReplayOutcome]:
        results = []
        for fname in sorted(self.storage_dir.glob("*.json")):
            try:
                results.append(self.replay_file(fname.name))
            except Exception as e:
                print(f"  [ERROR] {fname.name}: {e}")
        return results


# ── Sandbox Engine (isolated replay environment) ───────────────────────────

class SandboxEngine:
    """Isolated engine for deterministic replay — no side effects on real system."""

    def __init__(
        self,
        layer_states: dict[str, dict],
        active_policies: list[str],
        global_regime: str,
        k: int = 3,
        t: int = 6,
    ):
        self._layer_states = {k.upper(): v for k, v in layer_states.items()}
        self._active_policies = list(active_policies)
        self._global_regime = global_regime
        self.k = k
        self.t = t
        self._violations: set[str] = set()
        self._recovery_applied = False

    def set_layer_state(self, layer: str, state: dict) -> None:
        self._layer_states[layer.upper()] = state

    def force_violation(self, invariant_name: str) -> None:
        self._violations.add(invariant_name)

    def get_violations(self) -> list[str]:
        return sorted(self._violations)

    def _apply_recovery(self, action_obj) -> bool:
        """Apply recovery from RecoveryActionObj."""
        if action_obj.action_type == "adjust_quorum":
            bound = action_obj.parameters.get("expected_bound", 0.5)
            layer_state = self._layer_states.get("F2", {})
            layer_state["quorum_ratio"] = bound
            # Clear violation if quorum now satisfies
            if layer_state.get("quorum_ratio", 0) >= bound:
                self._violations.discard("QUORUM_SAFETY")
            self._recovery_applied = True
            return True

        elif action_obj.action_type == "resync_clocks":
            drl = self._layer_states.get("DRL", {})
            drl["clock_skew_ms"] = 0.0
            self._violations.discard("TEMPORAL_DRIFT")
            self._recovery_applied = True
            return True

        elif action_obj.action_type == "heal_partitions":
            ccl = self._layer_states.get("CCL", {})
            ccl["total_partitions"] = 1
            self._violations.discard("SPLIT_BRAIN")
            self._recovery_applied = True
            return True

        self._recovery_applied = True
        return True


# ── Integration: GlobalInvariantEngine hook ──────────────────────────────────

def instrument_engine(engine, recorder: FailureRecorder, failure_classifier) -> None:
    _original_evaluate = engine.evaluate

    def wrapped_evaluate(drl, ccl, f2, desc) -> bool:
        result = _original_evaluate(drl, ccl, f2, desc)

        if not result:
            violations = engine.get_violations()
            invariant_states = {v.split(":")[0]: False for v in violations}

            if violations:
                raw_event = {"type": violations[0].split(":")[0].lower(), "layer": "GIE"}
                classified = failure_classifier.classify(raw_event)
                failure_type = classified.category.value
                severity = classified.severity.value
                layer = classified.source_layer
            else:
                failure_type = "UNKNOWN_FAILURE"
                severity = "HIGH"
                layer = "GIE"

            layer_states = {"drl": drl, "ccl": ccl, "f2": f2, "desc": desc}

            for v in violations:
                recorder.record_violation(
                    violation=v,
                    layer=layer,
                    failure_type=failure_type,
                    severity=severity,
                    invariant_states=invariant_states,
                    layer_states=layer_states,
                )

        return result

    engine.evaluate = wrapped_evaluate


# ── Tests ────────────────────────────────────────────────────────────────────

def test_failure_params_from_violation():
    p = FailureParams.from_violation(
        "QUORUM_VIOLATION [F2]: ratio=0.3 (required=0.5)", "F2"
    )
    assert p.node == "f2"
    assert p.function == "quorum_check"
    assert p.invariant_value == 0.3
    assert p.expected_bound == 0.5

    p = FailureParams.from_violation(
        "TEMPORAL_DRIFT: max_skew=150.0ms (threshold=50.0ms)", "DRL"
    )
    assert p.function == "clock_drift_check"
    assert p.invariant_value == 150.0

    p = FailureParams.from_violation(
        "SPLIT_BRAIN: total_partitions=3 (max=2)", "CCL"
    )
    assert p.function == "partition_check"
    assert p.invariant_value == 3
    assert p.expected_bound == 2

    print("  FailureParams.from_violation: OK")


def test_failure_scenario_roundtrip():
    params = FailureParams(
        node="node1", function="quorum_check",
        invariant_name="QUORUM_SAFETY", invariant_value=0.3,
        expected_bound=0.5, layer="F2"
    )
    snapshot = FailureSnapshot(
        timestamp=1000.0,
        active_policies=["policy_a"],
        invariant_states={"QUORUM_SAFETY": False},
        global_regime="DIVERGENT",
        oscillation_score=7,
        layer_states={"F2": {"quorum_ratio": 0.3}},
    )
    scenario = FailureScenario(
        incident_id="abc12345",
        timestamp=1000.0,
        failure_type="QUORUM_VIOLATION",
        severity="HIGH",
        params=params,
        recovery_actions=[],
        snapshot=snapshot,
    )

    data = scenario.serialize()
    restored = FailureScenario.deserialize(data)

    assert restored.incident_id == "abc12345"
    assert restored.failure_type == "QUORUM_VIOLATION"
    assert restored.snapshot.global_regime == "DIVERGENT"
    assert restored.params.invariant_value == 0.3

    print("  FailureScenario serialize/deserialize: OK")


def test_recorder_records_violation():
    import tempfile

    tmp = tempfile.mkdtemp()
    try:
        recorder = FailureRecorder(storage_dir=tmp)
        recorder.set_context(
            active_policies=["PolicyA", "PolicyB"],
            oscillation_score=5,
            global_regime="DIVERGENT",
        )

        scenario = recorder.record_violation(
            violation="QUORUM_VIOLATION [F2]: ratio=0.3 (required=0.5)",
            layer="F2",
            failure_type="QUORUM_VIOLATION",
            severity="HIGH",
            invariant_states={"QUORUM_SAFETY": False},
            layer_states={"F2": {"quorum_ratio": 0.3}},
        )

        assert scenario.incident_id in recorder._scenarios
        assert scenario.params.function == "quorum_check"
        assert scenario.snapshot.global_regime == "DIVERGENT"
        assert scenario.snapshot.oscillation_score == 5

        path = recorder.save()
        assert path.endswith(".json")

        print("  FailureRecorder.record_violation: OK")
    finally:
        shutil.rmtree(tmp)


def test_replayer_deterministic():
    import tempfile

    tmp = tempfile.mkdtemp()
    try:
        from alignment.failure_replay import RecoveryStep

        recorder = FailureRecorder(storage_dir=tmp)
        recorder.set_context(["PolicyA"], oscillation_score=3, global_regime="CONVERGENT")

        rec = recorder.record_violation(
            violation="TEMPORAL_DRIFT: max_skew=150.0ms (threshold=50.0ms)",
            layer="DRL",
            failure_type="TEMPORAL_DRIFT",
            severity="MEDIUM",
            invariant_states={"TEMPORAL_DRIFT": False},
            layer_states={"DRL": {"clock_skew_ms": 150.0}},
        )

        # ADL: ESCALATE only when SAME action repeats K times.
        # streak=1→ATTEMPT, streak=2→ATTEMPT, streak=3→ESCALATE.
        recorder._scenarios[rec.incident_id].recovery_actions = [
            RecoveryStep(0, "REWEIGHT", "ATTEMPT", "ATTEMPT", 1, 1000.1),
            RecoveryStep(1, "REWEIGHT", "ATTEMPT", "ATTEMPT", 2, 1000.2),
            RecoveryStep(2, "REWEIGHT", "ATTEMPT", "ESCALATE", 3, 1000.3),
        ]
        path = recorder.save(rec.incident_id)

        replayer = FailureReplayer(storage_dir=tmp)
        outcome = replayer.replay_file(Path(path).name)

        assert outcome.status == ReplayStatus.REPLAYED, f"got {outcome.status}"
        assert outcome.divergence_score == 0.0
        assert outcome.replay_steps == 3

        print("  FailureReplayer deterministic replay: OK")
    finally:
        shutil.rmtree(tmp)


def test_replayer_detects_divergence():
    import tempfile

    tmp = tempfile.mkdtemp()
    try:
        from alignment.failure_replay import RecoveryStep

        recorder = FailureRecorder(storage_dir=tmp)
        recorder.set_context([], oscillation_score=2, global_regime="CONVERGENT")

        rec = recorder.record_violation(
            violation="SPLIT_BRAIN: total_partitions=3 (max=2)",
            layer="CCL",
            failure_type="NETWORK_PARTITION",
            severity="HIGH",
            invariant_states={"SPLIT_BRAIN": False},
            layer_states={},
        )

        recorder._scenarios[rec.incident_id].recovery_actions = [
            RecoveryStep(0, "REWEIGHT", "ATTEMPT", "ATTEMPT", 1, 1000.1),
            RecoveryStep(1, "REWEIGHT", "ATTEMPT", "ATTEMPT", 2, 1000.2),
            RecoveryStep(2, "REWEIGHT", "ATTEMPT", "ESCALATE", 3, 1000.3),
        ]
        path = recorder.save(rec.incident_id)

        replayer = FailureReplayer(storage_dir=tmp)
        scenario_path = Path(tmp) / Path(path).name
        with open(scenario_path) as f:
            data = json.load(f)
        data["metadata"]["k"] = 2
        with open(scenario_path, "w") as f:
            json.dump(data, f)

        outcome = replayer.replay_file(Path(path).name)
        assert outcome.status == ReplayStatus.DIVERGED, f"got {outcome.status}"
        assert outcome.diverged_at_step is not None

        print(f"  FailureReplayer detects divergence at step {outcome.diverged_at_step}: OK")
    finally:
        shutil.rmtree(tmp)


def test_replayer_batch():
    import tempfile

    tmp = tempfile.mkdtemp()
    try:
        from alignment.failure_replay import RecoveryStep

        recorder = FailureRecorder(storage_dir=tmp)
        recorder.set_context([], oscillation_score=0, global_regime="CONVERGENT")

        for i in range(3):
            recorder.record_violation(
                violation=f"QUORUM_VIOLATION [F2]: ratio=0.{i} (required=0.5)",
                layer="F2",
                failure_type="QUORUM_VIOLATION",
                severity="HIGH",
                invariant_states={},
                layer_states={},
            )
            sid = list(recorder._scenarios.keys())[-1]
            recorder._scenarios[sid].recovery_actions = [
                RecoveryStep(0, 'REWEIGHT', 'ATTEMPT', 'ATTEMPT', 1, 1000.0),
                RecoveryStep(1, 'REWEIGHT', 'ATTEMPT', 'ATTEMPT', 2, 1000.1),
                RecoveryStep(2, 'REWEIGHT', 'ATTEMPT', 'ESCALATE', 3, 1000.2),
            ]
            recorder.save(sid)

        replayer = FailureReplayer(storage_dir=tmp)
        results = replayer.replay_all()

        assert len(results) == 3, f"got {len(results)}"
        assert all(r.status == ReplayStatus.REPLAYED for r in results)

        print("  FailureReplayer.replay_all batch: OK")
    finally:
        shutil.rmtree(tmp)


def test_replay_scenario_success():
    """Recorder.replay_scenario: record → save → replay → verify healthy state."""
    import tempfile

    tmp = tempfile.mkdtemp()
    try:
        recorder = FailureRecorder(storage_dir=tmp)
        recorder.set_context(["PolicyA"], oscillation_score=3, global_regime="CONVERGENT")

        rec = recorder.record_violation(
            violation="TEMPORAL_DRIFT: max_skew=150.0ms (threshold=50.0ms)",
            layer="DRL",
            failure_type="TEMPORAL_DRIFT",
            severity="MEDIUM",
            invariant_states={"TEMPORAL_DRIFT": False},
            layer_states={"DRL": {"clock_skew_ms": 150.0}},
        )
        recorder._scenarios[rec.incident_id].recovery_actions = [
            RecoveryStep(0, "REWEIGHT", "ATTEMPT", "ATTEMPT", 1, 1000.1),
            RecoveryStep(1, "REWEIGHT", "ATTEMPT", "ATTEMPT", 2, 1000.2),
            RecoveryStep(2, "REWEIGHT", "ATTEMPT", "ESCALATE", 3, 1000.3),
        ]
        recorder.save(rec.incident_id)

        # replay_scenario returns dict with success, action, final_violations, details
        outcome = recorder.replay_scenario(rec.incident_id)
        assert outcome["success"] is True, f"got success={outcome['success']}"
        assert outcome["action"] is not None
        assert outcome["final_violations"] == []

        print("  FailureRecorder.replay_scenario success: OK")
    finally:
        shutil.rmtree(tmp)


def test_replay_determinism():
    """Two replay_scenario calls on same incident give identical results."""
    import tempfile

    tmp = tempfile.mkdtemp()
    try:
        recorder = FailureRecorder(storage_dir=tmp)
        recorder.set_context(["PolicyA"], oscillation_score=3, global_regime="CONVERGENT")

        rec = recorder.record_violation(
            violation="QUORUM_VIOLATION [F2]: ratio=0.3 (required=0.5)",
            layer="F2",
            failure_type="QUORUM_VIOLATION",
            severity="HIGH",
            invariant_states={"QUORUM_SAFETY": False},
            layer_states={"F2": {"quorum_ratio": 0.3}},
        )
        recorder._scenarios[rec.incident_id].recovery_actions = [
            RecoveryStep(0, "REWEIGHT", "ATTEMPT", "ATTEMPT", 1, 1000.1),
            RecoveryStep(1, "REWEIGHT", "ATTEMPT", "ATTEMPT", 2, 1000.2),
            RecoveryStep(2, "REWEIGHT", "ATTEMPT", "ESCALATE", 3, 1000.3),
        ]
        recorder.save(rec.incident_id)

        r1 = recorder.replay_scenario(rec.incident_id)
        r2 = recorder.replay_scenario(rec.incident_id)

        assert r1["success"] == r2["success"]
        assert r1["final_violations"] == r2["final_violations"]
        assert r1["details"] == r2["details"]

        print("  FailureRecorder.replay_scenario determinism: OK")
    finally:
        shutil.rmtree(tmp)


def test_replay_isolation():
    """replay_scenario on a second recorder doesn't affect the first."""
    import tempfile

    tmp = tempfile.mkdtemp()
    try:
        # Create two independent recorders pointing to same storage
        rec1 = FailureRecorder(storage_dir=tmp)
        rec1.set_context(["PolicyA"], oscillation_score=3, global_regime="CONVERGENT")
        scenario1 = rec1.record_violation(
            violation="TEMPORAL_DRIFT: max_skew=150.0ms (threshold=50.0ms)",
            layer="DRL",
            failure_type="TEMPORAL_DRIFT",
            severity="MEDIUM",
            invariant_states={"TEMPORAL_DRIFT": False},
            layer_states={"DRL": {"clock_skew_ms": 150.0}},
        )
        rec1._scenarios[scenario1.incident_id].recovery_actions = [
            RecoveryStep(0, "REWEIGHT", "ATTEMPT", "ATTEMPT", 1, 1000.1),
            RecoveryStep(1, "REWEIGHT", "ATTEMPT", "ATTEMPT", 2, 1000.2),
            RecoveryStep(2, "REWEIGHT", "ATTEMPT", "ESCALATE", 3, 1000.3),
        ]
        rec1.save(scenario1.incident_id)

        # A second recorder replays the same file
        rec2 = FailureRecorder(storage_dir=tmp)
        outcome2 = rec2.replay_scenario(scenario1.incident_id)

        # Both succeed — second didn't corrupt scenario
        assert outcome2["success"] is True

        # First recorder's in-memory state is unchanged
        assert scenario1.incident_id in rec1._scenarios

        print("  FailureRecorder.replay_scenario isolation: OK")
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    tests = [
        test_failure_params_from_violation,
        test_failure_scenario_roundtrip,
        test_recorder_records_violation,
        test_replayer_deterministic,
        test_replayer_detects_divergence,
        test_replayer_batch,
        test_replay_scenario_success,
        test_replay_determinism,
        test_replay_isolation,
    ]

    for fn in tests:
        try:
            fn()
        except Exception as e:
            print(f"  FAIL {fn.__name__}: {e}")
            sys.exit(1)

    print("\n  ALL FailureReplay TESTS PASSED")

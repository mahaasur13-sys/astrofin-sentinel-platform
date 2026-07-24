from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import logging
log = logging.getLogger(__name__)


# ── PATH ────────────────────────────────────────────────
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# ── IMPORTS ─────────────────────────────────────────────
from chaos.scenarios import ChaosScenario
from chaos.validator import ChaosValidator, ValidationResult, Verdict
from sbs.boundary_spec import SystemBoundarySpec
from sbs.global_invariant_engine import GlobalInvariantEngine


# ── ПРОСТОЙ EVENT STORE (вместо внешнего pkg.eventstore) ──
def _json_safe(obj):
    """Recursively replace non-JSON-serializable values with safe placeholders."""
    if callable(obj):
        return f"<callable:{obj.__name__ if hasattr(obj, '__name__') else type(obj).__name__}>"
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return repr(obj)


class EventStore:
    def __init__(self):
        self.events: list[dict[str, Any]] = []

    def append(self, stage: str, action: str, input_data: dict | None = None, output: dict | None = None):
        self.events.append({
            "timestamp": time.time(),
            "stage": stage,
            "action": action,
            "input": _json_safe(input_data) if input_data else {},
            "output": _json_safe(output) if output else {},
        })

    def dump(self) -> list[dict]:
        return self.events


# ── CONST ───────────────────────────────────────────────
REPLAY_DIR = Path("/tmp/atom-federation-os/replay")
REPLAY_DIR.mkdir(parents=True, exist_ok=True)


# ── ENUM ────────────────────────────────────────────────
class ExperimentPhase(Enum):
    COMPLETE = "complete"


# ── RESULT ──────────────────────────────────────────────
@dataclass
class ChaosResult:
    scenario_name: str
    phase: ExperimentPhase
    verdict: Verdict
    duration_s: float
    fault_apply_duration_s: float
    raw_events: list[dict]          # добавлено для replay
    incident_id: str                # добавлено

    def save_to_failure_replay(self) -> str | None:
        """Save this chaos result to FailureReplay with correct stage progression."""
        if self.verdict == Verdict.PASS:
            return None

        try:
            from alignment.adlr import ADLRecoveryOrchestrator, FailureReplay

            # Маппинг действий из chaos → понятные оркестратору
            action_mapping = {
                "start_scenario": "NOOP",
                "apply_fault": "NOOP",
                "sleep": "NOOP",
                "check_invariants": "REWEIGHT",
                "validator_result": "REWEIGHT",
                "chaos_fail": "EPOCH_RESET",
                "chaos_pass": "NOOP",
                "fault_failed": "EPOCH_RESET",
                "sbs_failed": "EPOCH_RESET",
                "validation_failed": "EPOCH_RESET",
            }
            actions = []
            for ev in self.raw_events:
                act = ev.get("action", "unknown")
                actions.append(action_mapping.get(act, "NOOP"))

            if not actions:
                actions = ["NOOP"]

            # Симуляция оркестратора для получения реальных стадий
            orch = ADLRecoveryOrchestrator(byzantine_risk=False, k=3, t=len(actions))
            stage_sequence = []
            for action in actions:
                stage = orch.step(action)
                stage_sequence.append(stage.name)

            final_stage = stage_sequence[-1] if stage_sequence else "TERMINAL"
            final_action = actions[-1] if actions else "NOOP"

            fr = FailureReplay()
            incident = fr.record(
                action_sequence=actions,
                stage_sequence=stage_sequence,
                oscillation_scores=[1] * len(actions),
                byzantine_risk=False,
                k=3,
                t=len(actions),
                final_stage=final_stage,
                final_action=final_action,
                metadata={
                    "chaos_scenario": self.scenario_name,
                    "verdict": self.verdict.value,
                    "duration_s": self.duration_s,
                    "incident_id": self.incident_id,
                },
            )
            return fr.save(incident.incident_id)
        except Exception as e:
            log.info(f"Failed to save to FailureReplay: {e}")
            return None


# ── HARNESS ─────────────────────────────────────────────
class ChaosHarness:
    def __init__(
        self,
        scenario: ChaosScenario,
        cluster_ctx: dict[str, Any],
        stabilization_time_s: float = 2.0,
    ):
        self.scenario = scenario
        self.cluster_ctx = cluster_ctx
        self.stabilization_time_s = stabilization_time_s

        self.validator = ChaosValidator()
        self.sbs_engine = GlobalInvariantEngine(SystemBoundarySpec())

        self.event_store = EventStore()
        self.incident_id = uuid.uuid4().hex[:8]

    # ────────────────────────────────────────────────────
    def run(self) -> ChaosResult:
        start_ts = time.time()
        raw_events = []  # накапливаем для результата

        # START
        self.event_store.append(
            stage="ATTEMPT",
            action="start_scenario",
            input_data={
                "scenario": self.scenario.name,
                "cluster": self.cluster_ctx,
            },
        )
        raw_events.append({"stage": "ATTEMPT", "action": "start_scenario"})

        # FAULT
        fault_start = time.time()
        try:
            self.event_store.append(
                stage="FAULT_INJECTION",
                action="apply_fault",
            )
            raw_events.append({"stage": "FAULT_INJECTION", "action": "apply_fault"})
            self.scenario.apply(self.cluster_ctx)
        except Exception as e:
            self.event_store.append(
                stage="ERROR",
                action="fault_failed",
                output={"error": str(e)},
            )
            raw_events.append({"stage": "ERROR", "action": "fault_failed"})
            return self._finalize(start_ts, Verdict.FAIL, fault_duration=0.0, raw_events=raw_events)

        fault_duration = time.time() - fault_start

        # STABILIZE
        self.event_store.append(
            stage="STABILIZATION",
            action="sleep",
            input_data={"seconds": self.stabilization_time_s},
        )
        raw_events.append({"stage": "STABILIZATION", "action": "sleep"})
        time.sleep(self.stabilization_time_s)

        # COLLECT (минимально)
        health_states = {
            "nodes": self.cluster_ctx.get("nodes", []),
            "status": "unknown",
        }
        ccl_state = {
            "nodes": self.cluster_ctx.get("nodes", []),
            "connectivity": "unknown",
        }
        f2_state = {
            "fault_tolerance": "unknown",
        }
        desc_state = {
            "system": "cluster",
            "mode": "chaos_test",
        }

        # SBS EVAL
        try:
            sbs_ok = self.sbs_engine.evaluate(
                self.cluster_ctx,
                ccl_state,
                f2_state,
                desc_state,
            )
        except Exception as e:
            self.event_store.append(
                stage="ERROR",
                action="sbs_failed",
                output={"error": str(e)},
            )
            raw_events.append({"stage": "ERROR", "action": "sbs_failed"})
            return self._finalize(start_ts, Verdict.FAIL, fault_duration, raw_events)

        sbs_results = [{"ok": sbs_ok}]
        self.event_store.append(
            stage="SBS",
            action="check_invariants",
            output={"ok": sbs_ok},
        )
        raw_events.append({"stage": "SBS", "action": "check_invariants", "result": sbs_ok})

        # EXPECTED BEHAVIOR
        if hasattr(self.scenario, "expected_behavior"):
            expected_behavior = self.scenario.expected_behavior()
        else:
            expected_behavior = {
                "type": "steady_state",
                "allowed_failures": 0,
            }

        # VALIDATION
        try:
            validation: ValidationResult = self.validator.validate(
                self.cluster_ctx,
                health_states,
                sbs_results,
                self.event_store.dump(),
                expected_behavior,
            )
        except Exception as e:
            self.event_store.append(
                stage="ERROR",
                action="validation_failed",
                output={"error": str(e)},
            )
            raw_events.append({"stage": "ERROR", "action": "validation_failed"})
            return self._finalize(start_ts, Verdict.FAIL, fault_duration, raw_events)

        self.event_store.append(
            stage="VALIDATION",
            action="validator_result",
            output={
                "verdict": validation.verdict.value,
                "details": getattr(validation, "details", {}),
            },
        )
        raw_events.append({"stage": "VALIDATION", "action": "validator_result", "verdict": validation.verdict.value})

        verdict = Verdict.FAIL if validation.verdict == Verdict.FAIL else Verdict.PASS
        return self._finalize(start_ts, verdict, fault_duration, raw_events)

    # ────────────────────────────────────────────────────
    def _finalize(
        self,
        start_ts: float,
        verdict: Verdict,
        fault_duration: float = 0.0,
        raw_events: list[dict] | None = None,
    ) -> ChaosResult:
        duration = time.time() - start_ts
        if raw_events is None:
            raw_events = []

        self.event_store.append(
            stage="TERMINAL",
            action="chaos_pass" if verdict == Verdict.PASS else "chaos_fail",
        )
        raw_events.append({"stage": "TERMINAL", "action": "chaos_fail" if verdict != Verdict.PASS else "chaos_pass"})

        # ── Сохраняем в старом формате (для совместимости) ──
        record = {
            "incident_id": self.incident_id,
            "timestamp": time.time(),
            "events": self.event_store.dump(),
            "final_stage": "TERMINAL",
            "metadata": {
                "scenario": self.scenario.name,
                "verdict": verdict.value,
                "duration_s": round(duration, 2),
            },
        }
        path = REPLAY_DIR / f"{self.incident_id}.json"
        with open(path, "w") as f:
            json.dump(record, f, indent=2)

        # ── Создаём ChaosResult ──
        result = ChaosResult(
            scenario_name=self.scenario.name,
            phase=ExperimentPhase.COMPLETE,
            verdict=verdict,
            duration_s=duration,
            fault_apply_duration_s=fault_duration,
            raw_events=raw_events,
            incident_id=self.incident_id,
        )

        # ── Сохраняем в FailureReplay (через правильный метод) ──
        replay_path = result.save_to_failure_replay()
        if replay_path:
            log.info(f"✅ Saved to replay: {replay_path}")

        log.info(f"\n🔥 Scenario: {self.scenario.name}")
        log.info(f"Verdict: {verdict.value}")
        log.info(f"Saved: {path}")

        return result


# ── ENTRYPOINT ───────────────────────────────────────────
if __name__ == "__main__":
    from chaos.scenarios import node_isolation

    scenario = node_isolation()
    harness = ChaosHarness(
        scenario=scenario,
        cluster_ctx={"nodes": ["node-a", "node-b", "node-c"]},
    )
    result = harness.run()
    log.info("\n=== RESULT ===")
    log.info(result)

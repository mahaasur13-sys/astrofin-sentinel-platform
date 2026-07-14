from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

# ── PATH SETUP ─────────────────────────────────────────────
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# ── IMPORTS ────────────────────────────────────────────────
from chaos.scenarios import ChaosScenario
from chaos.validator import ChaosValidator, ValidationResult, Verdict
from pkg.eventstore.store import EventStore
from sbs.boundary_spec import SystemBoundarySpec
from sbs.global_invariant_engine import GlobalInvariantEngine

# ── CONSTANTS ──────────────────────────────────────────────
REPLAY_DIR = Path("/tmp/atom-federation-os/replay")
REPLAY_DIR.mkdir(parents=True, exist_ok=True)


# ── ENUMS ──────────────────────────────────────────────────
class ExperimentPhase(Enum):
    IDLE = "idle"
    FAULT_INJECTION = "fault_injection"
    STABILIZATION = "stabilization"
    VALIDATION = "validation"
    COMPLETE = "complete"


# ── RESULT ─────────────────────────────────────────────────
@dataclass
class ChaosResult:
    scenario_name: str
    phase: ExperimentPhase
    verdict: Verdict
    duration_s: float
    fault_apply_duration_s: float


# ── HARNESS ────────────────────────────────────────────────
class ChaosHarness:
    """
    Jepsen-style Chaos Harness with Event Sourcing.
    """

    def __init__(
        self,
        scenario: ChaosScenario,
        cluster_ctx: dict[str, Any],
        stabilization_time_s: float = 5.0,
    ):
        self.scenario = scenario
        self.cluster_ctx = cluster_ctx
        self.stabilization_time_s = stabilization_time_s

        self.validator = ChaosValidator()
        self.sbs_engine = GlobalInvariantEngine(SystemBoundarySpec())

        self.event_store = EventStore()
        self.incident_id = uuid.uuid4().hex[:8]

    # ────────────────────────────────────────────────────────
    def run(self) -> ChaosResult:
        start_ts = time.time()

        # ── STEP 0: START ───────────────────────────────────
        self.event_store.append(
            stage="ATTEMPT",
            action="start_scenario",
            input_data={
                "scenario": self.scenario.name,
                "cluster": self.cluster_ctx,
            },
        )

        # ── STEP 1: FAULT INJECTION ─────────────────────────
        fault_start = time.time()

        try:
            self.event_store.append(
                stage="FAULT_INJECTION",
                action="apply_fault",
            )

            self.scenario.apply(self.cluster_ctx)

        except Exception as e:
            self.event_store.append(
                stage="ERROR",
                action="fault_injection_failed",
                output={"error": str(e)},
            )
            return self._finalize(start_ts, Verdict.FAIL)

        fault_duration = time.time() - fault_start

        # ── STEP 2: STABILIZATION ───────────────────────────
        self.event_store.append(
            stage="STABILIZATION",
            action="wait",
            input_data={"seconds": self.stabilization_time_s},
        )

        time.sleep(self.stabilization_time_s)

        # ── STEP 3: VALIDATION ──────────────────────────────
        self.event_store.append(
            stage="VALIDATION",
            action="run_validator",
        )

        validation: ValidationResult = self.validator.validate(self.cluster_ctx)

        self.event_store.append(
            stage="VALIDATION_RESULT",
            action="validator_result",
            output={
                "verdict": validation.verdict.value,
                "details": validation.details,
            },
        )

        # ── STEP 4: SBS INVARIANTS ──────────────────────────
        sbs_ok = self.sbs_engine.evaluate(self.cluster_ctx)

        self.event_store.append(
            stage="SBS_CHECK",
            action="global_invariants",
            output={"ok": sbs_ok},
        )

        # ── FINAL VERDICT ───────────────────────────────────
        if validation.verdict == Verdict.FAIL or not sbs_ok:
            verdict = Verdict.FAIL
        else:
            verdict = Verdict.PASS

        return self._finalize(
            start_ts,
            verdict,
            fault_duration,
            validation,
        )

    # ────────────────────────────────────────────────────────
    def _finalize(
        self,
        start_ts: float,
        verdict: Verdict,
        fault_duration: float = 0.0,
        validation: ValidationResult | None = None,
    ) -> ChaosResult:

        duration = time.time() - start_ts

        final_action = "chaos_pass" if verdict == Verdict.PASS else "chaos_fail"

        self.event_store.append(
            stage="TERMINAL",
            action=final_action,
            output={
                "verdict": verdict.value,
                "duration_s": round(duration, 3),
            },
        )

        record = {
            "incident_id": self.incident_id,
            "timestamp": time.time(),

            # legacy
            "action_sequence": [e["action"] for e in self.event_store.events],
            "stage_sequence": [e["stage"] for e in self.event_store.events],

            # 🔥 главное
            "events": self.event_store.dump(),

            "final_stage": "TERMINAL",
            "final_action": final_action,

            "metadata": {
                "chaos_scenario": self.scenario.name,
                "verdict": verdict.value,
                "duration_s": round(duration, 3),
                "fault_apply_duration_s": round(fault_duration, 3),
            },
        }

        path = REPLAY_DIR / f"{self.incident_id}.json"

        with open(path, "w") as f:
            json.dump(record, f, indent=2)

        print("\n🔥 Chaos Experiment Result")
        print(f"Scenario: {self.scenario.name}")
        print(f"Verdict: {verdict.value}")
        print(f"Duration: {round(duration, 2)}s")
        print(f"Saved to replay: {path}")

        return ChaosResult(
            scenario_name=self.scenario.name,
            phase=ExperimentPhase.COMPLETE,
            verdict=verdict,
            duration_s=duration,
            fault_apply_duration_s=fault_duration,
        )

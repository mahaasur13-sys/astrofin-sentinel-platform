"""
ReplayValidator — H-4: Deterministic replay & divergence detection for chaos traces.

Records chaos events, drift episodes, feedback decisions, and envelope states
into a serializable trace. Supports faithful replay and computes divergence scores
between original and replayed runs.

Usage
----
    rv = ReplayValidator()

    trace_id = rv.start_trace("partition_half_cluster")

    rv.record_step(trace_id, step_index=0, phase="chaos",
                   event={"type": "partition", "target": "node-a"},
                   metrics={"plan_stability_index": 0.7,
                            "coherence_drop_rate": 0.05,
                            "replanning_frequency": 0.1,
                            "oscillation_index": 0.05},
                   feedback={"action": "adapt_rate", "delta": -0.1})

    rv.record_step(trace_id, step_index=1, phase="recovery",
                   event={"type": "quorum_restored"},
                   metrics={"plan_stability_index": 0.9,
                            "coherence_drop_rate": 0.0,
                            "replanning_frequency": 0.0,
                            "oscillation_index": 0.0},
                   feedback={"action": "none"})

    trace = rv.finalize_trace(trace_id)

    # Replay: system produces new outputs for the same events
    replayed = rv.replay(trace,
                          system_eval_fn=lambda step: {"output_hash": "abc123",
                                                       "envelope_state": "stable",
                                                       "impact": 0.0})

    # Compare original vs replayed
    report = rv.compare(trace, replayed)
    log.info(report.divergence_score)   # 0.0 = identical
    log.info(report.verdict)            # DETERMINISTIC / DIVERGENT / PARTIAL
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from chaos.stress_envelope import StabilityEnvelope, StabilityState

import logging
log = logging.getLogger(__name__)


# ── Enums ─────────────────────────────────────────────────────────────────────


class TracePhase(Enum):
    CHAOS = "chaos"
    RECOVERY = "recovery"
    CONVERGENCE = "convergence"
    UNKNOWN = "unknown"


class ReplayVerdict(Enum):
    DETERMINISTIC = "DETERMINISTIC"
    DIVERGENT = "DIVERGENT"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


# ── Dataclasses ───────────────────────────────────────────────────────────────


@dataclass
class TraceStep:
    """
    Single recorded step in a chaos trace.

    phase          : which control loop phase this step belongs to
    event          : chaos event or cluster event that occurred
    metrics        : snapshot of all StabilityEnvelope metrics at this step
    feedback       : feedback decision made by the adaptive controller
    envelope_state : computed StabilityState at this step
    timestamp      : wall-clock time when step was recorded
    """
    step_index: int
    phase: TracePhase
    event: dict[str, Any]
    metrics: dict[str, float]
    feedback: dict[str, Any]
    envelope_state: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["phase"] = self.phase.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> TraceStep:
        d = dict(d)
        d["phase"] = TracePhase(d["phase"])
        return cls(**d)

    def metrics_hash(self) -> str:
        canonical = json.dumps(self.metrics, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def event_hash(self) -> str:
        canonical = json.dumps(self.event, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass
class ChaosTrace:
    """
    Complete recorded trace of one chaos experiment run.
    """
    id: str
    scenario_name: str
    started_at: float = field(default_factory=time.time)
    steps: list[TraceStep] = field(default_factory=list)
    finalized: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scenario_name": self.scenario_name,
            "started_at": self.started_at,
            "finalized": self.finalized,
            "metadata": self.metadata,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, d: dict) -> ChaosTrace:
        steps = [TraceStep.from_dict(s) for s in d.get("steps", [])]
        return cls(
            id=d["id"],
            scenario_name=d["scenario_name"],
            started_at=d.get("started_at", time.time()),
            finalized=d.get("finalized", False),
            metadata=d.get("metadata", {}),
            steps=steps,
        )

    def duration_s(self) -> float:
        if not self.steps:
            return 0.0
        return self.steps[-1].timestamp - self.started_at

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_json(cls, s: str) -> ChaosTrace:
        return cls.from_dict(json.loads(s))


@dataclass
class ReplayResult:
    """
    Result of replaying a trace against a live/replayed system.
    """
    trace_id: str
    replayed_steps: list[dict[str, Any]] = field(default_factory=list)
    replayed_at: float = field(default_factory=time.time)
    duration_s: float = 0.0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class DivergenceReport:
    """
    Comparison report between an original trace and a replayed trace.
    """
    trace_id: str
    replay_verdict: ReplayVerdict
    divergence_score: float
    drift_count_diff: int
    impact_delta: float
    envelope_mismatch: int
    convergence_diff: int
    step_divergences: list[dict[str, Any]] = field(default_factory=list)
    verdict: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["replay_verdict"] = self.replay_verdict.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ── Core Validator ────────────────────────────────────────────────────────────


class ReplayValidator:
    """
    Records chaos traces and validates system determinism via replay.

    Integration with ChaosObservabilityBridge
    ------------------------------------------
        rv = ReplayValidator()

        # In the control loop, after each step:
        rv.record_step(
            trace_id   = observation_id,
            step_index = step_num,
            phase      = TracePhase.CHAOS,
            event      = event_dict,
            metrics    = stability_metrics_dict,
            feedback   = feedback_dict,
        )

        # After the experiment ends:
        trace   = rv.finalize_trace(trace_id)
        replayed = rv.replay(trace, system_eval_fn=my_system.eval_step)
        report   = rv.compare(trace, replayed)
    """

    def __init__(self, tolerance: float = 0.1):
        self.tolerance = tolerance
        self.envelope = StabilityEnvelope()
        self._active_traces: dict[str, ChaosTrace] = {}
        self._traces: dict[str, ChaosTrace] = {}

    # ── Recording API ─────────────────────────────────────────────────────────

    def start_trace(self, scenario_name: str,
                    metadata: dict[str, Any] | None = None) -> str:
        trace_id = str(uuid.uuid4())[:8]
        trace = ChaosTrace(
            id=trace_id,
            scenario_name=scenario_name,
            metadata=metadata or {},
        )
        self._active_traces[trace_id] = trace
        return trace_id

    def record_step(
        self,
        trace_id: str,
        step_index: int,
        phase: TracePhase | str,
        event: dict[str, Any],
        metrics: dict[str, float],
        feedback: dict[str, Any],
    ) -> None:
        if trace_id not in self._active_traces:
            raise KeyError(f"No active trace with id={trace_id}. Call start_trace() first.")
        if isinstance(phase, str):
            phase = TracePhase(phase)
        report = self.envelope.evaluate(metrics)
        step = TraceStep(
            step_index=step_index,
            phase=phase,
            event=event,
            metrics=metrics,
            feedback=feedback,
            envelope_state=report.state.value,
        )
        self._active_traces[trace_id].steps.append(step)

    def finalize_trace(self, trace_id: str) -> ChaosTrace:
        if trace_id not in self._active_traces:
            raise KeyError(f"No active trace with id={trace_id}.")
        trace = self._active_traces.pop(trace_id)
        trace.finalized = True
        self._traces[trace_id] = trace
        return trace

    def save_trace(self, trace_id: str, path: str) -> None:
        if trace_id not in self._traces:
            raise KeyError(f"No finalized trace with id={trace_id}.")
        trace = self._traces[trace_id]
        with open(path, "w") as f:
            f.write(trace.to_json())

    def load_trace(self, path: str) -> ChaosTrace:
        with open(path) as f:
            trace = ChaosTrace.from_json(f.read())
        self._traces[trace.id] = trace
        return trace

    def get_trace(self, trace_id: str) -> ChaosTrace:
        if trace_id not in self._traces:
            raise KeyError(f"No finalized trace with id={trace_id}.")
        return self._traces[trace_id]

    # ── Replay API ────────────────────────────────────────────────────────────

    def replay(
        self,
        trace: ChaosTrace,
        system_eval_fn: Callable[[TraceStep], dict[str, Any]],
    ) -> ReplayResult:
        if not trace.finalized:
            raise ValueError(f"Trace {trace.id} is not finalized.")
        result = ReplayResult(trace_id=trace.id)
        start = time.time()
        try:
            for step in trace.steps:
                output = system_eval_fn(step)
                result.replayed_steps.append(output)
        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"
        result.duration_s = time.time() - start
        return result

    # ── Comparison API ────────────────────────────────────────────────────────

    def compare(self, original: ChaosTrace,
                replayed: ReplayResult) -> DivergenceReport:
        if replayed.error:
            return DivergenceReport(
                trace_id=original.id,
                replay_verdict=ReplayVerdict.ERROR,
                divergence_score=1.0,
                drift_count_diff=0,
                impact_delta=0.0,
                envelope_mismatch=0,
                convergence_diff=0,
                verdict=f"Replay error: {replayed.error}",
            )

        # ── Single-pass accumulation ─────────────────────────────────────────
        DRIFT_STATES = {
            StabilityState.WARNING.value,
            StabilityState.CRITICAL.value,
            StabilityState.COLLAPSE.value,
        }

        drift_count_orig = 0
        cumulative_impact = 0.0
        first_stable_orig = len(original.steps)   # default: no convergence

        envelope_mismatches = 0
        step_divergences = []

        # Replay state is per-step, indexed by step_index
        replay_by_index = {
            i: step
            for i, step in enumerate(replayed.replayed_steps)
        }

        n = len(original.steps)
        for i, orig_step in enumerate(original.steps):
            # ── original accumulators ───────────────────────────────────────
            if orig_step.envelope_state in DRIFT_STATES:
                drift_count_orig += 1
            else:
                if first_stable_orig == n:        # first time we see STABLE
                    first_stable_orig = i

            r = self.envelope.evaluate(orig_step.metrics)
            cumulative_impact += r.violation_score

            # ── envelope mismatch (per-step pair) ─────────────────────────
            repl_step = replay_by_index.get(i, {})
            repl_state = repl_step.get("envelope_state", "")
            mismatch = orig_step.envelope_state != repl_state
            step_divergences.append({
                "step_index": i,
                "original_envelope": orig_step.envelope_state,
                "replayed_envelope": repl_state,
                "mismatch": mismatch,
            })
            if mismatch:
                envelope_mismatches += 1

        # ── replay-side accumulators ─────────────────────────────────────────
        drift_count_repl = sum(
            1 for step in replayed.replayed_steps
            if step.get("envelope_state", "") in DRIFT_STATES
        )
        cumulative_replay_impact = sum(
            step.get("impact", 0.0) for step in replayed.replayed_steps
        )

        # convergence on replayed side
        first_stable_repl = n
        for i, step in enumerate(replayed.replayed_steps):
            state = step.get("envelope_state", "")
            if state == StabilityState.STABLE.value or state not in DRIFT_STATES:
                first_stable_repl = i
                break

        # ── final deltas ────────────────────────────────────────────────────
        drift_count_diff   = abs(drift_count_orig - drift_count_repl)
        impact_delta       = abs(cumulative_impact - cumulative_replay_impact)
        convergence_diff   = abs(first_stable_orig - first_stable_repl)

        score = self._divergence_score(
            drift_count_diff, impact_delta,
            envelope_mismatches, convergence_diff,
            total_steps=n,
        )

        if score == 0.0:
            verdict = ReplayVerdict.DETERMINISTIC
            verdict_str = "Identical outputs — system is deterministic"
        elif score <= self.tolerance:
            verdict = ReplayVerdict.PARTIAL
            verdict_str = f"Minor divergence (score={score:.3f}) — within tolerance"
        else:
            verdict = ReplayVerdict.DIVERGENT
            verdict_str = f"Material divergence detected (score={score:.3f})"

        return DivergenceReport(
            trace_id=original.id,
            replay_verdict=verdict,
            divergence_score=score,
            drift_count_diff=drift_count_diff,
            impact_delta=impact_delta,
            envelope_mismatch=envelope_mismatches,
            convergence_diff=convergence_diff,
            step_divergences=step_divergences,
            verdict=verdict_str,
        )

    # ── Public helpers (keep for test compatibility) ───────────────────────────

    def _steps_to_convergence(self, trace: ChaosTrace) -> int:
        """Return step index of first STABLE state, or len(steps) if never stable."""
        for i, step in enumerate(trace.steps):
            if step.envelope_state == StabilityState.STABLE.value:
                return i
        return len(trace.steps)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _divergence_score(self, drift_diff: int, impact_delta: float,
                          env_mismatch: int, conv_diff: int,
                          total_steps: int) -> float:
        if total_steps == 0:
            return 0.0
        norm_drift = drift_diff / max(total_steps, 1)
        norm_env = env_mismatch / max(total_steps, 1)
        norm_conv = conv_diff / max(total_steps, 1)
        # impact_delta is already normalized (violation_score is 0-1)
        return min(1.0, norm_drift + impact_delta + norm_env + norm_conv)

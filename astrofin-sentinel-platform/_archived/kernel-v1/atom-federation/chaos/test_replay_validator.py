"""
Tests for ReplayValidator (H-4).
"""

import pytest

from chaos.replay_validator import (
    ChaosTrace,
    ReplayValidator,
    ReplayVerdict,
    TracePhase,
)
from chaos.stress_envelope import StabilityEnvelope

STABLE_METRICS = {
    "plan_stability_index": 0.9,
    "coherence_drop_rate": 0.05,
    "replanning_frequency": 0.1,
    "oscillation_index": 0.05,
}

COLLAPSE_METRICS = {
    "plan_stability_index": 0.2,
    "coherence_drop_rate": 0.5,
    "replanning_frequency": 0.7,
    "oscillation_index": 0.8,
}

_env = StabilityEnvelope()
_ORIGINAL_IMPACTS = [
    _env.evaluate(STABLE_METRICS).violation_score,
    _env.evaluate(COLLAPSE_METRICS).violation_score,
    _env.evaluate(STABLE_METRICS).violation_score,
]
assert _ORIGINAL_IMPACTS[0] == 0.0
assert _ORIGINAL_IMPACTS[1] > 0.5


def _build_3step_trace(rv: ReplayValidator) -> ChaosTrace:
    tid = rv.start_trace("partition_half_cluster", metadata={"nodes": 3})
    rv.record_step(tid, 0, TracePhase.CHAOS,
                   event={"type": "partition"},
                   metrics=STABLE_METRICS,
                   feedback={"action": "none"})
    rv.record_step(tid, 1, TracePhase.RECOVERY,
                   event={"type": "quorum_check"},
                   metrics=COLLAPSE_METRICS,
                   feedback={"action": "adapt_rate", "delta": -0.1})
    rv.record_step(tid, 2, TracePhase.CONVERGENCE,
                   event={"type": "leader_elected"},
                   metrics=STABLE_METRICS,
                   feedback={"action": "none"})
    return rv.finalize_trace(tid)


def make_deterministic_eval_fn():
    states = ["stable", "collapse", "stable"]
    def eval_fn(step):
        i = step.step_index
        return {"output_hash": f"hash-step{i}",
                "envelope_state": states[i],
                "impact": _ORIGINAL_IMPACTS[i]}
    return eval_fn


def make_slightly_different_eval_fn():
    def eval_fn(step):
        if step.step_index == 0:
            return {"output_hash": "stable-hash", "envelope_state": "stable", "impact": 0.0}
        return {"output_hash": "changed-hash", "envelope_state": "warning", "impact": 0.3}
    return eval_fn


# ── Test 1: Deterministic replay ─────────────────────────────────────────────

class TestDeterministicReplay:

    def test_identical_output_deterministic_verdict(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        replayed = rv.replay(trace, make_deterministic_eval_fn())
        report = rv.compare(trace, replayed)
        assert report.replay_verdict == ReplayVerdict.DETERMINISTIC
        assert report.divergence_score == 0.0
        assert report.drift_count_diff == 0
        assert report.envelope_mismatch == 0
        assert report.convergence_diff == 0

    def test_deterministic_eval_fn_idempotent(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        eval_fn = make_deterministic_eval_fn()
        r1 = rv.replay(trace, eval_fn)
        r2 = rv.replay(trace, eval_fn)
        assert r1.replayed_steps == r2.replayed_steps

    def test_feedback_consistent_across_runs(self):
        rv1 = ReplayValidator()
        rv2 = ReplayValidator()
        trace1 = _build_3step_trace(rv1)
        trace2 = _build_3step_trace(rv2)
        for a, b in zip(trace1.steps, trace2.steps):
            assert a.feedback == b.feedback

    def test_trace_serialization_roundtrip(self):
        rv = ReplayValidator()
        trace = _build_3step_trace(rv)
        restored = ChaosTrace.from_json(trace.to_json())
        assert restored.id == trace.id
        assert len(restored.steps) == len(trace.steps)
        assert restored.finalized
        for a, b in zip(trace.steps, restored.steps):
            assert a.envelope_state == b.envelope_state
            assert a.feedback == b.feedback


# ── Test 2: Divergence detection ─────────────────────────────────────────────

class TestDivergenceDetection:

    def test_divergence_score_nonzero(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        replayed = rv.replay(trace, make_slightly_different_eval_fn())
        report = rv.compare(trace, replayed)
        assert report.divergence_score > 0.0
        assert report.replay_verdict in (ReplayVerdict.DIVERGENT, ReplayVerdict.PARTIAL)

    def test_drift_count_diff_detected(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        def eval_fn(step):
            return {"output_hash": "x", "envelope_state": "collapse", "impact": 1.0}
        replayed = rv.replay(trace, eval_fn)
        report = rv.compare(trace, replayed)
        assert report.drift_count_diff > 0

    def test_impact_delta_detected(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        def eval_fn(step):
            return {"output_hash": "x", "envelope_state": "stable", "impact": 2.0}
        replayed = rv.replay(trace, eval_fn)
        report = rv.compare(trace, replayed)
        assert report.impact_delta > 0.0

    def test_divergence_report_has_step_details(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        def eval_fn(step):
            return {"output_hash": "x", "envelope_state": "warning", "impact": 0.5}
        replayed = rv.replay(trace, eval_fn)
        report = rv.compare(trace, replayed)
        assert len(report.step_divergences) == len(trace.steps)
        assert all("step_index" in d for d in report.step_divergences)
        assert all("mismatch" in d for d in report.step_divergences)


# ── Test 3: Envelope consistency ─────────────────────────────────────────────

class TestEnvelopeConsistency:

    def test_envelope_state_sequence(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        assert [s.envelope_state for s in trace.steps] == ["stable", "collapse", "stable"]

    def test_envelope_mismatch_zero_when_identical(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        replayed = rv.replay(trace, make_deterministic_eval_fn())
        report = rv.compare(trace, replayed)
        assert report.envelope_mismatch == 0
        assert report.divergence_score == 0.0

    def test_envelope_mismatch_nonzero_when_different(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        def eval_fn(step):
            return {"output_hash": "x", "envelope_state": "critical", "impact": 0.8}
        replayed = rv.replay(trace, eval_fn)
        report = rv.compare(trace, replayed)
        # All 3 steps mismatch (stable≠critical, collapse≠critical, stable≠critical)
        assert report.envelope_mismatch == 3

    def test_convergence_at_first_stable_step(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        assert rv._steps_to_convergence(trace) == 0  # step 0 already stable

    def test_convergence_diff_detected(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        def eval_fn(step):
            state = "stable" if step.step_index >= 2 else "collapse"
            return {"output_hash": "x", "envelope_state": state, "impact": 0.0}
        replayed = rv.replay(trace, eval_fn)
        report = rv.compare(trace, replayed)
        assert report.convergence_diff == 2  # 0 vs 2


# ── Test 4: Edge cases ───────────────────────────────────────────────────────

class TestEdgeCases:

    def test_record_step_unknown_trace_raises(self):
        rv = ReplayValidator()
        with pytest.raises(KeyError):
            rv.record_step("bad-id", 0, TracePhase.CHAOS, {}, STABLE_METRICS, {})

    def test_finalize_unknown_trace_raises(self):
        rv = ReplayValidator()
        with pytest.raises(KeyError):
            rv.finalize_trace("bad-id")

    def test_replay_unfinalized_raises(self):
        rv = ReplayValidator()
        tid = rv.start_trace("test")
        trace = rv._active_traces[tid]
        with pytest.raises(ValueError):
            rv.replay(trace, lambda s: {})

    def test_replay_error_sets_error_verdict(self):
        rv = ReplayValidator(tolerance=0.1)
        trace = _build_3step_trace(rv)
        def bad_eval_fn(step):
            raise RuntimeError("system unavailable")
        replayed = rv.replay(trace, bad_eval_fn)
        report = rv.compare(trace, replayed)
        assert report.replay_verdict == ReplayVerdict.ERROR
        assert "RuntimeError" in report.verdict

    def test_divergence_score_bounded_at_one(self):
        rv = ReplayValidator(tolerance=0.0)
        trace = _build_3step_trace(rv)
        def worst_eval_fn(step):
            return {"output_hash": "x", "envelope_state": "collapse", "impact": 1.0}
        replayed = rv.replay(trace, worst_eval_fn)
        report = rv.compare(trace, replayed)
        assert report.divergence_score <= 1.0

    def test_empty_trace_divergence_zero(self):
        rv = ReplayValidator()
        tid = rv.start_trace("empty_scenario")
        trace = rv.finalize_trace(tid)
        def eval_fn(step):
            return {"output_hash": "x", "envelope_state": "stable", "impact": 0.0}
        replayed = rv.replay(trace, eval_fn)
        report = rv.compare(trace, replayed)
        assert report.divergence_score == 0.0
        assert report.replay_verdict == ReplayVerdict.DETERMINISTIC

    def test_partial_within_tolerance(self):
        rv = ReplayValidator(tolerance=0.5)
        trace = _build_3step_trace(rv)
        # Same drift count and envelope states as original.
        # Only a tiny impact delta (0.001 vs 0.0) on step 0.
        # This produces score < 0.5 → PARTIAL.
        def eval_fn(step):
            if step.step_index == 0:
                return {"output_hash": "x",
                        "envelope_state": "stable",
                        "impact": 0.001}  # tiny delta vs 0.0
            return {"output_hash": "x",
                    "envelope_state": ["stable", "collapse", "stable"][step.step_index],
                    "impact": _ORIGINAL_IMPACTS[step.step_index]}
        replayed = rv.replay(trace, eval_fn)
        report = rv.compare(trace, replayed)
        assert report.replay_verdict in (ReplayVerdict.DETERMINISTIC, ReplayVerdict.PARTIAL)

    def test_save_and_load_trace(self, tmp_path):
        rv = ReplayValidator()
        trace = _build_3step_trace(rv)
        path = tmp_path / "trace.json"
        rv.save_trace(trace.id, str(path))
        loaded = rv.load_trace(str(path))
        assert loaded.id == trace.id
        assert len(loaded.steps) == 3
        assert loaded.finalized

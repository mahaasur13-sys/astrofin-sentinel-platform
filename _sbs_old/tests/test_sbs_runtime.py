"""
SBS Runtime Enforcer — integration tests.

Verifies that SBSRuntimeEnforcer correctly enforces invariants
and raises InvariantViolation in ENFORCED mode at each stage.

Tests:
    1. ENFORCED mode blocks on violation
    2. AUDIT mode logs but does not block
    3. OFF mode is no-op
    4. execute_with_sbs() returns (plan, None) on success
    5. collect_state() returns correct layer snapshot
    6. Layer state getters registered via set_layers()
    7. ExecutionLoop sbs_is_available() returns True
"""

import pytest
import sys

sys.path.insert(0, "/home/workspace/atom-federation-os")
sys.path.insert(0, "/home/workspace/atomos_pkg")
sys.path.insert(0, "/home/workspace/agents")

from sbs import (
    SBSRuntimeEnforcer,
    SBS_MODE,
    InvariantViolation,
    ViolationPolicy,
    ExecutionStage,
    SystemBoundarySpec,
    GlobalInvariantEngine,
)


class TestSBSRuntimeEnforcer:
    """SBSRuntimeEnforcer core tests."""

    def test_enforced_mode__pass(self):
        """Healthy state → enforce returns True, no exception."""
        spec = SystemBoundarySpec()
        engine = GlobalInvariantEngine(spec)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.ENFORCED)

        state = {
            "drl": {"leader": "n1", "term": 1, "partitions": 0, "quorum_ratio": 0.9},
            "ccl": {"leader": "n1", "term": 1, "stale_reads": 0},
            "f2":  {"leader": "n1", "term": 1, "quorum_ratio": 0.9, "commit_index": 5},
            "desc": {"leader": "n1", "term": 1, "commit_index": 5},
            "quorum_ratio": 0.9,  # top-level for spec.validate()
            "partitions": 0,
        }
        result = enforcer.enforce(ExecutionStage.PRE_DRL, state)
        assert result is True
        assert enforcer.get_violations_summary() == {}

    def test_enforced_mode__violation_raises(self):
        """Invariant violation → InvariantViolation raised."""
        spec = SystemBoundarySpec(allow_split_brain=False, max_partitions=1)
        engine = GlobalInvariantEngine(spec)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.ENFORCED)

        state = {
            "drl": {"partitions": 2, "quorum_ratio": 0.9},
            "ccl": {},
            "f2":  {"quorum_ratio": 0.9},
            "desc": {},
            "partitions": 2,
            "quorum_ratio": 0.9,
        }
        with pytest.raises(InvariantViolation) as exc_info:
            enforcer.enforce(ExecutionStage.PRE_COMMIT, state)

        assert exc_info.value.stage == ExecutionStage.PRE_COMMIT
        assert len(exc_info.value.failed_invariants) > 0

    def test_audit_mode__violation_does_not_raise(self):
        """AUDIT mode → returns False, no exception."""
        spec = SystemBoundarySpec(allow_split_brain=False, max_partitions=1)
        engine = GlobalInvariantEngine(spec)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.AUDIT)

        state = {
            "drl": {"partitions": 2, "quorum_ratio": 0.9},
            "ccl": {},
            "f2":  {"quorum_ratio": 0.9},
            "desc": {},
            "partitions": 2,
            "quorum_ratio": 0.9,
        }
        result = enforcer.enforce(ExecutionStage.PRE_COMMIT, state)
        assert result is False

        log = enforcer.get_audit_log()
        assert len(log) == 1
        assert log[0]["stage"] == ExecutionStage.PRE_COMMIT
        assert len(log[0]["violations"]) > 0

    def test_off_mode__no_op(self):
        """OFF mode → always returns False, no enforcement."""
        spec = SystemBoundarySpec(allow_split_brain=False, max_partitions=1)
        engine = GlobalInvariantEngine(spec)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.OFF)

        state = {"drl": {"partitions": 999}, "partitions": 999}
        result = enforcer.enforce(ExecutionStage.POST_COMMIT, state)
        assert result is False
        assert enforcer.get_audit_log() == []

    def test_quorum_violation__pre_commit_blocks(self):
        """Quorum below threshold → pre_commit blocks in ENFORCED mode."""
        spec = SystemBoundarySpec(quorum_threshold=0.67)
        engine = GlobalInvariantEngine(spec)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.ENFORCED)

        state = {
            "drl": {"partitions": 0, "quorum_ratio": 0.3},
            "ccl": {},
            "f2":  {"quorum_ratio": 0.3},
            "desc": {},
            "quorum_ratio": 0.3,
            "partitions": 0,
        }
        with pytest.raises(InvariantViolation) as exc_info:
            enforcer.enforce(ExecutionStage.PRE_COMMIT, state)

        assert "QUORUM" in str(exc_info.value.failed_invariants[0])

    def test_leader_uniqueness_violation__detected(self):
        """Two layers with different leaders → detected as violation."""
        spec = SystemBoundarySpec()
        engine = GlobalInvariantEngine(spec)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.AUDIT)

        state = {
            "drl": {"leader": "node-1", "term": 3, "partitions": 0},
            "ccl": {"leader": "node-2", "term": 3},
            "f2":  {"leader": "node-1", "term": 3, "quorum_ratio": 0.9},
            "desc": {"leader": "node-1", "term": 3, "commit_index": 10},
            "partitions": 0,
            "quorum_ratio": 0.9,
        }
        result = enforcer.enforce(ExecutionStage.POST_QUORUM, state)
        assert result is False

        violations = enforcer.get_last_audit()["violations"]
        assert any("LEADER_UNIQUENESS" in v for v in violations)

    def test_custom_policy__warning_does_not_raise(self):
        """Custom WARNING policy → logs but does not raise."""
        spec = SystemBoundarySpec(allow_split_brain=False, max_partitions=1)
        engine = GlobalInvariantEngine(spec)
        policy = ViolationPolicy(level=ViolationPolicy.Level.WARNING)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.ENFORCED, default_policy=policy)

        state = {"drl": {"partitions": 2, "quorum_ratio": 0.9}, "ccl": {}, "f2": {}, "desc": {},
                 "partitions": 2, "quorum_ratio": 0.9}
        result = enforcer.enforce(ExecutionStage.PRE_DRL, state)
        assert result is False

    def test_per_stage_policy__override(self):
        """Per-stage policy overrides default."""
        spec = SystemBoundarySpec(allow_split_brain=False, max_partitions=1)
        engine = GlobalInvariantEngine(spec)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.ENFORCED)

        enforcer.set_policy(
            ExecutionStage.PRE_DRL,
            ViolationPolicy(level=ViolationPolicy.Level.WARNING),
        )
        state = {"drl": {"partitions": 2, "quorum_ratio": 0.9}, "ccl": {}, "f2": {}, "desc": {},
                 "partitions": 2, "quorum_ratio": 0.9}
        result = enforcer.enforce(ExecutionStage.PRE_DRL, state)
        assert result is False

        with pytest.raises(InvariantViolation):
            enforcer.enforce(ExecutionStage.POST_COMMIT, state)

    def test_audit_log__persists(self):
        """Audit log accumulates across multiple enforce() calls."""
        spec = SystemBoundarySpec()
        engine = GlobalInvariantEngine(spec)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.AUDIT)

        healthy = {
            "drl": {"leader": "n1", "term": 1, "partitions": 0},
            "ccl": {},
            "f2":  {},
            "desc": {},
            "partitions": 0,
            "quorum_ratio": 0.9,
        }
        for i in range(3):
            enforcer.enforce(f"stage_{i}", healthy)

        log = enforcer.get_audit_log()
        assert len(log) == 3
        enforcer.clear_audit_log()
        assert enforcer.get_audit_log() == []

    def test_flat_state__fallback(self):
        """Flat state dict (no sub-dicts) is treated as all layers."""
        spec = SystemBoundarySpec(quorum_threshold=0.67)
        engine = GlobalInvariantEngine(spec)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.ENFORCED)

        state = {"partitions": 0, "quorum_ratio": 0.3}
        with pytest.raises(InvariantViolation):
            enforcer.enforce(ExecutionStage.PRE_COMMIT, state)

    def test_recoverable_policy__calls_reconcile(self):
        """RECOVERABLE policy calls reconcile_fn."""
        spec = SystemBoundarySpec(allow_split_brain=False, max_partitions=1)
        engine = GlobalInvariantEngine(spec)
        reconcile_called = []

        def reconcile(stage, state):
            reconcile_called.append((stage, state))

        policy = ViolationPolicy(level=ViolationPolicy.Level.RECOVERABLE, reconcile_fn=reconcile)
        enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.ENFORCED, default_policy=policy)

        state = {"drl": {"partitions": 2, "quorum_ratio": 0.9}, "ccl": {}, "f2": {}, "desc": {},
                 "partitions": 2, "quorum_ratio": 0.9}
        result = enforcer.enforce(ExecutionStage.PRE_EXECUTE, state)
        assert result is False
        assert len(reconcile_called) == 1
        assert reconcile_called[0][0] == ExecutionStage.PRE_EXECUTE


class TestExecutionLoopSBS:
    """ExecutionLoop SBS integration tests."""

    def _make_loop(self):
        from atomos.core.execution_loop import ExecutionLoop

        class StubPK:
            def evaluate(self, action, context, user_intent):
                return ("ALLOW", "ok", {}, {})

        return ExecutionLoop(policy_kernel=StubPK())

    def test_execute_plan__backward_compatible(self):
        """Original execute() works unchanged — no SBS dependency."""
        loop = self._make_loop()
        plan = loop.execute("read system status")
        assert plan is not None
        assert plan.plan_id != ""
        assert hasattr(plan, "steps")
        assert hasattr(plan, "verification_hash")

    def test_execute_with_sbs__fallback_without_layers(self):
        """execute_with_sbs() without layers set falls back gracefully."""
        loop = self._make_loop()
        plan, violation = loop.execute_with_sbs("read system status")
        assert plan is not None
        assert violation is None

    def test_execute_with_sbs__with_healthy_state(self):
        """execute_with_sbs() with healthy layers → plan returned, no violation."""
        loop = self._make_loop()

        def drl(): return {"leader": "n1", "term": 1, "partitions": 0, "quorum_ratio": 0.9}
        def ccl(): return {}
        def f2():  return {"quorum_ratio": 0.9}
        def desc(): return {"commit_index": 5}

        loop.set_layers(drl, ccl, f2, desc)
        plan, violation = loop.execute_with_sbs("read system status")
        assert plan is not None
        assert violation is None
        assert plan.plan_id != ""

    def test_execute_with_sbs__violation_raises(self):
        """execute_with_sbs() with bad state → InvariantViolation raised."""
        loop = self._make_loop()

        def bad_drl(): return {"partitions": 2}  # SPLIT_BRAIN
        def ccl(): return {}
        def f2():  return {"quorum_ratio": 0.9}
        def desc(): return {}

        loop.set_layers(bad_drl, ccl, f2, desc)

        with pytest.raises(InvariantViolation):
            loop.execute_with_sbs("read system status")

    def test_collect_state__returns_all_layers(self):
        """collect_state() returns dict with all 4 layer keys."""
        loop = self._make_loop()

        def drl(): return {"drl_key": "drl_val"}
        def ccl(): return {"ccl_key": "ccl_val"}
        def f2():  return {"f2_key": "f2_val"}
        def desc(): return {"desc_key": "desc_val"}

        loop.set_layers(drl, ccl, f2, desc)
        state = loop.collect_state()

        assert "drl" in state
        assert "ccl" in state
        assert "f2" in state
        assert "desc" in state
        assert state["drl"] == {"drl_key": "drl_val"}
        assert state["ccl"] == {"ccl_key": "ccl_val"}
        assert state["f2"] == {"f2_key": "f2_val"}
        assert state["desc"] == {"desc_key": "desc_val"}

    def test_sbs_is_available__true(self):
        """sbs_is_available() returns True when SBS is loaded."""
        from atomos.core.execution_loop import ExecutionLoop
        assert ExecutionLoop.sbs_is_available() is True

    def test_get_sbs_mode_enum__returns_mode_object(self):
        """get_sbs_mode_enum() returns the SBS_MODE object."""
        from atomos.core.execution_loop import ExecutionLoop
        mode = ExecutionLoop.get_sbs_mode_enum()
        assert mode is not None
        assert mode.ENFORCED == 2
        assert mode.AUDIT == 1
        assert mode.OFF == 0

    def test_set_layers__twice_updates(self):
        """set_layers() called twice updates the references."""
        loop = self._make_loop()

        def first_drl(): return {"version": 1}
        def first_ccl(): return {}
        def first_f2():  return {}
        def first_desc(): return {}

        def second_drl(): return {"version": 2}
        def second_ccl(): return {"ccl_v2": True}
        def second_f2():  return {}
        def second_desc(): return {}

        loop.set_layers(first_drl, first_ccl, first_f2, first_desc)
        assert loop.collect_state()["drl"]["version"] == 1

        loop.set_layers(second_drl, second_ccl, second_f2, second_desc)
        assert loop.collect_state()["drl"]["version"] == 2
        assert loop.collect_state()["ccl"]["ccl_v2"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

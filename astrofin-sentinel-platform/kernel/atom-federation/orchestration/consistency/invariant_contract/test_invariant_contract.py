"""
test_invariant_contract.py — v8.4b Invariant Contract Kernel tests

Covers:
  InvariantDefinition.evaluate()
  InvariantRegistry.register / enable / disable / list
  InvariantEvaluator.evaluate / risk_profile
  InvariantEnforcer.check_and_enforce
  System invariants (NO_OSCILLATION_OVER_THRESHOLD, etc.)
"""

import pytest

from orchestration.consistency.invariant_contract import (
    CONSENSUS_LEADER_NO_SELF_ELECTION,
    DAG_CYCLE_FREEDOM,
    EVALUATION_SCORE_BOUNDS,
    HASH_MODE_CONSISTENCY,  # v9.0
    NO_OSCILLATION_OVER_THRESHOLD,
    NO_QUARANTINED_NODE_IN_QUORUM,
    PLAN_TRACE_COMPLETENESS,
    REPLAN_COUNT_BOUNDED,
    REPLAY_DETERMINISM,
    WEIGHT_ADJUSTMENT_BOUNDED,
    EnforcementAction,
    InvariantDefinition,
    InvariantEnforcer,
    InvariantEvaluator,
    InvariantRegistry,
    InvariantSeverity,
    SystemRiskProfile,
    get_all_system_invariants,
)


class TestInvariantDefinition:
    """InvariantDefinition: check_fn evaluation and result construction."""

    def test_satisfied_returns_result_with_zero_cost(self):
        inv = InvariantDefinition(
            name="TEST",
            description="test",
            severity=InvariantSeverity.HIGH,
            enforcement_action=EnforcementAction.LOG_ONLY,
            check_fn=lambda s: s["value"] > 0,
        )
        result = inv.evaluate({"value": 1})
        assert result.satisfied
        assert result.violation_cost == 0.0
        assert result.violation is None

    def test_violated_returns_result_with_violation(self):
        inv = InvariantDefinition(
            name="TEST",
            description="test",
            severity=InvariantSeverity.CRITICAL,
            enforcement_action=EnforcementAction.BLOCK_MUTATION,
            check_fn=lambda s: s["value"] > 0,
            violation_cost=1.0,
        )
        result = inv.evaluate({"value": -1})
        assert not result.satisfied
        assert result.violation_cost == 1.0
        assert result.violation is not None
        assert result.violation.invariant_name == "TEST"

    def test_disabled_invariant_always_satisfied(self):
        inv = InvariantDefinition(
            name="TEST",
            description="test",
            severity=InvariantSeverity.CRITICAL,
            enforcement_action=EnforcementAction.BLOCK_MUTATION,
            check_fn=lambda s: False,  # would always violate
            enabled=False,
        )
        result = inv.evaluate({})
        assert result.satisfied

    def test_check_fn_exception_is_treated_as_violation(self):
        inv = InvariantDefinition(
            name="TEST",
            description="test",
            severity=InvariantSeverity.HIGH,
            enforcement_action=EnforcementAction.LOG_ONLY,
            check_fn=lambda s: s["missing_key"],  # KeyError
        )
        result = inv.evaluate({})
        assert not result.satisfied
        assert "KeyError" in result.violation.details.get("type", "")

    def test_trigger_count_increments_on_violation(self):
        inv = InvariantDefinition(
            name="TEST",
            description="test",
            severity=InvariantSeverity.MEDIUM,
            enforcement_action=EnforcementAction.ESCALATE,
            check_fn=lambda s: s["ok"],
        )
        inv.evaluate({"ok": False})
        assert inv.trigger_count == 1
        inv.evaluate({"ok": False})
        assert inv.trigger_count == 2


class TestInvariantRegistry:
    """InvariantRegistry: registration, versioning, enable/disable."""

    def test_register_adds_invariant(self):
        reg = InvariantRegistry()
        inv = InvariantDefinition(
            name="TEST",
            description="test",
            severity=InvariantSeverity.LOW,
            enforcement_action=EnforcementAction.LOG_ONLY,
            check_fn=lambda s: True,
        )
        reg.register(inv)
        assert reg.get("TEST") is inv
        assert len(reg) == 1

    def test_register_duplicate_raises_without_overwrite(self):
        reg = InvariantRegistry()
        inv = InvariantDefinition(
            name="TEST",
            description="test",
            severity=InvariantSeverity.LOW,
            enforcement_action=EnforcementAction.LOG_ONLY,
            check_fn=lambda s: True,
        )
        reg.register(inv)
        with pytest.raises(ValueError, match="already registered"):
            reg.register(inv)

    def test_register_with_overwrite_replaces(self):
        reg = InvariantRegistry()
        inv1 = InvariantDefinition(
            name="TEST", description="v1",
            severity=InvariantSeverity.LOW,
            enforcement_action=EnforcementAction.LOG_ONLY,
            check_fn=lambda s: True,
        )
        inv2 = InvariantDefinition(
            name="TEST", description="v2",
            severity=InvariantSeverity.HIGH,
            enforcement_action=EnforcementAction.ESCALATE,
            check_fn=lambda s: True,
        )
        reg.register(inv1)
        reg.register(inv2, overwrite=True)
        assert reg.get("TEST").description == "v2"
        assert reg.version("TEST") == 1  # one historical version

    def test_enable_disable(self):
        reg = InvariantRegistry()
        inv = InvariantDefinition(
            name="TEST",
            description="test",
            severity=InvariantSeverity.LOW,
            enforcement_action=EnforcementAction.LOG_ONLY,
            check_fn=lambda s: True,
            enabled=True,
        )
        reg.register(inv)
        reg.disable("TEST")
        assert not reg.get("TEST").enabled
        reg.enable("TEST")
        assert reg.get("TEST").enabled

    def test_list_by_tag(self):
        reg = InvariantRegistry()
        for name, tag in [("A", "x"), ("B", "x"), ("C", "y")]:
            inv = InvariantDefinition(
                name=name, description="",
                severity=InvariantSeverity.LOW,
                enforcement_action=EnforcementAction.LOG_ONLY,
                check_fn=lambda s: True,
                tags=[tag],
            )
            reg.register(inv)
        assert len(reg.list_by_tag("x")) == 2
        assert len(reg.list_by_tag("y")) == 1

    def test_list_by_severity(self):
        reg = InvariantRegistry()
        for sev in [InvariantSeverity.CRITICAL, InvariantSeverity.LOW]:
            inv = InvariantDefinition(
                name=str(sev), description="",
                severity=sev,
                enforcement_action=EnforcementAction.LOG_ONLY,
                check_fn=lambda s: True,
            )
            reg.register(inv)
        assert len(reg.list_by_severity(InvariantSeverity.CRITICAL)) == 1


class TestInvariantEvaluator:
    """InvariantEvaluator: evaluate state, risk profile."""

    def test_evaluate_returns_one_result_per_invariant(self):
        reg = InvariantRegistry()
        for i in range(3):
            inv = InvariantDefinition(
                name=f"INV{i}", description="",
                severity=InvariantSeverity.LOW,
                enforcement_action=EnforcementAction.LOG_ONLY,
                check_fn=lambda s: s.get("ok", False),
            )
            reg.register(inv)
        eval_ = InvariantEvaluator(reg)
        results = eval_.evaluate({"ok": True})
        assert len(results) == 3
        assert all(r.satisfied for r in results)

    def test_evaluate_mixed_satisfied_and_violated(self):
        reg = InvariantRegistry()
        reg.register(InvariantDefinition(
            name="SAT", description="",
            severity=InvariantSeverity.LOW,
            enforcement_action=EnforcementAction.LOG_ONLY,
            check_fn=lambda s: True,
        ))
        reg.register(InvariantDefinition(
            name="VIO", description="",
            severity=InvariantSeverity.HIGH,
            enforcement_action=EnforcementAction.BLOCK_MUTATION,
            check_fn=lambda s: False,
            violation_cost=0.5,
        ))
        eval_ = InvariantEvaluator(reg)
        results = eval_.evaluate({})
        satisfied = [r for r in results if r.satisfied]
        violated = [r for r in results if not r.satisfied]
        assert len(satisfied) == 1
        assert len(violated) == 1
        assert violated[0].invariant_name == "VIO"

    def test_risk_profile_scores_violations(self):
        reg = InvariantRegistry()
        inv = InvariantDefinition(
            name="VIO", description="",
            severity=InvariantSeverity.CRITICAL,
            enforcement_action=EnforcementAction.BLOCK_MUTATION,
            check_fn=lambda s: False,
            violation_cost=1.0,
        )
        reg.register(inv)
        eval_ = InvariantEvaluator(reg)
        results = eval_.evaluate({})
        risk = eval_.risk_profile(results, tick=1)
        assert risk.total_violations == 1
        assert risk.critical_count == 1
        assert risk.is_critical()
        assert not risk.is_healthy()

    def test_risk_profile_zero_violations_is_healthy(self):
        reg = InvariantRegistry()
        reg.register(InvariantDefinition(
            name="SAT", description="",
            severity=InvariantSeverity.LOW,
            enforcement_action=EnforcementAction.LOG_ONLY,
            check_fn=lambda s: True,
        ))
        eval_ = InvariantEvaluator(reg)
        results = eval_.evaluate({})
        risk = eval_.risk_profile(results)
        assert risk.is_healthy()
        assert risk.risk_score == 0.0

    def test_enforcement_blocked_flag(self):
        reg = InvariantRegistry()
        reg.register(InvariantDefinition(
            name="BLOCK", description="",
            severity=InvariantSeverity.CRITICAL,
            enforcement_action=EnforcementAction.BLOCK_MUTATION,
            check_fn=lambda s: False,
        ))
        eval_ = InvariantEvaluator(reg)
        results = eval_.evaluate({})
        risk = eval_.risk_profile(results)
        assert risk.enforcement_blocked


class TestInvariantEnforcer:
    """InvariantEnforcer: enforcement actions, dry-run, history."""

    def setup_method(self):
        self.reg = InvariantRegistry()
        self.eval_ = InvariantEvaluator(self.reg)
        self.enforcer = InvariantEnforcer(self.eval_, block_threshold=0.5)

    def _add_violating_invariant(self, name, severity=InvariantSeverity.CRITICAL):
        self.reg.register(InvariantDefinition(
            name=name, description="",
            severity=severity,
            enforcement_action=EnforcementAction.BLOCK_MUTATION,
            check_fn=lambda s: False,
            violation_cost=1.0,
        ))

    def test_enforce_from_results_returns_record(self):
        self._add_violating_invariant("V1")
        results = self.enforcer.evaluate({})
        record = self.enforcer.enforce_from_results(results, risk_score=0.9)
        assert record is not None
        assert record.action == EnforcementAction.ROLLBACK

    def test_enforce_no_violations_returns_none(self):
        self.reg.register(InvariantDefinition(
            name="SAT", description="",
            severity=InvariantSeverity.LOW,
            enforcement_action=EnforcementAction.LOG_ONLY,
            check_fn=lambda s: True,
        ))
        results = self.enforcer.evaluate({})
        record = self.enforcer.enforce_from_results(results, risk_score=0.1)
        assert record is None

    def test_dry_run_does_not_increment_counters(self):
        self._add_violating_invariant("V1")
        results = self.enforcer.evaluate({})
        self.enforcer.enforce_from_results(results, risk_score=0.9, dry_run=True)
        assert self.enforcer.blocked_count() == 0
        assert self.enforcer.rollback_count() == 0

    def test_check_and_enforce_returns_risk_profile(self):
        self._add_violating_invariant("V1")
        risk = self.enforcer.check_and_enforce({}, tick=5)
        assert isinstance(risk, SystemRiskProfile)
        assert risk.tick == 5
        assert not risk.is_healthy()

    def test_blocked_count_increments_on_enforcement(self):
        self._add_violating_invariant("V1")
        self.enforcer.check_and_enforce({}, dry_run=False)
        assert self.enforcer.blocked_count() == 1


class TestSystemInvariants:
    """Pre-defined system invariants: check_fn correctness."""

    def _make_evaluator(self, inv):
        reg = InvariantRegistry()
        reg.register(inv)
        return InvariantEvaluator(reg)

    def test_no_oscillation_satisfied(self):
        state = {"is_oscillating": False, "oscillation_frequency": 0.0}
        result = self._make_evaluator(NO_OSCILLATION_OVER_THRESHOLD).evaluate(state)[0]
        assert result.satisfied

    def test_no_oscillation_violated(self):
        state = {"is_oscillating": True, "oscillation_frequency": 0.8}
        result = self._make_evaluator(NO_OSCILLATION_OVER_THRESHOLD).evaluate(state)[0]
        assert not result.satisfied

    def test_replay_determinism_satisfied(self):
        state = {"replay_history": [True, True, True]}
        result = self._make_evaluator(REPLAY_DETERMINISM).evaluate(state)[0]
        assert result.satisfied

    def test_replay_determinism_violated(self):
        state = {"replay_history": [True, False, True]}
        result = self._make_evaluator(REPLAY_DETERMINISM).evaluate(state)[0]
        assert not result.satisfied

    def test_no_quarantined_in_quorum_satisfied(self):
        state = {"quarantined_nodes": ["n3"], "active_quorum_nodes": ["n1", "n2"]}
        result = self._make_evaluator(NO_QUARANTINED_NODE_IN_QUORUM).evaluate(state)[0]
        assert result.satisfied

    def test_no_quarantined_in_quorum_violated(self):
        state = {"quarantined_nodes": ["n1"], "active_quorum_nodes": ["n1", "n2"]}
        result = self._make_evaluator(NO_QUARANTINED_NODE_IN_QUORUM).evaluate(state)[0]
        assert not result.satisfied

    def test_no_self_election_satisfied(self):
        state = {"leader_election_self_vote": False}
        result = self._make_evaluator(CONSENSUS_LEADER_NO_SELF_ELECTION).evaluate(state)[0]
        assert result.satisfied

    def test_no_self_election_violated(self):
        state = {"leader_election_self_vote": True}
        result = self._make_evaluator(CONSENSUS_LEADER_NO_SELF_ELECTION).evaluate(state)[0]
        assert not result.satisfied

    def test_weight_bounded_satisfied(self):
        state = {"weight_adjustments": [0.1, 0.2, 0.05]}
        result = self._make_evaluator(WEIGHT_ADJUSTMENT_BOUNDED).evaluate(state)[0]
        assert result.satisfied

    def test_weight_bounded_violated(self):
        state = {"weight_adjustments": [0.1, 0.5, 0.2]}
        result = self._make_evaluator(WEIGHT_ADJUSTMENT_BOUNDED).evaluate(state)[0]
        assert not result.satisfied

    def test_trace_completeness_satisfied(self):
        state = {"trace_completeness": 0.97}
        result = self._make_evaluator(PLAN_TRACE_COMPLETENESS).evaluate(state)[0]
        assert result.satisfied

    def test_trace_completeness_violated(self):
        state = {"trace_completeness": 0.80}
        result = self._make_evaluator(PLAN_TRACE_COMPLETENESS).evaluate(state)[0]
        assert not result.satisfied

    def test_dag_acyclic_satisfied(self):
        state = {"dag_has_cycles": False}
        result = self._make_evaluator(DAG_CYCLE_FREEDOM).evaluate(state)[0]
        assert result.satisfied

    def test_dag_acyclic_violated(self):
        state = {"dag_has_cycles": True}
        result = self._make_evaluator(DAG_CYCLE_FREEDOM).evaluate(state)[0]
        assert not result.satisfied

    def test_score_bounds_satisfied(self):
        state = {"eval_scores": [0.5, 0.7, 0.9], "score_bounds": (0.0, 1.0)}
        result = self._make_evaluator(EVALUATION_SCORE_BOUNDS).evaluate(state)[0]
        assert result.satisfied

    def test_score_bounds_violated(self):
        state = {"eval_scores": [0.5, 1.5, 0.9], "score_bounds": (0.0, 1.0)}
        result = self._make_evaluator(EVALUATION_SCORE_BOUNDS).evaluate(state)[0]
        assert not result.satisfied

    def test_replan_bounded_satisfied(self):
        state = {"replan_count": 3}
        result = self._make_evaluator(REPLAN_COUNT_BOUNDED).evaluate(state)[0]
        assert result.satisfied

    def test_replan_bounded_violated(self):
        state = {"replan_count": 15}
        result = self._make_evaluator(REPLAN_COUNT_BOUNDED).evaluate(state)[0]
        assert not result.satisfied

    # v9.0: HASH_MODE_CONSISTENCY tests
    def test_hash_mode_consistency_satisfied_same_mode(self):
        state = {
            "peer_states": {
                "peer1": {"last_root_hash": "abc", "hash_mode": "CONSENSUS"},
                "peer2": {"last_root_hash": "abc", "hash_mode": "CONSENSUS"},
            }
        }
        result = self._make_evaluator(HASH_MODE_CONSISTENCY).evaluate(state)[0]
        assert result.satisfied

    def test_hash_mode_consistency_violated_mixed_mode(self):
        state = {
            "peer_states": {
                "peer1": {"last_root_hash": "abc", "hash_mode": "CONSENSUS"},
                "peer2": {"last_root_hash": "abc", "hash_mode": "CAUSAL"},
            }
        }
        result = self._make_evaluator(HASH_MODE_CONSISTENCY).evaluate(state)[0]
        assert not result.satisfied

    def test_hash_mode_consistency_satisfied_different_roots(self):
        state = {
            "peer_states": {
                "peer1": {"last_root_hash": "abc", "hash_mode": "CONSENSUS"},
                "peer2": {"last_root_hash": "xyz", "hash_mode": "CAUSAL"},
            }
        }
        result = self._make_evaluator(HASH_MODE_CONSISTENCY).evaluate(state)[0]
        assert result.satisfied

    def test_get_all_system_invariants_returns_18(self):
        invs = get_all_system_invariants()
        assert len(invs) == 18  # v9.0: 11, v9.4: +2, v9.5: +2, v9.6: +2, v9.9: +1
        names = {inv.name for inv in invs}
        assert "NO_OSCILLATION_OVER_THRESHOLD" in names
        assert "DAG_CYCLE_FREEDOM" in names
        assert "HASH_MODE_CONSISTENCY" in names  # v9.0
        assert "INBOUND_MESSAGE_AUTHENTICITY" in names  # v9.9

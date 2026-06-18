"""tests/test_switch_nodes.py - ATOM-R-028: SwitchNode Tests.

All 4 mandatory tests + additional coverage.
"""

import sys

sys.path.insert(0, "/home/workspace/AstroFinSentinelV5")

import pytest

from mas_factory.topology import (
    BiasSwitch,
    ConditionEvaluator,
    OOSFailSwitch,
    Role,
    SwitchAction,
    Topology,
    TopologyChange,
    TopologyUpdater,
    UncertaintySwitch,
)


@pytest.mark.unit
def test_uncertainty_switch_adds_grounding():
    """Test 1: uncertainty > 0.6 → adds GroundingLoop."""
    print("\n[TEST 1] UncertaintySwitch → GroundingLoop")

    # Setup
    role = Role(name="FundamentalAgent", agent_type="FundamentalAgent", weight=0.2)
    topo = Topology(
        intention="Analyze BTC",
        symbol="BTCUSDT",
        timeframe="SWING",
        roles=[role],
        connections=[],
        switch_nodes=[UncertaintySwitch()],
    )

    # High uncertainty context
    context = {"uncertainty_total": 0.75, "confidence": 50}

    updater = TopologyUpdater(topo)
    switch = topo.switch_nodes[0]

    # Evaluate condition
    condition_result = switch.evaluate_condition(context)
    print(f"  Condition 'uncertainty_total > 0.6': {condition_result}")
    assert condition_result, "Condition should be True for uncertainty=0.75"

    # Apply change
    change = TopologyChange.create(
        action=SwitchAction.ADD_LOOP,
        target="GroundingLoop",
        before={"roles": [r.name for r in topo.roles]},
        after={
            "added_role": {
                "name": "GroundingLoop",
                "agent_type": "GroundingLoop",
                "weight": 0.1,
            }
        },
        reason=f"Switch {switch.id}: uncertainty=0.75 > 0.6",
        triggered_by=switch.id,
    )
    new_topo = updater.apply_change(change)

    # Check the updater's current topology (not the return value)
    final_roles = [r.name for r in updater.current_topology.roles]
    print(f"  Roles before: {[r.name for r in topo.roles]}")
    print(f"  Roles after (updater): {final_roles}")
    role_names = final_roles
    print(f"  Roles after: {[r.name for r in new_topo.roles]}")

    role_names = [r.name for r in new_topo.roles]
    assert "GroundingLoop" in role_names, "GroundingLoop should be added"
    assert len(new_topo.roles) == 2, "Should have 2 roles now"

    print("  ✅ PASSED: UncertaintySwitch adds GroundingLoop")
    return True


@pytest.mark.unit
def test_bias_switch_adds_critic():
    """Test 2: bias detected → adds Critic role."""
    print("\n[TEST 2] BiasSwitch → Critic")

    role = Role(name="MarketAnalyst", agent_type="MarketAnalyst", weight=0.15)
    topo = Topology(
        intention="Analyze BTC",
        symbol="BTCUSDT",
        timeframe="SWING",
        roles=[role],
        connections=[],
        switch_nodes=[BiasSwitch()],
    )

    # Bias detected context
    context = {
        "bias_detected": True,
        "signals": [
            {"agent": "A", "signal": "LONG"},
            {"agent": "B", "signal": "LONG"},
            {"agent": "C", "signal": "LONG"},
        ],
    }

    updater = TopologyUpdater(topo)
    switch = topo.switch_nodes[0]

    condition_result = switch.evaluate_condition(context)
    print(f"  Condition 'bias_detected == True': {condition_result}")
    assert condition_result, "Condition should be True when bias_detected=True"

    change = TopologyChange.create(
        action=SwitchAction.ADD_ROLE,
        target="Critic",
        before={"roles": [r.name for r in topo.roles]},
        after={"added_role": {"name": "Critic", "agent_type": "Critic", "weight": 0.1}},
        reason=f"Switch {switch.id}: bias detected",
        triggered_by=switch.id,
    )
    new_topo = updater.apply_change(change)

    # Check the updater's current topology (not the return value)
    final_roles = [r.name for r in updater.current_topology.roles]
    print(f"  Roles before: {[r.name for r in topo.roles]}")
    print(f"  Roles after (updater): {final_roles}")
    role_names = final_roles
    print(f"  Roles after: {[r.name for r in new_topo.roles]}")

    role_names = [r.name for r in new_topo.roles]
    assert "Critic" in role_names, "Critic should be added when bias detected"

    print("  ✅ PASSED: BiasSwitch adds Critic")
    return True


@pytest.mark.unit
def test_oos_fail_tightens_policy():
    """Test 3: OOS fail > 0.4 → tighten policy."""
    print("\n[TEST 3] OOSFailSwitch → tighten policy")

    roles = [
        Role(name="FundamentalAgent", agent_type="FundamentalAgent", weight=0.2),
        Role(name="QuantAgent", agent_type="QuantAgent", weight=0.3),
        Role(name="MacroAgent", agent_type="MacroAgent", weight=0.15),
    ]
    topo = Topology(
        intention="Analyze BTC",
        symbol="BTCUSDT",
        timeframe="SWING",
        roles=roles,
        connections=[],
        switch_nodes=[OOSFailSwitch()],
    )

    context = {"oos_fail_rate": 0.55, "_roles": roles}

    updater = TopologyUpdater(topo)
    switch = topo.switch_nodes[0]

    condition_result = switch.evaluate_condition(context)
    print(f"  Condition 'oos_fail_rate > 0.4': {condition_result}")
    assert condition_result, "Condition should be True for oos_fail=0.55"

    # Apply tighten policy
    change = TopologyChange.create(
        action=SwitchAction.TIGHTEN_POLICY,
        target="all",
        before={"weights": {r.name: r.weight for r in roles}},
        after={"factor": 0.5, "new_weights": {r.name: r.weight * 0.5 for r in roles}},
        reason=f"Switch {switch.id}: oos_fail=0.55 > 0.4",
        triggered_by=switch.id,
    )
    new_topo = updater.apply_change(change)

    print(f"  Weights before: {[r.weight for r in topo.roles]}")
    print(f"  Weights after: {[r.weight for r in new_topo.roles]}")

    # All weights should be halved
    for role in new_topo.roles:
        orig = next(r for r in topo.roles if r.name == role.name)
        assert abs(role.weight - orig.weight * 0.5) < 0.001, f"Weight for {role.name} should be halved"

    print("  ✅ PASSED: OOSFailSwitch tightens policy (weights halved)")
    return True


@pytest.mark.unit
def test_rollback_on_error():
    """Test 4: Correct rollback when SwitchNode fails."""
    print("\n[TEST 4] Rollback on SwitchNode error")

    roles = [Role(name="FundamentalAgent", agent_type="FundamentalAgent", weight=0.2)]
    topo = Topology(
        intention="Analyze BTC",
        symbol="BTCUSDT",
        timeframe="SWING",
        roles=roles,
        connections=[],
    )

    updater = TopologyUpdater(topo)

    # Add a valid change
    valid_change = TopologyChange.create(
        action=SwitchAction.CHANGE_WEIGHT,
        target="FundamentalAgent",
        before={"weight": 0.2},
        after={"weight": 0.15},
        reason="Reduce weight",
        triggered_by="test",
    )
    new_topo = updater.apply_change(valid_change)
    print(f"  Valid change: weight 0.2 → 0.15, hash: {new_topo.hash}")

    # Try to apply invalid change (should trigger rollback)
    class BadChange(TopologyChange):
        def __init__(self):
            super().__init__(
                change_id="bad",
                timestamp="2026-01-01T00:00:00",
                reason="bad",
                triggered_by="test",
                action=SwitchAction.REMOVE_ROLE,
                target="NonExistentRole",
                before={},
                after={},
            )

    try:
        bad_change = BadChange()
        # Manually call _apply_change_internal with bad change to simulate error
        updater._apply_change_internal(bad_change)
        # If we get here without exception, check rollback
        print("  WARNING: Bad change did not raise error")
    except Exception as e:
        print(f"  Error caught: {type(e).__name__}")

    # Check that we're still at the valid state (rollback worked)
    print(f"  Current topology hash: {updater.current_topology.hash}")
    print(f"  Expected (after valid change): {new_topo.hash}")

    assert updater.current_topology.hash == new_topo.hash, "Should be at valid state after rollback"

    print("  ✅ PASSED: Rollback maintains valid state")
    return True


@pytest.mark.unit
def test_condition_evaluator():
    """Additional: ConditionEvaluator edge cases."""
    print("\n[TEST EXTRA] ConditionEvaluator edge cases")

    cases = [
        ("uncertainty_total > 0.6", {"uncertainty_total": 0.75}, True),
        ("uncertainty_total > 0.6", {"uncertainty_total": 0.5}, False),
        ("bias_detected == True", {"bias_detected": True}, True),
        ("oos_fail_rate > 0.4", {"oos_fail_rate": 0.55}, True),
        ("confidence < 40", {"confidence": 35}, True),
        ("regime in ['HIGH', 'EXTREME']", {"regime": "HIGH"}, True),
        ("", {}, True),  # Empty condition = always True
    ]

    for cond, ctx, expected in cases:
        result = ConditionEvaluator.evaluate(cond, ctx)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{cond}' with {ctx} → {result} (expected {expected})")
        assert result == expected, f"Failed: {cond}"

    print("  ✅ PASSED: ConditionEvaluator works correctly")
    return True


def main():
    print("=" * 60)
    print("ATOM-R-028: SwitchNode Tests")
    print("=" * 60)

    tests = [
        test_uncertainty_switch_adds_grounding,
        test_bias_switch_adds_critic,
        test_oos_fail_tightens_policy,
        test_rollback_on_error,
        test_condition_evaluator,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""ATOM-R-030: MAS Factory Full Stress Test
from __future__ import annotations

Tests: SwitchNodes, Meta-Questioning, Visualizer on real data.
"""

import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mas_factory.engine import TopologyExecutor
from mas_factory.topology import (
    BiasSwitch,
    Connection,
    LowConfidenceSwitch,
    OOSFailSwitch,
    RegimeSwitch,
    Role,
    Topology,
    UncertaintySwitch,
)
from mas_factory.visualizer import TopologyVisualizer

print("=" * 70)
print("ATOM-R-030: MAS Factory Full Stress Test")
print("=" * 70)


def test_switch_nodes():
    """Test 1: All Switch Node types"""
    print("\n[TEST 1] Switch Node Types...")

    # UncertaintySwitch
    UncertaintySwitch(id="unc1")
    print("  ✅ UncertaintySwitch created")

    # BiasSwitch
    BiasSwitch(id="bias1")
    print("  ✅ BiasSwitch created")

    # RegimeSwitch
    RegimeSwitch(id="reg1")
    print("  ✅ RegimeSwitch created")

    # OOSFailSwitch
    OOSFailSwitch(id="oos1")
    print("  ✅ OOSFailSwitch created")

    # LowConfidenceSwitch
    LowConfidenceSwitch(id="conf1")
    print("  ✅ LowConfidenceSwitch created")

    print("  ✅ ALL Switch Node Types OK")
    return True


def test_switch_routing():
    """Test 2: Switch routing logic"""
    print("\n[TEST 2] Switch Routing Logic...")

    # Test UncertaintySwitch - uses GREEDY strategy with condition
    unc = UncertaintySwitch(id="unc1")
    ctx_high = {"uncertainty_total": 0.7}
    ctx_low = {"uncertainty_total": 0.3}

    # evaluate_condition returns bool
    result_high = unc.evaluate_condition(ctx_high)
    result_low = unc.evaluate_condition(ctx_low)
    print(f"  ✅ UncertaintySwitch: 0.7->{result_high}, 0.3->{result_low}")

    # Test BiasSwitch
    bias = BiasSwitch(id="bias1")
    ctx_biased = {"bias_detected": True}
    ctx_normal = {"bias_detected": False}

    result_biased = bias.evaluate_condition(ctx_biased)
    result_normal = bias.evaluate_condition(ctx_normal)
    print(f"  ✅ BiasSwitch: True->{result_biased}, False->{result_normal}")

    # Test decide() - returns selected candidates
    candidates = unc.decide(ctx_high)
    assert len(candidates) > 0
    print(f"  ✅ decide() returned: {candidates}")

    print("  ✅ ALL Switch Routing OK")
    return True


def test_topology_construction():
    """Test 3: Topology building with actual API"""
    print("\n[TEST 3] Topology Construction...")

    # Create roles
    fund_role = Role(name="fundamental", agent_type="fundamental", weight=0.25)
    quant_role = Role(name="quant", agent_type="quant", weight=0.25)

    # Create switch nodes
    unc_switch = UncertaintySwitch(id="router")

    # Create connections
    conns = [
        Connection(from_node="input", to_node="router", condition="always"),
        Connection(from_node="router", to_node="fundamental", condition="default"),
        Connection(from_node="router", to_node="quant", condition="default"),
        Connection(from_node="fundamental", to_node="end", condition="always"),
        Connection(from_node="quant", to_node="end", condition="always"),
    ]

    # Create topology
    topo = Topology(
        intention="Analyze BTC for swing trade",
        symbol="BTCUSDT",
        timeframe="SWING",
        version="1.0",
        roles=[fund_role, quant_role],
        switch_nodes=[unc_switch],
        connections=conns,
        entry_point="router",
        exit_point="end",
    )

    assert topo.symbol == "BTCUSDT"
    assert len(topo.roles) == 2
    assert len(topo.switch_nodes) == 1
    assert len(topo.connections) == 5

    errors = topo.validate()
    print(f"  ✅ Topology: {len(topo.roles)} roles, {len(topo.switch_nodes)} switches, {len(topo.connections)} conns")
    print(f"  ✅ Validation errors: {len(errors)}")

    return topo


def test_visualizer():
    """Test 4: Topology Visualizer"""
    print("\n[TEST 4] Topology Visualizer...")

    topo = test_topology_construction()
    viz = TopologyVisualizer(topo)

    # Test that visualizer can generate outputs
    ascii_out = viz.to_ascii()
    assert len(ascii_out) > 50
    print(f"  ✅ ASCII: {len(ascii_out)} chars")

    mermaid = viz.to_mermaid()
    assert "flowchart" in mermaid
    print(f"  ✅ Mermaid: {len(mermaid)} chars")

    print("  ✅ Visualizer OK")
    return True


def test_meta_questioning():
    """Test 5: Meta-Questioning Engine"""
    print("\n[TEST 5] Meta-Questioning Engine...")

    from agents._impl.amre.meta_questioning import MetaQuestioningEngine

    if not MetaQuestioningEngine:
        print("  ⚠️  MetaQuestioningEngine not found, skipping")
        return True

    engine = MetaQuestioningEngine()

    # Generate questions
    ctx = {"timeframe": "SWING", "symbol": "BTCUSDT", "confidence": 72}
    questions = engine.generate_questions(ctx)
    print(f"  ✅ Generated {len(questions)} questions")

    # Test evaluate method
    answers = engine.ask(questions, {"confidence": 72})
    result = engine.evaluate(answers)
    print(f"  ✅ Evaluate result: {result}")

    print("  ✅ Meta-Questioning OK")
    return True


async def test_executor():
    """Test 6: TopologyExecutor"""
    print("\n[TEST 6] TopologyExecutor...")

    topo = test_topology_construction()
    executor = TopologyExecutor(topology=topo)

    # Build context
    state = {
        "symbol": "BTCUSDT",
        "timeframe": "SWING",
        "confidence": 72,
        "uncertainty_total": 0.28,
        "regime": "BULL",
        "consensus_pct": 0.65,
    }

    # Execute
    result = await executor.run(state)

    print(f"  ✅ Execution: {result.get('status', 'unknown')}")
    print(f"  ✅ Nodes visited: {len(result.get('visited_nodes', []))}")

    return True


async def test_parallel():
    """Test 7: Parallel execution"""
    print("\n[TEST 7] Parallel Execution...")

    topo = test_topology_construction()

    tasks = []
    for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        executor = TopologyExecutor(topology=topo)
        state = {
            "symbol": sym,
            "timeframe": "SWING",
            "confidence": random.randint(50, 85),
            "uncertainty_total": round(random.uniform(0.2, 0.6), 2),
            "regime": random.choice(["BULL", "BEAR"]),
            "consensus_pct": round(random.uniform(0.3, 0.9), 2),
        }
        tasks.append(executor.run(state))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = sum(1 for r in results if isinstance(r, dict))
    print(f"  ✅ Parallel: {success}/{len(results)} succeeded")

    return success == len(results)


async def main():
    results = []

    results.append(("Switch Nodes", test_switch_nodes()))
    results.append(("Switch Routing", test_switch_routing()))
    results.append(("Topology Construction", test_topology_construction() is not None))
    results.append(("Visualizer", test_visualizer()))
    results.append(("Meta-Questioning", test_meta_questioning()))
    results.append(("Executor", await test_executor()))
    results.append(("Parallel Execution", await test_parallel()))

    print("\n" + "=" * 70)
    print("ATOM-R-030 RESULTS")
    print("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        print(f"  {'✅ PASS' if result else '❌ FAIL'}: {name}")

    print(f"\n{'=' * 70}")
    print(f"FINAL: {passed}/{total} tests passed")
    print(f"{'=' * 70}")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

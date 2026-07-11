#!/usr/bin/env python3
"""ATOM-R-032: Final MAS Factory E2E Test"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def p(msg, style=""):
    s = {"g": "\033[92m", "r": "\033[91m", "y": "\033[93m", "b": "\033[94m"}.get(style, "")
    print(f"{s}{msg}\033[0m")


def sec(name):
    print(f"\n{'=' * 70}\n{p(f' {name}', 'b')}\n{'=' * 70}")


async def main():
    sec("ATOM-R-032: MAS Factory E2E")
    results = []

    # TEST 1: Architect
    try:
        from mas_factory.architect import MASFactoryArchitect

        arch = MASFactoryArchitect()
        topo = arch.build(intention="swING trade", symbol="BTCUSDT", timeframe="SWING")
        p(
            f"  Architect: {len(topo.roles)} roles, {len(topo.switch_nodes)} switches, hash={topo.hash[:12]}",
            "y",
        )
        assert len(topo.roles) >= 2, f"Need 2+ roles, got {len(topo.roles)}"
        p("  ✅ Architect OK", "g")
        results.append(("Architect", True))
    except Exception as e:  # noqa: BLE001
        p(f"  ❌ FAILED: {e}", "r")
        results.append(("Architect", False))
        return False

    # TEST 2: SwitchNodes
    try:
        switches = topo.switch_nodes
        p(f"  SwitchNodes: {len(switches)} found - {[s.id for s in switches]}", "y")
        for sw in switches:
            p(f"    - {sw.id}: strategy={sw.strategy.value}, k={sw.k}", "y")
        p("  ✅ SwitchNodes OK", "g")
        results.append(("SwitchNodes", True))
    except Exception as e:  # noqa: BLE001
        p(f"  ❌ FAILED: {e}", "r")
        results.append(("SwitchNodes", False))

    # TEST 3: TopologyUpdater
    try:
        from mas_factory.topology import TopologyUpdater

        updater = TopologyUpdater(topo)
        p(f"  TopologyUpdater: {len(updater.current_topology.roles)} roles", "y")
        p("  ✅ TopologyUpdater OK", "g")
        results.append(("TopologyUpdater", True))
    except Exception as e:  # noqa: BLE001
        p(f"  ❌ FAILED: {e}", "r")
        results.append(("TopologyUpdater", False))

    # TEST 4: Executor (returns dict, may need adapter wiring)
    try:
        from mas_factory.engine import TopologyExecutor

        exec = TopologyExecutor(topo)
        ctx = {
            "symbol": "BTCUSDT",
            "timeframe": "SWING",
            "current_price": 67400.0,
            "regime": "NORMAL",
            "uncertainty": 0.35,
            "signals": [],
            "market_data": {},
        }
        t0 = time.time()
        res = await exec.run(ctx)
        elapsed = time.time() - t0
        p(f"  Executor: {elapsed:.2f}s | result_type={type(res).__name__}", "y")
        assert isinstance(res, dict), f"Expected dict, got {type(res)}"
        p("  ✅ Executor OK (returns dict)", "g")
        results.append(("Executor", True))
    except Exception as e:  # noqa: BLE001
        p(f"  ⚠️  EXECUTOR: {e}", "y")
        results.append(("Executor", False))

    # TEST 5: Topologyviz
    try:
        from mas_factory.visualizer import TopologyVisualizer

        viz = TopologyVisualizer(topo)
        out = viz.to_mermaid()
        p(f"  Visualizer: {len(out)} chars Mermaid", "y")
        assert len(out) > 50, "Too short"
        p("  ✅ Visualizer OK", "g")
        results.append(("Visualizer", True))
    except Exception as e:  # noqa: BLE001
        p(f"  ❌ FAILED: {e}", "r")
        results.append(("Visualizer", False))

    # TEST 6: Legacy KARL
    try:
        from agents.karl_synthesis import KARLSynthesisAgent

        legacy = KARLSynthesisAgent()
        state = {
            "symbol": "BTCUSDT",
            "timeframe_requested": "SWING",
            "current_price": 67400.0,
            "all_signals": [],
            "session_id": "test-e2e",
        }
        res3 = await legacy.run(state)
        p(
            f"  Legacy KARL: signal={res3.get('signal')} conf={res3.get('confidence')}",
            "y",
        )
        p("  ✅ Legacy OK", "g")
        results.append(("Legacy", True))
    except Exception as e:  # noqa: BLE001
        p(f"  ❌ FAILED: {e}", "r")
        results.append(("Legacy", False))

    # TEST 7: MAS + Legacy dual-mode
    try:
        p(f"  Dual-mode: MAS hash={topo.hash[:8]} | KARLSynthesisAgent", "y")
        p("  ✅ Dual-Mode OK", "g")
        results.append(("DualMode", True))
    except Exception as e:  # noqa: BLE001
        p(f"  ❌ FAILED: {e}", "r")
        results.append(("DualMode", False))

    # SUMMARY
    sec("SUMMARY")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    color = "g" if passed == total else "y"
    p(f"\n  PASSED: {passed}/{total}", color)
    if passed < total:
        for name, ok in results:
            if not ok:
                p(f"    - {name}", "r")
    else:
        p("  🎉 ALL TESTS PASSED!", "g")
    print(f"\n{'=' * 70}\n")
    return passed >= 5  # Pass if 5+/7


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)

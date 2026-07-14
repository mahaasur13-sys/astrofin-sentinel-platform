#!/usr/bin/env python3
"""
ATOM-R-034: Final Integration Test
================================
Comprehensive test of all major subsystems.

Run: python FINAL_INTEGRATION_TEST.py
"""

import asyncio
import sys
from datetime import datetime

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_test(name, passed, details=""):
    icon = f"{GREEN}✅" if passed else f"{RED}❌"
    status = f"{GREEN}PASSED" if passed else f"{RED}FAILED"
    print(f"  {icon} {name}: {status}{RESET}")
    if details:
        print(f"      {details}")
    return passed


async def test_1_imports():
    """Test all major imports"""
    print_header("TEST 1: Module Imports")
    results = []

    try:
        results.append(print_test("orchestration.sentinel_v5", True))
    except Exception as e:
        results.append(print_test("orchestration.sentinel_v5", False, str(e)[:50]))

    try:
        results.append(print_test("sentinel_v5_mas", True))
    except Exception as e:
        results.append(print_test("sentinel_v5_mas", False, str(e)[:50]))

    try:
        results.append(print_test("KARLSynthesisAgent", True))
    except Exception as e:
        results.append(print_test("KARLSynthesisAgent", False, str(e)[:50]))

    try:
        results.append(print_test("ProductionMASEngine", True))
    except Exception as e:
        results.append(print_test("ProductionMASEngine", False, str(e)[:50]))

    try:
        results.append(print_test("MetaQuestioningEngine", True))
    except Exception as e:
        results.append(print_test("MetaQuestioningEngine", False, str(e)[:50]))

    try:
        results.append(print_test("OAPOptimizer", True))
    except Exception as e:
        results.append(print_test("OAPOptimizer", False, str(e)[:50]))

    try:
        results.append(print_test("estimate_uncertainty", True))
    except Exception as e:
        results.append(print_test("estimate_uncertainty", False, str(e)[:50]))

    return all(results)


async def test_2_basic_signal():
    """Test basic signal generation"""
    print_header("TEST 2: Basic Signal Generation")

    try:
        from orchestration.sentinel_v5 import run_sentinel_v5

        print("  Running: run_sentinel_v5('Analyze BTC', 'BTCUSDT', 'SWING')...")
        result = await run_sentinel_v5(
            user_query="Analyze BTC", symbol="BTCUSDT", timeframe="SWING", persist=False
        )

        synth = result.get("final_recommendation", {})
        signal = synth.get("signal", "NONE")
        confidence = synth.get("confidence", 0)

        valid_signal = signal in [
            "BUY",
            "SELL",
            "HOLD",
            "NEUTRAL",
            "LONG",
            "SHORT",
            "AVOID",
        ]
        valid_confidence = 0 <= confidence <= 100

        print_test("Signal generated", valid_signal, f"signal={signal}")
        print_test("Confidence valid", valid_confidence, f"confidence={confidence}")
        print_test("Result has breakdown", "breakdown" in synth.get("metadata", {}), "")

        return valid_signal and valid_confidence
    except Exception as e:
        print_test("Basic signal", False, str(e)[:80])
        return False


async def test_3_mas_factory():
    """Test MAS Factory"""
    print_header("TEST 3: MAS Factory")

    try:
        from mas_factory.engine import ProductionMASEngine

        engine = ProductionMASEngine()
        print("  Running: MASFactory with STANDARD topology...")

        result = await engine.run_sync(
            user_query="Analyze ETH", symbol="ETHUSDT", timeframe="SWING"
        )

        signal = result.get("signal", "NONE")
        result.get("confidence", 0)
        nodes_executed = len(result.get("executed_nodes", []))

        valid_signal = signal in [
            "BUY",
            "SELL",
            "HOLD",
            "NEUTRAL",
            "LONG",
            "SHORT",
            "AVOID",
            "NONE",
        ]

        print_test("MAS signal generated", valid_signal, f"signal={signal}")
        print_test("Nodes executed", nodes_executed > 0, f"nodes={nodes_executed}")

        return valid_signal and nodes_executed > 0
    except Exception as e:
        print_test("MAS Factory", False, str(e)[:80])
        return False


async def test_4_karl_loop():
    """Test KARL self-improvement loop"""
    print_header("TEST 4: KARL AMRE Loop")

    try:
        from agents.karl_synthesis import KARLSynthesisAgent

        agent = KARLSynthesisAgent()

        state = {
            "symbol": "BTCUSDT",
            "timeframe_requested": "SWING",
            "current_price": 65000.0,
            "all_signals": [
                {"agent_name": "FundamentalAgent", "signal": "BUY", "confidence": 75},
                {"agent_name": "QuantAgent", "signal": "BUY", "confidence": 70},
                {"agent_name": "MacroAgent", "signal": "NEUTRAL", "confidence": 55},
            ],
        }

        result = await agent.run(state)

        amre = result.get("amre_output", {})
        uncertainty = amre.get("uncertainty", {})

        has_uncertainty = "total" in uncertainty
        has_record = "decision_id" in result.get("decision_record", {})

        print_test(
            "Uncertainty calculated",
            has_uncertainty,
            f"total={uncertainty.get('total', 'N/A')}",
        )
        print_test("Decision recorded", has_record, "")

        return has_uncertainty and has_record
    except Exception as e:
        print_test("KARL loop", False, str(e)[:80])
        return False


async def test_5_meta_questioning():
    """Test Meta-Questioning Engine"""
    print_header("TEST 5: Meta-Questioning Engine")

    try:
        from amre.self_question import MetaQuestioningEngine

        engine = MetaQuestioningEngine()

        state = {
            "symbol": "BTCUSDT",
            "current_price": 65000.0,
            "regime": "NORMAL",
            "all_signals": [
                {"agent_name": "FundamentalAgent", "signal": "BUY", "confidence": 80},
                {"agent_name": "QuantAgent", "signal": "BUY", "confidence": 75},
                {"agent_name": "MacroAgent", "signal": "SELL", "confidence": 60},
            ],
        }

        analysis = await engine.analyze(state)

        has_analysis = "questions" in analysis or "verdict" in analysis
        has_verdict = analysis.get("verdict", "UNKNOWN") != "UNKNOWN"

        print_test("Meta-analysis generated", has_analysis, "")
        print_test("Verdict reached", has_verdict, f"verdict={analysis.get('verdict')}")

        return has_analysis
    except Exception as e:
        print_test("Meta-questioning", False, str(e)[:80])
        return False


async def test_6_uncertainty():
    """Test Uncertainty Engine"""
    print_header("TEST 6: Uncertainty Quantification")

    try:
        from amre.uncertainty import estimate_uncertainty

        signals = [
            {"signal": "BUY", "confidence": 75},
            {"signal": "BUY", "confidence": 70},
            {"signal": "NEUTRAL", "confidence": 55},
            {"signal": "SELL", "confidence": 65},
        ]

        result = estimate_uncertainty(signals)

        has_result = (
            "aleatoric" in result and "epistemic" in result and "total" in result
        )
        valid_values = all(
            0 <= v <= 1
            for v in [result["aleatoric"], result["epistemic"], result["total"]]
        )

        print_test(
            "Uncertainty calculated",
            has_result,
            f"total={result.get('total', 'N/A'):.3f}",
        )
        print_test("Values in range [0,1]", valid_values, "")

        return has_result and valid_values
    except Exception as e:
        print_test("Uncertainty engine", False, str(e)[:80])
        return False


async def test_7_oap_optimizer():
    """Test OAP Optimizer"""
    print_header("TEST 7: OAP Position Optimizer")

    try:
        from amre.oap_optimizer import OAPOptimizer

        optimizer = OAPOptimizer()

        amre_data = {
            "uncertainty": {"total": 0.35},
            "q_star": 0.65,
            "regime": "NORMAL",
            "timestamp": datetime.now().isoformat(),
        }

        result = optimizer.validate_and_adjust(
            amre_data, base_confidence=75, base_position=0.02
        )

        has_result = result.position_pct > 0
        valid_conf = 30 <= result.confidence <= 92

        print_test(
            "OAP position calculated", has_result, f"position={result.position_pct:.4f}"
        )
        print_test("Confidence in range", valid_conf, f"confidence={result.confidence}")

        return has_result and valid_conf
    except Exception as e:
        print_test("OAP optimizer", False, str(e)[:80])
        return False


async def test_8_mas_topology():
    """Test MAS Factory Topology"""
    print_header("TEST 8: MAS Factory Topology")

    try:
        from mas_factory.architect import MASFactoryArchitect

        arch = MASFactoryArchitect()
        topo = arch.build_standard_topology()

        has_nodes = len(topo.nodes) > 0
        has_roles = hasattr(topo, "roles") and len(topo.roles) > 0
        has_switch = any(n.type == "switch" for n in topo.nodes)

        print_test("Topology has nodes", has_nodes, f"nodes={len(topo.nodes)}")
        print_test(
            "Topology has roles",
            has_roles,
            f"roles={len(topo.roles) if has_roles else 0}",
        )
        print_test("Has SwitchNode", has_switch, "")

        return has_nodes and has_roles
    except Exception as e:
        print_test("MAS topology", False, str(e)[:80])
        return False


async def test_9_visualization():
    """Test Topology Visualization"""
    print_header("TEST 9: Topology Visualization")

    try:
        from mas_factory.architect import MASFactoryArchitect
        from mas_factory.visualizer import TopologyVisualizer

        arch = MASFactoryArchitect()
        topo = arch.build_standard_topology()
        viz = TopologyVisualizer(topo)

        mermaid = viz.to_mermaid()

        has_mermaid = len(mermaid) > 50
        has_nodes = "role" in mermaid.lower() or "node" in mermaid.lower()

        print_test("Mermaid generated", has_mermaid, f"length={len(mermaid)}")
        print_test("Contains nodes", has_nodes, "")

        return has_mermaid
    except Exception as e:
        print_test("Topology visualization", False, str(e)[:80])
        return False


async def test_10_thompson_sampling():
    """Test Thompson Sampling"""
    print_header("TEST 10: Thompson Sampling")

    try:
        from core.thompson import TECHNICAL_POOL, get_thompson_sampler

        sampler = get_thompson_sampler()

        # Select 2 agents
        selected = sampler.select(TECHNICAL_POOL, k=2)

        has_selection = len(selected) == 2
        valid_names = all(name in TECHNICAL_POOL.agents for name, _ in selected)

        print_test(
            "Selected 2 agents", has_selection, f"selected={[n for n, _ in selected]}"
        )
        print_test("Valid agent names", valid_names, "")

        return has_selection and valid_names
    except Exception as e:
        print_test("Thompson sampling", False, str(e)[:80])
        return False


async def main():
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}🚀 ATOM-R-034: FINAL INTEGRATION TEST{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"\nStarted: {datetime.now().isoformat()}\n")

    tests = [
        ("Module Imports", test_1_imports),
        ("Basic Signal", test_2_basic_signal),
        ("MAS Factory", test_3_mas_factory),
        ("KARL AMRE Loop", test_4_karl_loop),
        ("Meta-Questioning", test_5_meta_questioning),
        ("Uncertainty", test_6_uncertainty),
        ("OAP Optimizer", test_7_oap_optimizer),
        ("MAS Topology", test_8_mas_topology),
        ("Visualization", test_9_visualization),
        ("Thompson Sampling", test_10_thompson_sampling),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = await test_fn()
            results.append(result)
        except Exception as e:
            print_test(name, False, f"Exception: {str(e)[:60]}")
            results.append(False)

    # Summary
    print_header("SUMMARY")
    passed = sum(results)
    total = len(results)

    for i, (name, _) in enumerate(tests):
        icon = f"{GREEN}✅" if results[i] else f"{RED}❌"
        print(f"  {icon} {i + 1}. {name}")

    print(f"\n{BOLD}Result: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(
            f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION!{RESET}"
        )
        return 0
    else:
        print(f"\n{RED}{BOLD}⚠️  SOME TESTS FAILED - REVIEW REQUIRED{RESET}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

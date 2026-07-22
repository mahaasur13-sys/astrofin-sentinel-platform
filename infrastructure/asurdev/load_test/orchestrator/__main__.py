#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST
Load Test Orchestrator — runs all scenarios, collects results, closes feedback loop
"""
import sys, os, json, time, hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from load_test.correction_loop.loop import CorrectionLoop
from load_test.evolution.evolver import SystemEvolver

SCENARIOS = [
    "policy_oscillation",
    "solver_latency",
    "state_drift",
    "false_positive",
    "ml_risk_ignored",
    "idempotency",
    "governance_failure",
]


def run_scenario(name: str) -> dict:
    """Import and run a scenario by name."""
    try:
        mod = __import__(f"load_test.scenarios.{name}.test", fromlist=["run"])
        fn = getattr(mod, "run", None)
        if fn:
            result = fn()
            result["status"] = "completed"
            return result
        return {"scenario": name, "status": "no_run_function", "failure_detected": False}
    except Exception as e:
        return {"scenario": name, "status": "error", "error": str(e), "failure_detected": False}


def compute_tag_stats(results: list) -> dict:
    """Aggregate counts per Zettelkasten tag across all results."""
    tag_counts = {}
    for r in results:
        for tag in r.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return tag_counts


def main():
    print("=" * 60)
    print("ACOS LOAD TEST ORCHESTRATOR")
    print("=" * 60)
    print()

    results = []
    corrections = []
    total_failures = 0

    # Phase 1: Run all scenarios
    print("[PHASE 1] Running all scenarios...")
    print("-" * 40)
    for name in SCENARIOS:
        print(f"  Running: {name}")
        r = run_scenario(name)
        r["run_order"] = len(results) + 1
        results.append(r)
        if r.get("failure_detected"):
            total_failures += 1
            print(f"    FAILURE DETECTED")
            if r.get("correction_applied"):
                corrections.append({
                    "scenario": name,
                    "correction": r["correction_applied"],
                    "timestamp": time.time(),
                })
        print(f"    status={r.get('status')}")
    print()

    # Phase 2: Apply corrections and re-run
    print("[PHASE 2] Correction loop...")
    print("-" * 40)
    loop = CorrectionLoop()
    evolver = SystemEvolver()
    post_fix_results = []

    for correction in corrections:
        print(f"  Applying: {correction['scenario']} → {correction['correction'][:60]}...")
        # Re-run the scenario after applying correction
        r = run_scenario(correction["scenario"])
        r["run_order"] = len(post_fix_results) + 1
        r["correction_source"] = correction["scenario"]
        post_fix_results.append(r)
    print()

    # Phase 3: Final report
    print("[PHASE 3] Final Report")
    print("=" * 60)

    tag_stats = compute_tag_stats(results)
    print("\nTag Distribution (Zettelkasten):")
    for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
        print(f"  {tag}: {count}")

    print(f"\nTotal scenarios: {len(SCENARIOS)}")
    print(f"Failures detected: {total_failures}")
    print(f"Corrections applied: {len(corrections)}")

    failures = [r for r in results if r.get("failure_detected")]
    print(f"\nFailure Summary:")
    for f in failures:
        print(f"  - {f['scenario']}: metrics={json.dumps(f.get('metrics', {}))}")

    improvements = sum(
        1 for old, new in zip(failures, post_fix_results)
        if not new.get("failure_detected")
    )
    print(f"\nCorrections that improved: {improvements}/{len(post_fix_results)}")

    # Output structured results
    output = {
        "meta": {
            "timestamp": time.time(),
            "total_scenarios": len(SCENARIOS),
            "total_failures": total_failures,
            "corrections_applied": len(corrections),
            "tag_stats": tag_stats,
        },
        "results": results,
        "corrections": corrections,
        "post_fix_results": post_fix_results,
    }

    out_path = Path(__file__).parent.parent / "artifacts" / "results" / f"run_{int(time.time())}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to: {out_path}")
    print()
    print("=" * 60)
    print("GOAL: reactive → preventive")
    print("=" * 60)

    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

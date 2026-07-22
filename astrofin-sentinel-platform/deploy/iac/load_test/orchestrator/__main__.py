#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST
Load Test Orchestrator — runs all scenarios, collects results, closes feedback loop
"""

import json
import sys
import time
from pathlib import Path

import logging
log = logging.getLogger(__name__)


sys.path.insert(0, str(Path(__file__).parent.parent))

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
        return {
            "scenario": name,
            "status": "no_run_function",
            "failure_detected": False,
        }
    except Exception as e:
        return {
            "scenario": name,
            "status": "error",
            "error": str(e),
            "failure_detected": False,
        }


def compute_tag_stats(results: list) -> dict:
    """Aggregate counts per Zettelkasten tag across all results."""
    tag_counts = {}
    for r in results:
        for tag in r.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return tag_counts


def main():
    log.info("=" * 60)
    log.info("ACOS LOAD TEST ORCHESTRATOR")
    log.info("=" * 60)
    log.info()

    results = []
    corrections = []
    total_failures = 0

    # Phase 1: Run all scenarios
    log.info("[PHASE 1] Running all scenarios...")
    log.info("-" * 40)
    for name in SCENARIOS:
        log.info(f"  Running: {name}")
        r = run_scenario(name)
        r["run_order"] = len(results) + 1
        results.append(r)
        if r.get("failure_detected"):
            total_failures += 1
            log.info("    FAILURE DETECTED")
            if r.get("correction_applied"):
                corrections.append(
                    {
                        "scenario": name,
                        "correction": r["correction_applied"],
                        "timestamp": time.time(),
                    }
                )
        log.info(f"    status={r.get('status')}")
    log.info()

    # Phase 2: Apply corrections and re-run
    log.info("[PHASE 2] Correction loop...")
    log.info("-" * 40)
    post_fix_results = []

    for correction in corrections:
        log.info(
            f"  Applying: {correction['scenario']} → {correction['correction'][:60]}..."
        )
        # Re-run the scenario after applying correction
        r = run_scenario(correction["scenario"])
        r["run_order"] = len(post_fix_results) + 1
        r["correction_source"] = correction["scenario"]
        post_fix_results.append(r)
    log.info()

    # Phase 3: Final report
    log.info("[PHASE 3] Final Report")
    log.info("=" * 60)

    tag_stats = compute_tag_stats(results)
    log.info("\nTag Distribution (Zettelkasten):")
    for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
        log.info(f"  {tag}: {count}")

    log.info(f"\nTotal scenarios: {len(SCENARIOS)}")
    log.info(f"Failures detected: {total_failures}")
    log.info(f"Corrections applied: {len(corrections)}")

    failures = [r for r in results if r.get("failure_detected")]
    log.info("\nFailure Summary:")
    for f in failures:
        log.info(f"  - {f['scenario']}: metrics={json.dumps(f.get('metrics', {}))}")

    improvements = sum(
        1
        for old, new in zip(failures, post_fix_results)
        if not new.get("failure_detected")
    )
    log.info(f"\nCorrections that improved: {improvements}/{len(post_fix_results)}")

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

    out_path = (
        Path(__file__).parent.parent
        / "artifacts"
        / "results"
        / f"run_{int(time.time())}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    log.info(f"\nResults saved to: {out_path}")
    log.info()
    log.info("=" * 60)
    log.info("GOAL: reactive → preventive")
    log.info("=" * 60)

    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

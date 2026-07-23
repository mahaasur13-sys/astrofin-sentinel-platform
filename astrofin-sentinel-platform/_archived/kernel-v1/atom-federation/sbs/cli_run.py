"""
sbs/cli_run.py — run subcommand implementation.
"""
import time
from typing import Any

from sbs import GlobalInvariantEngine, SystemBoundarySpec

_SCENARIOS = {
    "list": {
        "description": "List available scenarios",
        "args": [],
    },
    "healthy": {
        "description": "All layers nominal — should pass",
        "drl_state": {"leader": "n1", "term": 3, "partitions": 0},
        "ccl_state": {"leader": "n1", "term": 3, "stale_reads": 0},
        "f2_state": {"leader": "n1", "term": 3, "commit_index": 10, "quorum_ratio": 0.9},
        "desc_state": {"commit_index": 10},
    },
    "split-brain": {
        "description": "Split-brain scenario — should fail",
        "drl_state": {"leader": None, "term": 5, "partitions": 2},
        "ccl_state": {"leader": "n1", "term": 3, "stale_reads": 0},
        "f2_state": {"leader": "n1", "term": 5, "commit_index": 5, "quorum_ratio": 0.5},
        "desc_state": {"commit_index": 5},
    },
    "stale-read": {
        "description": "Stale read scenario — should fail",
        "drl_state": {"leader": "n1", "term": 3, "partitions": 0},
        "ccl_state": {"leader": None, "term": 2, "stale_reads": 5},
        "f2_state": {"leader": "n1", "term": 3, "commit_index": 10, "quorum_ratio": 0.9},
        "desc_state": {"commit_index": 10},
    },
}


def run_scenario(name: str, state_override: str | None) -> dict[str, Any]:
    """Run a predefined test scenario."""
    if name == "list":
        return {
            "ok": True,
            "scenarios": [{"name": k, **v} for k, v in _SCENARIOS.items() if k != "list"],
        }

    if name not in _SCENARIOS:
        return {"ok": False, "error": f"Unknown scenario: {name}. Run 'sbs run list' to see available."}

    scenario = _SCENARIOS[name]
    engine = GlobalInvariantEngine(SystemBoundarySpec())

    start = time.time()
    ok = engine.evaluate(
        scenario["drl_state"],
        scenario["ccl_state"],
        scenario["f2_state"],
        scenario["desc_state"],
    )
    duration = time.time() - start

    return {
        "ok": ok,
        "scenario": name,
        "description": scenario.get("description", ""),
        "duration": round(duration, 4),
        "expected": "pass" if name == "healthy" else "fail",
        "actual": "pass" if ok else "fail",
        "verdict": "✅ PASS" if (ok == (name == "healthy")) else "❌ FAIL",
    }

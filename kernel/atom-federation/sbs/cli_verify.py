"""
sbs/cli_verify.py — verify subcommand implementation.
"""
from typing import Any

from sbs import GlobalInvariantEngine, SystemBoundarySpec


def run_verify(spec: str = "strict") -> tuple[bool, dict[str, Any]]:
    """Run SBS verification."""
    spec_mode = {"strict": False, "relaxed": True, "minimal": True}.get(spec, False)
    engine = GlobalInvariantEngine(SystemBoundarySpec(allow_split_brain=spec_mode))

    test_cases = [
        {"name": "healthy", "expect": "pass", "drl_state": {"leader": "n1", "term": 3, "partitions": 0}, "ccl_state": {"leader": "n1", "term": 3, "stale_reads": 0}, "f2_state": {"leader": "n1", "term": 3, "commit_index": 10, "quorum_ratio": 0.9}, "desc_state": {"commit_index": 10}},
        {"name": "split-brain", "expect": "fail", "drl_state": {"leader": None, "term": 5, "partitions": 2}, "ccl_state": {"leader": "n1", "term": 3, "stale_reads": 0}, "f2_state": {"leader": "n1", "term": 5, "commit_index": 5, "quorum_ratio": 0.5}, "desc_state": {"commit_index": 5}},
        {"name": "stale-read", "expect": "fail", "drl_state": {"leader": "n1", "term": 3, "partitions": 0}, "ccl_state": {"leader": None, "term": 2, "stale_reads": 5}, "f2_state": {"leader": "n1", "term": 3, "commit_index": 10, "quorum_ratio": 0.9}, "desc_state": {"commit_index": 10}},
        {"name": "uncommitted-read", "expect": "fail", "drl_state": {"leader": "n1", "term": 3, "partitions": 0}, "ccl_state": {"leader": "n1", "term": 3, "stale_reads": 0}, "f2_state": {"leader": "n1", "term": 3, "commit_index": 5, "quorum_ratio": 0.9}, "desc_state": {"commit_index": 10}},
    ]

    results = []
    for tc in test_cases:
        drl = tc["drl_state"]
        ccl = tc["ccl_state"]
        f2 = tc["f2_state"]
        desc = tc["desc_state"]
        ok = engine.evaluate(drl, ccl, f2, desc)
        expect_fail = tc["expect"] == "fail"
        layer_ok = ok != expect_fail
        results.append({
            "name": tc["name"],
            "ok": layer_ok,
            "message": "invariant holds" if layer_ok else "invariant violated",
        })

    total = len(results)
    passed = sum(1 for r in results if r["ok"])

    return passed == total, {
        "spec": spec,
        "layers": {r["name"]: {"ok": r["ok"], "message": r["message"]} for r in results},
        "summary": {"total": total, "passed": passed},
    }

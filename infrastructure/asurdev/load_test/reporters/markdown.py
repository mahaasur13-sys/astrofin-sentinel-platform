#!/usr/bin/env python3
"""
#ACOS #LOAD_TEST
Markdown Reporter — generates human-readable report from orchestrator results
"""
import json, sys
from pathlib import Path
from datetime import datetime


def format_result(r: dict) -> str:
    lines = [
        f"## {r['scenario']}",
        f"",
        f"**Tags:** {', '.join(r.get('tags', []))}",
        f"**Failure detected:** {'❌ YES' if r.get('failure_detected') else '✅ NO'}",
        f"",
    ]
    if r.get("metrics"):
        lines.append("**Metrics:**")
        for k, v in r["metrics"].items():
            lines.append(f"  - `{k}`: {v}")
        lines.append("")
    if r.get("observed_behavior"):
        lines.append("**Observed:**")
        for k, v in r["observed_behavior"].items():
            lines.append(f"  - `{k}`: {v}")
        lines.append("")
    if r.get("correction_applied"):
        lines.append(f"**Correction:** {r['correction_applied']}")
        lines.append("")
    if r.get("result_after_fix"):
        lines.append("**After fix:**")
        for k, v in r["result_after_fix"].items():
            lines.append(f"  - `{k}`: {v}")
        lines.append("")
    return "\n".join(lines)


def generate_report(results_file: str):
    with open(results_file) as f:
        data = json.load(f)

    meta = data.get("meta", {})
    results = data.get("results", [])
    corrections = data.get("corrections", [])
    post = data.get("post_fix_results", [])

    lines = [
        f"# ACOS Load Test Report",
        f"",
        f"**Generated:** {datetime.fromtimestamp(meta.get('timestamp', 0))}",
        f"**Total scenarios:** {meta.get('total_scenarios', 0)}",
        f"**Failures detected:** {meta.get('total_failures', 0)}",
        f"**Corrections applied:** {meta.get('corrections_applied', 0)}",
        f"",
        f"## Tag Distribution",
        f"",
    ]

    for tag, count in sorted(meta.get("tag_stats", {}).items(), key=lambda x: -x[1]):
        lines.append(f"- {tag}: {count}")

    lines += ["", "## Results", ""]
    for r in results:
        lines.append(format_result(r))

    if corrections:
        lines += ["", "## Corrections Applied", ""]
        for c in corrections:
            lines.append(f"- **{c['scenario']}**: {c['correction']}")

    report = "\n".join(lines)
    print(report)

    out = Path(results_file).parent / "report.md"
    out.write_text(report)
    print(f"\nReport saved to: {out}")
    return report


if __name__ == "__main__":
    import glob
    results_files = sorted(glob.glob(str(Path(__file__).parent.parent / "artifacts" / "results" / "run_*.json")))
    if results_files:
        generate_report(results_files[-1])
    else:
        print("No results found. Run orchestrator first.")

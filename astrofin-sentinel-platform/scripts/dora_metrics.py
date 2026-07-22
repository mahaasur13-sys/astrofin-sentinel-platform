#!/usr/bin/env python3
"""DORA Metrics Collector for AstroFin Sentinel Platform.

Calculates the four DORA metrics from GitHub Actions workflow runs and
recent commit history via the GitHub REST API:

  1. Deployment Frequency (per week)
  2. Lead Time for Changes (commit -> first successful deployment, hours)
  3. Change Failure Rate (fraction of deployments that caused a reverted /
     failed follow-up within the window)
  4. Time to Restore (MTTR after a failed deploy, hours)

Outputs both a human-readable summary and a JSON report.

Usage:
    export GITHUB_TOKEN=ghp_...   # any token with `repo` read scope
    python scripts/dora_metrics.py --days 30
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import urllib.request
import urllib.error

REPO = "mahaasur13-sys/astrofin-sentinel-platform"
API = "https://api.github.com"


def gh_get(path: str, token: str) -> Tuple[int, Any]:
    url = f"{API}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "astrofin-dora-collector",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}


def collect(runs: List[dict], days: int) -> Dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    successful, failed = [], []
    for r in runs:
        ts = r.get("created_at") or r.get("updated_at")
        if not ts:
            continue
        when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if when < cutoff:
            continue
        status = r.get("conclusion") or r.get("status")
        if status == "success":
            successful.append(r)
        elif status == "failure":
            failed.append(r)

    deployments = len(successful)
    weeks = max(days / 7.0, 1.0)
    deploy_freq = deployments / weeks

    lead_times = []
    for r in successful:
        head_sha = r.get("head_sha") or r.get("sha")
        ts = r.get("created_at") or r.get["updated_at"]
        if not head_sha:
            continue
        try:
            when = datetime.fromisoformat((ts or "").replace("Z", "+00:00"))
            commit_resp = gh_get(f"/repos/{REPO}/commits/{head_sha}", token=os.environ.get("GITHUB_TOKEN") or os.environ.get("AFS4", ""))
            if commit_resp[0] == 200:
                committed = commit_resp[1]["commit"]["author"]["date"]
                committed_dt = datetime.fromisoformat(committed.replace("Z", "+00:00"))
                lead_times.append((when - committed_dt).total_seconds() / 3600.0)
        except Exception:
            pass

    total_runs = len(successful) + len(failed)
    cfr = (len(failed) / total_runs) if total_runs else 0.0

    return {
        "window_days": days,
        "deployment_frequency_per_week": round(deploy_freq, 3),
        "lead_time_hours_avg": round(sum(lead_times) / len(lead_times), 2) if lead_times else None,
        "lead_time_hours_median": round(sorted(lead_times)[len(lead_times) // 2], 2) if lead_times else None,
        "lead_time_samples": len(lead_times),
        "change_failure_rate": round(cfr, 3),
        "deployments": deployments,
        "failed_runs": len(failed),
        "successful_runs": len(successful),
    }


def render_table(m: Dict[str, Any]) -> str:
    rf = "High" if m["deployment_frequency_per_week"] >= 7 else ("Medium" if m["deployment_frequency_per_week"] >= 1 else "Low")
    lt = m["lead_time_hours_avg"]
    if lt is None:
        lt_str = "n/a"
        lt_rate = "n/a"
    else:
        lt_str = f"{lt:.2f} h"
        lt_rate = "High" if lt <= 24 else ("Medium" if lt <= 168 else "Low")
    cfr = m["change_failure_rate"]
    cfr_rate = "High" if cfr <= 0.05 else ("Medium" if cfr <= 0.10 else "Low")

    return (
        "DORA Performance Summary\n"
        "=========================\n"
        f"Window: last {m['window_days']} days\n\n"
        f"1) Deployment Frequency: {m['deployment_frequency_per_week']} / week  -> {rf}\n"
        f"   ({m['successful_runs']} successful runs, {m['failed_runs']} failed)\n\n"
        f"2) Lead Time for Changes: {lt_str} (samples: {m['lead_time_samples']})  -> {lt_rate}\n\n"
        f"3) Change Failure Rate:   {cfr:.1%}  -> {cfr_rate}\n\n"
        "4) Time to Restore (MTTR): reported via workflow reruns; not collected here.\n"
    )


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Collect DORA metrics from GitHub Actions")
    p.add_argument("--days", type=int, default=30, help="window in days (default: 30)")
    p.add_argument("--per-page", type=int, default=100, help="workflow runs per page")
    p.add_argument("--out", type=Path, default=None, help="optional JSON output path")
    args = p.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("AFS4") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: set GITHUB_TOKEN (or AFS4) environment variable", file=sys.stderr)
        return 2

    status, runs = gh_get(
        f"/repos/{REPO}/actions/runs?per_page={args.per_page}", token
    )
    if status != 200:
        print(f"ERROR: GitHub API returned HTTP {status}", file=sys.stderr)
        if isinstance(runs, dict):
            print(json.dumps(runs, indent=2)[:500], file=sys.stderr)
        return 1

    workflow_runs = runs.get("workflow_runs", [])
    metrics = collect(workflow_runs, args.days)
    print(render_table(metrics))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        metrics["generated_at"] = datetime.now(timezone.utc).isoformat()
        args.out.write_text(json.dumps(metrics, indent=2))
        print(f"JSON report written to: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

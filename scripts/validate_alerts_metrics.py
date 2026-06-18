#!/usr/bin/env python3
"""
Validate that all alert rules reference existing metrics.
Known metrics list should be updated when new metrics are added.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# --- Extend this list when implementing new domain metrics ---
KNOWN_METRICS = {
    # Standard exporters
    "pg_up",
    "redis_up",
    # From tools/metrics_server.py
    "astrofin_requests_total",
    "astrofin_broker_errors_total",
    "astrofin_ollama_available",
    "astrofin_cache_hits_total",
    "astrofin_cache_misses_total",
    "astrofin_backtest_real_runs_total",
    "astrofin_backtest_synthetic_runs_total",
    "astrofin_agent_selection_total",
    "astrofin_agent_signal_total",
    "astrofin_thompson_params",
    "astrofin_rag_relevance_avg",
    "astrofin_rag_chunk_count",
    "astrofin_rag_query_cache_hits_total",
    "astrofin_rag_query_cache_misses_total",
}


def extract_metric_names(expr: str) -> list[str]:
    """Naively extract metric names from a PromQL expression."""
    # Simple regex: match words that follow prometheus metric naming conventions
    # This will also match function names, but it's good enough for validation
    return re.findall(r"\b([a-zA-Z_:][a-zA-Z0-9_:]*)\b", expr)


def main():
    alerts_path = Path(__file__).parent.parent / "deploy" / "monitoring" / "alerts.yml"
    if not alerts_path.exists():
        print(f"ERROR: {alerts_path} not found")
        sys.exit(1)

    with open(alerts_path) as f:
        data = yaml.safe_load(f)

    errors = []
    for group in data.get("groups", []):
        for rule in group.get("rules", []):
            alert_name = rule.get("alert")
            if not alert_name:
                continue
            expr = rule.get("expr", "")
            for metric in extract_metric_names(expr):
                # Skip functions and operators (uppercase or known PromQL functions)
                if metric.isupper() or metric in {
                    "rate",
                    "irate",
                    "increase",
                    "sum",
                    "avg",
                    "max",
                    "min",
                    "by",
                    "without",
                    "offset",
                    "on",
                    "ignoring",
                    "group_left",
                    "group_right",
                }:
                    continue
                if metric not in KNOWN_METRICS:
                    errors.append(f"{alert_name}: metric '{metric}' not in known metrics list")

    if errors:
        print("ERROR: Alert rules reference unknown metrics:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("OK: All alert metrics are known.")
        sys.exit(0)


if __name__ == "__main__":
    main()

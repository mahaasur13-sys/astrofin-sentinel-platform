#!/usr/bin/env python3
"""H-05: Simulate alert storm — test Alertmanager routing + dedup.

Usage:
    python scripts/alert_storm_test.py --count 20 --alertmanager http://localhost:9093
    python scripts/alert_storm_test.py --dry-run  # validate structure only
"""

from __future__ import annotations

import argparse
import json
import time

ALERT_START = "2026-08-11T00:00:00Z"


def generate_alerts(count: int = 20) -> list[dict]:
    """Generate simulated alert storm events."""
    alerts = []
    severities = ["critical", "warning"]
    instances = ["agent-0", "agent-1", "agent-2", "api-0", "scheduler-0"]

    for i in range(count):
        severity = severities[0] if i < count // 2 else severities[1]
        alert = {
            "labels": {
                "alertname": f"TestAlert_{i % 5}",
                "severity": severity,
                "instance": instances[i % len(instances)],
                "job": "astrofin-sentinel",
            },
            "annotations": {
                "summary": f"Test alert #{i} — {severity} severity",
                "description": f"Simulated alert for hardening window. Seq: {i}/{count}",
            },
            "startsAt": ALERT_START,
            "endsAt": "2026-08-11T01:00:00Z",
        }
        alerts.append(alert)
    return alerts


def validate_alerts(alerts: list[dict]) -> bool:
    """Validate alert structure before sending."""
    required_labels = {"alertname", "severity", "instance", "job"}
    valid = True
    for i, a in enumerate(alerts):
        missing = required_labels - set(a["labels"].keys())
        if missing:
            print(f"  ❌ Alert {i}: missing labels {missing}")
            valid = False
    return valid


def send_alerts(alerts: list[dict], alertmanager_url: str) -> dict:
    """POST alerts to Alertmanager API."""
    import requests
    resp = requests.post(
        f"{alertmanager_url}/api/v1/alerts",
        json=alerts,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    return {"status_code": resp.status_code, "body": resp.text[:500]}


def check_groups(alertmanager_url: str) -> dict:
    """Check how Alertmanager grouped the alerts."""
    import requests
    resp = requests.get(f"{alertmanager_url}/api/v2/alerts/groups", timeout=10)
    data = resp.json()
    group_count = len(data) if isinstance(data, list) else len(data.get("data", []))
    return {"status_code": resp.status_code, "group_count": group_count}


def main():
    parser = argparse.ArgumentParser(description="Alert storm simulation")
    parser.add_argument("--count", type=int, default=20, help="Number of alerts to generate")
    parser.add_argument("--alertmanager", default="http://localhost:9093", help="Alertmanager URL")
    parser.add_argument("--dry-run", action="store_true", help="Generate but don't send")
    args = parser.parse_args()

    alerts = generate_alerts(args.count)
    print(f"\n{'='*60}")
    print(f"  ALERT STORM TEST — {len(alerts)} alerts")
    print(f"  Severities: {len([a for a in alerts if a['labels']['severity']=='critical'])} critical, "
          f"{len([a for a in alerts if a['labels']['severity']=='warning'])} warning")
    print(f"  Unique alertnames: {len(set(a['labels']['alertname'] for a in alerts))}")
    print(f"{'='*60}")

    if not validate_alerts(alerts):
        print("  ❌ Validation failed")
        return

    if args.dry_run:
        print("  ✅ Dry-run: alerts validated (not sent)")
        for i, a in enumerate(alerts[:5]):
            print(f"    [{i}] {a['labels']['alertname']} severity={a['labels']['severity']} instance={a['labels']['instance']}")
        if len(alerts) > 5:
            print(f"    ... and {len(alerts)-5} more")
        return

    print(f"\n  Sending to {args.alertmanager}/api/v1/alerts ...")
    result = send_alerts(alerts, args.alertmanager)
    print(f"  Status: {result['status_code']}")

    time.sleep(2)

    groups = check_groups(args.alertmanager)
    print(f"  Groups after dedup: {groups['group_count']}")
    print(f"\n  Expected: ≤5 groups (one per alertname, severity-split possible)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

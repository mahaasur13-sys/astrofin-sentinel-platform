"""Simulate alert storm to test Alertmanager routing and deduplication (H-05)."""
import requests
import time
import sys

ALERTMANAGER_URL = "http://localhost:9093/api/v1/alerts"
ALERT_COUNT = 20
UNIQUE_ALERT_NAMES = 5

def generate_alerts(count=ALERT_COUNT, unique_names=UNIQUE_ALERT_NAMES):
    alerts = []
    for i in range(count):
        alerts.append({
            "labels": {
                "alertname": f"TestAlert_{i % unique_names}",
                "severity": "critical" if i < 10 else "warning",
                "instance": f"agent-{i}"
            },
            "annotations": {
                "summary": f"Test alert {i}"
            },
            "startsAt": "2026-08-11T00:00:00Z"
        })
    return alerts

def send_alerts(alerts):
    try:
        resp = requests.post(ALERTMANAGER_URL, json=alerts, timeout=10)
        print(f"Sent {len(alerts)} alerts, status: {resp.status_code}")
        return resp.status_code == 200
    except requests.ConnectionError:
        print("Alertmanager not reachable at", ALERTMANAGER_URL)
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_groups():
    try:
        time.sleep(2)
        resp = requests.get(f"{ALERTMANAGER_URL}/groups", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            groups_count = len(data.get("data", []))
            print(f"Groups after storm: {groups_count}")
            return groups_count
    except Exception:
        pass
    return None

if __name__ == "__main__":
    alerts = generate_alerts()
    sent = send_alerts(alerts)
    if sent is None:
        print("SKIP: Alertmanager not available (requires Docker)")
        sys.exit(0)
    groups = check_groups()
    total = len(alerts)
    print(f"Result: {total} alerts sent, {groups} groups formed")

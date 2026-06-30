"""ROMA Audit Log — Immutable append-only event log."""
import time
import json
import csv
import io

class AuditLog:
    def __init__(self):
        self._events = []
        self._counter = 0

    def log_event(self, user_id: str, org_id: str, event_type: str, metadata: dict):
        self._counter += 1
        entry = {
            "entry_id": f"ae_{self._counter:06d}",
            "timestamp": time.time(),
            "user_id": user_id,
            "org_id": org_id,
            "event_type": event_type,
            "metadata": metadata,
            "immutable": True
        }
        self._events.append(entry)

    def query_events(self, org_id: str = None, user_id: str = None,
                     event_type: str = None, limit: int = 100) -> list:
        results = self._events
        if org_id:
            results = [e for e in results if e["org_id"] == org_id]
        if user_id:
            results = [e for e in results if e["user_id"] == user_id]
        if event_type:
            results = [e for e in results if e["event_type"] == event_type]
        return results[-limit:]

    def export_json(self, org_id: str) -> str:
        events = self.query_events(org_id=org_id, limit=10000)
        return json.dumps({"org_id": org_id, "events": events, "count": len(events)}, indent=2)

    def export_csv(self, org_id: str) -> str:
        events = self.query_events(org_id=org_id, limit=10000)
        output = io.StringIO()
        if events:
            writer = csv.DictWriter(output, fieldnames=list(events[0].keys()))
            writer.writeheader()
            writer.writerows(events)
        return output.getvalue()

    def export_pdf_report(self, org_id: str) -> dict:
        events = self.query_events(org_id=org_id, limit=10000)
        return {
            "org_id": org_id,
            "period": {"from": events[0]["timestamp"] if events else None,
                       "to": events[-1]["timestamp"] if events else None},
            "total_events": len(events),
            "event_types": list(set(e["event_type"] for e in events)),
            "report_url": f"/audit/org/{org_id}/report.pdf"
        }

if __name__ == "__main__":
    log = AuditLog()
    log.log_event("alice", "org_acme", "JOB_EXECUTED", {"job_id": "j001", "cost": 2.50})
    log.log_event("bob", "org_acme", "API_KEY_CREATED", {"key_id": "kid_123"})
    entries = log.query_events(org_id="org_acme", limit=10)
    print(f"Audit entries: {len(entries)}")
    print("CSV:", log.export_csv("org_acme").splitlines()[:3])

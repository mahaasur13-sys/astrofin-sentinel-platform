#!/usr/bin/env python3
from enum import Enum
"""
Incident Model — auto-classification + severity scoring.
Severity = f(p99_delta, error_rate, alignment_drop).
Auto-classification: S1 → L3 rollback / S2 → L2 / S3 → alert only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib


class Severity(Enum):
    S1_CRITICAL = "S1"
    S2_WARNING = "S2"
    S3_INFO = "S3"


@dataclass
class Incident:
    incident_id: str
    timestamp: datetime
    trigger_type: str
    affected_nodes: list[str]
    pre_state: dict
    post_state: dict
    policy_hash: str
    severity: Severity
    root_cause: Optional[str] = None
    resolved: bool = False
    resolution_time_ms: Optional[float] = None
    actions_taken: list[str] = field(default_factory=list)


class IncidentManager:
    """
    Auto-classifies incidents by severity.
    Routes to appropriate response (rollback level or alert).
    
    Severity scoring:
        severity = w_latency * p99_delta + w_failure * error_rate + w_drift * alignment_drop
    """

    LATENCY_WEIGHT = 0.4
    FAILURE_WEIGHT = 0.4
    DRIFT_WEIGHT = 0.2
    S1_THRESHOLD = 0.8
    S2_THRESHOLD = 0.4

    def __init__(self, rollback_engine, alerting_callback=None):
        self.rollback_engine = rollback_engine
        self.alerting_callback = alerting_callback  # e.g. send_telegram_message
        self._incidents: list[Incident] = []

    def create(
        self,
        trigger_type: str,
        severity: float,
        details: dict,
        pre_state: Optional[dict] = None,
        post_state: Optional[dict] = None,
        policy_hash: Optional[str] = None,
    ) -> Incident:
        """Factory: create + classify + route incident."""
        incident_id = hashlib.sha256(
            f"{trigger_type}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]

        # Auto-classify severity
        severity_enum = self._classify(severity)

        incident = Incident(
            incident_id=incident_id,
            timestamp=datetime.utcnow(),
            trigger_type=trigger_type,
            affected_nodes=details.get("affected_nodes", []),
            pre_state=pre_state or {},
            post_state=post_state or {},
            policy_hash=policy_hash or details.get("policy_hash", ""),
            severity=severity_enum,
            root_cause=details.get("root_cause"),
        )

        self._incidents.append(incident)

        # Auto-route by severity
        self._route(incident)

        return incident

    def _classify(self, score: float) -> Severity:
        if score >= self.S1_THRESHOLD:
            return Severity.S1_CRITICAL
        elif score >= self.S2_THRESHOLD:
            return Severity.S2_WARNING
        return Severity.S3_INFO

    def _route(self, incident: Incident) -> None:
        """Route to appropriate response by severity."""
        if incident.severity == Severity.S1_CRITICAL:
            # Full L3 rollback
            self.rollback_engine.rollback_l3(f"incident_{incident.incident_id}")
            incident.actions_taken.append("L3_rollback")
            self._alert(incident, "🚨 S1 CRITICAL: L3 rollback triggered")

        elif incident.severity == Severity.S2_WARNING:
            # L2 rollback
            self.rollback_engine.rollback_l2(f"incident_{incident.incident_id}")
            incident.actions_taken.append("L2_rollback")
            self._alert(incident, "⚠️ S2 WARNING: L2 rollback triggered")

        else:
            # S3: alert only
            self._alert(incident, "ℹ️ S3 INFO: incident logged")

    def _alert(self, incident: Incident, message: str) -> None:
        if self.alerting_callback:
            self.alerting_callback(message)
        # Also log to incident channel
        print(f"[INCIDENT] {message} | {incident.trigger_type} | nodes={incident.affected_nodes}")

    def get_active(self) -> list[Incident]:
        return [i for i in self._incidents if not i.resolved]

    def resolve(self, incident_id: str) -> None:
        for inc in self._incidents:
            if inc.incident_id == incident_id:
                inc.resolved = True
                inc.resolution_time_ms = (
                    datetime.utcnow() - inc.timestamp
                ).total_seconds() * 1000
                break

    def get_incident_rate(self, window_minutes: int = 60) -> float:
        """Incidents per hour."""
        cutoff = datetime.utcnow().timestamp() - window_minutes * 60
        recent = [i for i in self._incidents if i.timestamp.timestamp() >= cutoff]
        return len(recent) / (window_minutes / 60)

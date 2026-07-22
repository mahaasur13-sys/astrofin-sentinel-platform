#!/usr/bin/env python3
"""
L10 Self-Healing — Failure Isolation Model
Partial rollback + cascade prevention + severity mapping.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class IncidentSeverity(Enum):
    NONE = 0
    WARNING = 1
    MINOR = 2
    MODERATE = 3
    SEVERE = 4
    CRITICAL = 5
    CATASTROPHIC = 6


class FailMode(Enum):
    SOFT = auto()  # log + monitor + optional rollback
    HARD = auto()  # mandatory rollback + escalation


@dataclass
class FailureTrigger:
    metric: str
    threshold: float
    comparison: str  # >, <, >=, <=
    window_sec: int = 60
    severity: IncidentSeverity = IncidentSeverity.WARNING


@dataclass
class RollbackAction:
    target_layer: str
    action: str  # restore_snapshot | restart_service | drain_node | fence_node
    target_id: str
    priority: int = 0
    timeout_sec: int = 300


@dataclass
class Incident:
    incident_id: str
    run_id: str
    severity: IncidentSeverity
    fail_mode: FailMode
    description: str
    affected_layers: list[str]
    trigger_metrics: dict[str, float] = field(default_factory=dict)
    root_cause: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: str | None = None
    rollback_actions: list[RollbackAction] = field(default_factory=list)

    def is_contained(self) -> bool:
        return self.severity.value <= IncidentSeverity.MODERATE.value

    def requires_hard_fail(self) -> bool:
        return (
            self.fail_mode == FailMode.HARD
            or self.severity.value >= IncidentSeverity.SEVERE.value
        )

    def containment_boundary(self) -> str:
        if self.severity.value >= IncidentSeverity.SEVERE.value:
            return "L8_governance"
        elif self.severity.value >= IncidentSeverity.MODERATE.value:
            return "L9_ebl"
        elif self.severity.value >= IncidentSeverity.MINOR.value:
            return "L10_self_healing"
        else:
            return "monitor_only"


SEVERITY_RESPONSE: dict[IncidentSeverity, dict[str, Any]] = {
    IncidentSeverity.WARNING: {
        "fail_mode": FailMode.SOFT,
        "rollback": False,
        "escalate": False,
        "notify": True,
    },
    IncidentSeverity.MINOR: {
        "fail_mode": FailMode.SOFT,
        "rollback": False,
        "escalate": False,
        "notify": True,
    },
    IncidentSeverity.MODERATE: {
        "fail_mode": FailMode.SOFT,
        "rollback": True,
        "escalate": False,
        "notify": True,
    },
    IncidentSeverity.SEVERE: {
        "fail_mode": FailMode.HARD,
        "rollback": True,
        "escalate": True,
        "notify": True,
    },
    IncidentSeverity.CRITICAL: {
        "fail_mode": FailMode.HARD,
        "rollback": True,
        "escalate": True,
        "notify": True,
    },
    IncidentSeverity.CATASTROPHIC: {
        "fail_mode": FailMode.HARD,
        "rollback": True,
        "escalate": True,
        "notify": True,
        "fence": True,
    },
}


class FailureIsolator:
    def __init__(self, snapshot_store, trace_store):
        self.snapshot_store = snapshot_store
        self.trace_store = trace_store
        self.active_incidents: dict[str, Incident] = {}
        self.incident_history: list[Incident] = []
        self.rollback_queue: list[RollbackAction] = []
        self.cascade_prevention: bool = True

    def classify_incident(
        self, trigger: FailureTrigger, metrics: dict[str, float], run_id: str, desc: str
    ) -> Incident:
        resp = SEVERITY_RESPONSE.get(
            trigger.severity, SEVERITY_RESPONSE[IncidentSeverity.WARNING]
        )
        fail_mode = (
            FailMode.HARD if resp["fail_mode"] == FailMode.HARD else FailMode.SOFT
        )

        incident = Incident(
            incident_id=f"inc_{len(self.active_incidents):04d}",
            run_id=run_id,
            severity=trigger.severity,
            fail_mode=fail_mode,
            description=desc,
            affected_layers=[trigger.metric.split(".")[0]],
            trigger_metrics=metrics,
            rollback_actions=self._plan_rollback(trigger),
        )
        self.active_incidents[incident.incident_id] = incident
        return incident

    def _plan_rollback(self, trigger: FailureTrigger) -> list[RollbackAction]:
        actions = []
        metric = trigger.metric

        if "slurm" in metric:
            actions.append(
                RollbackAction(
                    target_layer="L4",
                    action="restart_service",
                    target_id="slurmctld",
                    priority=1,
                )
            )
        elif "ceph" in metric:
            actions.append(
                RollbackAction(
                    target_layer="L3",
                    action="restore_snapshot",
                    target_id="ceph_osd",
                    priority=2,
                )
            )
            actions.append(
                RollbackAction(
                    target_layer="L3",
                    action="fence_node",
                    target_id="ceph_mon",
                    priority=1,
                )
            )
        elif "gpu" in metric:
            actions.append(
                RollbackAction(
                    target_layer="L0",
                    action="drain_node",
                    target_id="gpu_node",
                    priority=1,
                )
            )
        elif "ml" in metric:
            actions.append(
                RollbackAction(
                    target_layer="L5",
                    action="restore_snapshot",
                    target_id="ml_model",
                    priority=3,
                )
            )

        return sorted(actions, key=lambda a: a.priority)

    def resolve_incident(self, incident_id: str) -> None:
        incident = self.active_incidents.get(incident_id)
        if incident:
            incident.resolved_at = datetime.now(timezone.utc).isoformat()
            self.active_incidents.pop(incident_id)
            self.incident_history.append(incident)

    def cascade_check(
        self, incident: Incident, all_incidents: list[Incident]
    ) -> list[str]:
        """Prevent cascade failures by checking if new incident could trigger others."""
        warnings = []
        recent = [i for i in all_incidents if i.incident_id != incident.incident_id]

        for existing in recent:
            if existing.severity.value >= IncidentSeverity.SEVERE.value:
                shared_layers = set(existing.affected_layers) & set(
                    incident.affected_layers
                )
                if shared_layers:
                    warnings.append(
                        f"CASCADE_RISK: incident={incident.incident_id} shares layers {shared_layers} "
                        f"with active incident={existing.incident_id} (severity={existing.severity.name})"
                    )
        return warnings

    def incident_summary(self) -> dict[str, Any]:
        return {
            "active": len(self.active_incidents),
            "history": len(self.incident_history),
            "by_severity": {
                s.name: sum(
                    1 for i in self.active_incidents.values() if i.severity == s
                )
                for s in IncidentSeverity
                if s != IncidentSeverity.NONE
            },
        }

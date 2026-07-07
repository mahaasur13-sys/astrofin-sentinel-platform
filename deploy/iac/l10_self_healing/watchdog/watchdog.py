#!/usr/bin/env python3
"""
L10 Self-Healing — Watchdog
Monitors health across all layers, triggers isolation on failure.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from l10_self_healing.orchestrator.failure_isolation import FailureIsolator, FailureTrigger


@dataclass
class HealthMetric:
    name: str
    value: float
    unit: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_layer: str = ""


@dataclass
class WatchdogResult:
    checked_at: str
    total_metrics: int
    healthy: int
    degraded: int
    failed: int
    triggered_incidents: list[str]
    actions_taken: list[str]


class Watchdog:
    def __init__(self, failure_isolator: FailureIsolator):
        self.failure_isolator = failure_isolator
        self.health_checks: list[HealthMetric] = []
        self.watchdog_triggers: dict[str, FailureTrigger] = {}
        self.last_check: str | None = None
        self._monitors: dict[str, Callable] = {}

    def register_trigger(self, trigger: FailureTrigger) -> None:
        self.watchdog_triggers[trigger.metric] = trigger

    def register_monitor(self, metric_name: str, monitor_fn: Callable[[], float]) -> None:
        self._monitors[metric_name] = monitor_fn

    def check(self) -> WatchdogResult:
        triggered = []
        actions = []
        healthy = degraded = failed = 0

        for metric_name, monitor_fn in self._monitors.items():
            value = monitor_fn()
            hm = HealthMetric(name=metric_name, value=value, unit="", source_layer=metric_name.split(".")[0])
            self.health_checks.append(hm)

            trigger = self.watchdog_triggers.get(metric_name)
            if trigger:
                violating = self._evaluate_trigger(value, trigger)
                if violating:
                    failed += 1
                    incident = self.failure_isolator.classify_incident(
                        trigger=trigger,
                        metrics={metric_name: value},
                        run_id="wd_run",
                        desc=f"Watchdog trigger: {metric_name}={value} {trigger.comparison} {trigger.threshold}",
                    )
                    triggered.append(incident.incident_id)
                    for rb_action in incident.rollback_actions:
                        actions.append(f"{rb_action.action} on {rb_action.target_id} (layer={rb_action.target_layer})")
                else:
                    healthy += 1
            else:
                healthy += 1

        self.last_check = datetime.now(timezone.utc).isoformat()

        return WatchdogResult(
            checked_at=self.last_check,
            total_metrics=len(self._monitors),
            healthy=healthy,
            degraded=degraded,
            failed=failed,
            triggered_incidents=triggered,
            actions_taken=actions,
        )

    def _evaluate_trigger(self, value: float, trigger: FailureTrigger) -> bool:
        comp = trigger.comparison
        thr = trigger.threshold
        if comp == ">":
            return value > thr
        elif comp == "<":
            return value < thr
        elif comp == ">=":
            return value >= thr
        elif comp == "<=":
            return value <= thr
        elif comp == "==":
            return value == thr
        return False

    def status_summary(self) -> dict[str, Any]:
        return {
            "registered_triggers": len(self.watchdog_triggers),
            "registered_monitors": len(self._monitors),
            "last_check": self.last_check,
            "active_incidents": len(self.failure_isolator.active_incidents),
            "incident_summary": self.failure_isolator.incident_summary(),
        }

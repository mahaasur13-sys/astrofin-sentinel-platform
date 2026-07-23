"""
PolicyEngine v6.4 — Maps SBS/chaos events → runtime actions.

Usage:
    engine = PolicyEngine()
    engine.register(ReactionTrigger.SBS_VIOLATION, PolicyAction.EVICT_NODE)
    engine.register(ReactionTrigger.QUORUM_DEGRADED, PolicyAction.RECONFIGURE_QUORUM)
    engine.register(ReactionTrigger.NODE_UNREACHABLE, PolicyAction.ADD_OBSERVATION)

    action = engine.decide(trigger, context)
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto

__all__ = ["PolicyAction", "PolicyEngine", "PolicyRule", "TriggerMatch"]


# ── Triggers ──────────────────────────────────────────────────────────────────

class ReactionTrigger(Enum):
    """Events that can trigger a reaction."""

    SBS_VIOLATION = auto()          # Any SBS invariant broken
    LEADER_UNIQUENESS_VIOLATION = auto()  # Two leaders detected
    QUORUM_DEGRADED = auto()        # F2 quorum ratio below threshold
    QUORUM_LOST = auto()            # F2 quorum broken
    NODE_UNREACHABLE = auto()       # Health ping failed
    NODE_RECOVERED = auto()         # Node came back
    PARTITION_DETECTED = auto()     # Network partition identified
    PARTITION_HEALED = auto()       # Network partition resolved
    BYZANTINE_SIGNAL = auto()       # Conflicting/contradictory state
    CLOCK_SKEW_EXCEEDED = auto()    # Temporal drift too large
    DRL_LATENCY_EXCEEDED = auto()   # RPC latency above SLO
    DRL_LOSS_EXCEEDED = auto()      # Packet loss above SLO
    NODE_EVICTED = auto()           # Node was evicted
    NODE_JOINED = auto()            # New node joined cluster
    LEADERSHIP_CONTEST = auto()     # Term increase without election win
    RECOVERY_COMPLETE = auto()      # Healing action finished
    STABILITY_SCORE_LOW = auto()    # Overall stability below threshold


class PolicyAction(Enum):
    """Actions the resilience engine can take."""

    NOOP = auto()                   # Ignore event
    LOG_ONLY = auto()               # Log but don't act
    ADD_OBSERVATION = auto()        # Mark node degraded, continue
    EVICT_NODE = auto()             # Remove node from cluster
    RECONFIGURE_QUORUM = auto()     # Recalculate F2 quorum set
    TRIGGER_RE_ELECTION = auto()    # Force leader re-election
    INITIATE_NODE_JOIN = auto()     # Bootstrap new node
    INITIATE_PARTITION_HEAL = auto()  # Restore network path
    ISOLATE_BYZANTINE = auto()      # Quarantine malicious node
    DRAIN_NODE = auto()             # Stop routing to node, let it recover
    RESTORE_NODE = auto()           # Return node to full service
    TRIGGER_SELF_HEAL = auto()      # Invoke healing pipeline
    SCALE_UP = auto()               # Add capacity
    SCALE_DOWN = auto()             # Remove capacity
    ALERT_OPS = auto()              # Page/on-call alert


# ── Policy Rule ────────────────────────────────────────────────────────────────

@dataclass
class PolicyRule:
    """
    A single policy mapping trigger(s) to an action, with optional
    condition callable and cooldown.
    """

    trigger: ReactionTrigger
    action: PolicyAction
    condition: Callable[[dict], bool] | None = None
    cooldown_seconds: float = 5.0
    priority: int = 0  # Higher = evaluated first
    label: str = ""

    _last_fired: float = field(default=0.0, repr=False)

    def can_fire(self, now: float) -> bool:
        if self.cooldown_seconds <= 0:
            return True
        return (now - self._last_fired) >= self.cooldown_seconds

    def mark_fired(self, now: float) -> None:
        self._last_fired = now

    def matches(self, trigger: ReactionTrigger, context: dict) -> bool:
        if trigger != self.trigger:
            return False
        if self.condition is None:
            return True
        try:
            return bool(self.condition(context))
        except Exception:
            return False


@dataclass
class TriggerMatch:
    rule: PolicyRule
    action: PolicyAction


# ── PolicyEngine ───────────────────────────────────────────────────────────────

class PolicyEngine:
    """
    Maps ReactionTrigger events to PolicyAction responses using
    a priority-ordered rule set with per-rule cooldowns.

    Ships with sensible defaults covering all v6.4 reaction scenarios.
    """

    def __init__(self) -> None:
        self._rules: list[PolicyRule] = []
        self._cooldown_map: dict[ReactionTrigger, float] = {}
        self._log: list[dict] = []
        self._register_defaults()

    # ── Rule management ───────────────────────────────────────────────────

    def register(self, trigger: ReactionTrigger, action: PolicyAction,
                condition: Callable[[dict], bool] | None = None,
                cooldown: float = 5.0,
                priority: int = 0,
                label: str = "") -> PolicyRule:
        rule = PolicyRule(
            trigger=trigger,
            action=action,
            condition=condition,
            cooldown_seconds=cooldown,
            priority=priority,
            label=label or f"{trigger.name}→{action.name}",
        )
        self._rules.append(rule)
        self._rules.sort(key=lambda r: -r.priority)
        return rule

    def unregister(self, label: str) -> None:
        self._rules = [r for r in self._rules if r.label != label]

    def clear(self) -> None:
        self._rules.clear()

    # ── Decision ──────────────────────────────────────────────────────────

    def decide(self, trigger: ReactionTrigger,
               context: dict | None = None) -> PolicyAction:
        """
        Find the first matching rule for `trigger` and return its action.

        Rules are evaluated in priority order (highest first).
        Cooldowns prevent rapid re-triggering of the same rule.
        """
        context = context or {}
        now = time.monotonic()

        # Per-trigger global cooldown
        global_cooldown = self._cooldown_map.get(trigger, 0.0)
        if global_cooldown > 0 and (now - global_cooldown) < 1.0:
            self._log.append({
                "ts": now,
                "trigger": trigger.name,
                "action": "GLOBAL_COOLDOWN",
                "context": context,
            })
            return PolicyAction.NOOP

        for rule in self._rules:
            if rule.matches(trigger, context):
                if not rule.can_fire(now):
                    continue
                rule.mark_fired(now)
                self._cooldown_map[trigger] = now
                self._log.append({
                    "ts": now,
                    "trigger": trigger.name,
                    "action": rule.action.name,
                    "rule": rule.label,
                    "context": context,
                })
                return rule.action

        self._log.append({
            "ts": now,
            "trigger": trigger.name,
            "action": "NO_MATCH",
            "context": context,
        })
        return PolicyAction.NOOP

    def decide_and_record(self, trigger: ReactionTrigger,
                          context: dict | None = None) -> TriggerMatch:
        """decide() + return (rule, action) for transparency."""
        action = self.decide(trigger, context)
        matched_rule = next(
            (r for r in self._rules if r.trigger == trigger and r.can_fire(time.monotonic())),
            None
        )
        return TriggerMatch(rule=matched_rule, action=action)

    # ── Defaults ──────────────────────────────────────────────────────────

    def _register_defaults(self) -> None:
        """
        Ship-with defaults covering all SBS/chaos → action mappings.

        Priority: CRITICAL (100+) > NORMAL (50) > LOW (10)
        """

        # ── SBS Violations ──────────────────────────────────────────────
        self.register(
            ReactionTrigger.SBS_VIOLATION,
            PolicyAction.EVICT_NODE,
            condition=lambda c: c.get("violation_type") == "CRITICAL",
            priority=100,
            label="sbs_critical→evict",
        )
        self.register(
            ReactionTrigger.SBS_VIOLATION,
            PolicyAction.ADD_OBSERVATION,
            condition=lambda c: c.get("violation_type") == "RECOVERABLE",
            priority=90,
            label="sbs_recoverable→observe",
        )

        # ── Leadership ──────────────────────────────────────────────────
        self.register(
            ReactionTrigger.LEADER_UNIQUENESS_VIOLATION,
            PolicyAction.TRIGGER_RE_ELECTION,  # sic — handled by healer
            priority=100,
            label="split_brain→re_election",
        )
        self.register(
            ReactionTrigger.LEADERSHIP_CONTEST,
            PolicyAction.TRIGGER_SELF_HEAL,
            priority=80,
            label="leadership_contest→heal",
        )

        # ── Quorum ──────────────────────────────────────────────────────
        self.register(
            ReactionTrigger.QUORUM_LOST,
            PolicyAction.ALERT_OPS,
            priority=100,
            label="quorum_lost→alert",
        )
        self.register(
            ReactionTrigger.QUORUM_LOST,
            PolicyAction.RECONFIGURE_QUORUM,
            priority=95,
            label="quorum_lost→reconfigure",
        )
        self.register(
            ReactionTrigger.QUORUM_DEGRADED,
            PolicyAction.RECONFIGURE_QUORUM,
            cooldown=30.0,
            priority=60,
            label="quorum_degraded→reconfigure",
        )

        # ── Node Health ──────────────────────────────────────────────────
        self.register(
            ReactionTrigger.NODE_UNREACHABLE,
            PolicyAction.ADD_OBSERVATION,
            condition=lambda c: c.get("consecutive_failures", 0) < 3,
            cooldown=10.0,
            priority=50,
            label="node_unreachable_early→observe",
        )
        self.register(
            ReactionTrigger.NODE_UNREACHABLE,
            PolicyAction.EVICT_NODE,
            condition=lambda c: c.get("consecutive_failures", 0) >= 3,
            priority=90,
            label="node_unreachable_late→evict",
        )
        self.register(
            ReactionTrigger.NODE_RECOVERED,
            PolicyAction.RESTORE_NODE,
            priority=40,
            label="node_recovered→restore",
        )

        # ── Partition ────────────────────────────────────────────────────
        self.register(
            ReactionTrigger.PARTITION_DETECTED,
            PolicyAction.TRIGGER_SELF_HEAL,
            priority=85,
            label="partition_detected→heal",
        )
        self.register(
            ReactionTrigger.PARTITION_HEALED,
            PolicyAction.RECONFIGURE_QUORUM,
            cooldown=15.0,
            priority=50,
            label="partition_healed→reconfigure",
        )

        # ── Byzantine ──────────────────────────────────────────────────
        self.register(
            ReactionTrigger.BYZANTINE_SIGNAL,
            PolicyAction.ISOLATE_BYZANTINE,
            priority=100,
            label="byzantine→isolate",
        )
        self.register(
            ReactionTrigger.CLOCK_SKEW_EXCEEDED,
            PolicyAction.ADD_OBSERVATION,
            cooldown=20.0,
            priority=40,
            label="clock_skew→observe",
        )

        # ── DRL / Network SLO ──────────────────────────────────────────
        self.register(
            ReactionTrigger.DRL_LATENCY_EXCEEDED,
            PolicyAction.ADD_OBSERVATION,
            cooldown=30.0,
            priority=30,
            label="latency_slo→observe",
        )
        self.register(
            ReactionTrigger.DRL_LOSS_EXCEEDED,
            PolicyAction.ADD_OBSERVATION,
            cooldown=20.0,
            priority=35,
            label="loss_slo→observe",
        )

        # ── Healing ─────────────────────────────────────────────────────
        self.register(
            ReactionTrigger.RECOVERY_COMPLETE,
            PolicyAction.RECONFIGURE_QUORUM,
            cooldown=10.0,
            priority=45,
            label="recovery_done→reconfigure",
        )
        self.register(
            ReactionTrigger.NODE_EVICTED,
            PolicyAction.RECONFIGURE_QUORUM,
            cooldown=5.0,
            priority=70,
            label="node_evicted→reconfigure",
        )
        self.register(
            ReactionTrigger.NODE_JOINED,
            PolicyAction.RECONFIGURE_QUORUM,
            cooldown=5.0,
            priority=70,
            label="node_joined→reconfigure",
        )

        # ── Stability ───────────────────────────────────────────────────
        self.register(
            ReactionTrigger.STABILITY_SCORE_LOW,
            PolicyAction.ALERT_OPS,
            condition=lambda c: c.get("score", 1.0) < 0.3,
            priority=80,
            label="stability_critical→alert",
        )
        self.register(
            ReactionTrigger.STABILITY_SCORE_LOW,
            PolicyAction.TRIGGER_SELF_HEAL,
            condition=lambda c: c.get("score", 1.0) >= 0.3,
            priority=60,
            label="stability_low→heal",
        )

    # ── Introspection ────────────────────────────────────────────────────────

    def get_log(self, last_n: int | None = None) -> list[dict]:
        log = list(reversed(self._log))
        if last_n is not None:
            return log[:last_n]
        return log

    def list_rules(self) -> list[PolicyRule]:
        return list(self._rules)

    def dump(self) -> dict:
        return {
            "rules": [
                {"label": r.label, "trigger": r.trigger.name,
                 "action": r.action.name, "priority": r.priority,
                 "cooldown_s": r.cooldown_seconds}
                for r in self._rules
            ],
            "log_count": len(self._log),
        }

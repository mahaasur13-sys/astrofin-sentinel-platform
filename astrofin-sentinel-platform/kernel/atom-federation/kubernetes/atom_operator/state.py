"""ATOMCluster controller — custom ATOM state snapshot."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def _parse_heal_time(value) -> float | None:
    """
    Tolerate both numeric epochs and ISO-8601 strings on the way in.

    The CRD returns ``lastHealTime`` as a UTC string ("2026-06-19T12:00:00Z")
    but the controller code originally worked in epoch floats. The dataclass
    therefore has to accept both representations without crashing.
    """
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # ISO-8601 with trailing Z is the format the CRD emits.
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    return None


def _format_heal_time(value: float | None) -> str:
    if value is None:
        return ""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(value))


@dataclass
class NodeState:
    node_id: str
    status: str = "unknown"
    sbs_violation_rate: float = 0.0
    coherence_drift: float = 0.0
    last_heal_time: float | None = None
    restart_count: int = 0

    def to_k8s(self) -> dict:
        return {
            "nodeId": self.node_id,
            "status": self.status,
            "sbsViolationRate": self.sbs_violation_rate,
            "coherenceDrift": self.coherence_drift,
            "lastHealTime": _format_heal_time(self.last_heal_time),
        }

    @classmethod
    def from_k8s(cls, data: dict) -> NodeState:
        return cls(
            node_id=data.get("nodeId", ""),
            status=data.get("status", "unknown"),
            sbs_violation_rate=float(data.get("sbsViolationRate", 0.0)),
            coherence_drift=float(data.get("coherenceDrift", 0.0)),
            last_heal_time=_parse_heal_time(data.get("lastHealTime")),
            restart_count=int(data.get("restartCount", 0)),
        )


@dataclass
class ClusterState:
    name: str
    namespace: str
    replicas: int
    sbs_threshold: float = 0.01
    coherence_drift_max: float = 0.05
    phase: str = "Pending"
    ready_replicas: int = 0
    sbs_violation_rate: float = 0.0
    coherence_drift: float = 0.0
    quorum_safe: bool = False
    current_version: str = "7.0.0"
    nodes: list[NodeState] = field(default_factory=list)
    conditions: list[dict] = field(default_factory=list)

    @property
    def health_ratio(self) -> float:
        if self.replicas == 0:
            return 0.0
        return self.ready_replicas / self.replicas

    @property
    def needs_healing(self) -> bool:
        return self.sbs_violation_rate > self.sbs_threshold

    @property
    def needs_throttle(self) -> bool:
        return self.coherence_drift > self.coherence_drift_max

    @property
    def is_quorum_breached(self) -> bool:
        return self.ready_replicas < (self.replicas // 2 + 1)

    def to_k8s_status(self) -> dict:
        return {
            "phase": self.phase,
            "readyReplicas": self.ready_replicas,
            "sbsViolationRate": round(self.sbs_violation_rate, 6),
            "coherenceDrift": round(self.coherence_drift, 6),
            "quorumSafe": self.quorum_safe,
            "currentVersion": self.current_version,
            "nodeStates": [n.to_k8s() for n in self.nodes],
            "conditions": self.conditions,
        }

    def to_dict(self) -> dict:
        d = asdict(self)
        d["health_ratio"] = self.health_ratio
        d["needs_healing"] = self.needs_healing
        d["needs_throttle"] = self.needs_throttle
        d["is_quorum_breached"] = self.is_quorum_breached
        return d

    @classmethod
    def from_k8s(cls, cluster: dict) -> ClusterState:
        meta = cluster.get("metadata", {})
        spec = cluster.get("spec", {})
        status = cluster.get("status", {})
        node_states = [
            NodeState.from_k8s(n) for n in status.get("nodeStates", [])
        ]
        return cls(
            name=meta.get("name", ""),
            namespace=meta.get("namespace", "default"),
            replicas=int(spec.get("replicas", 3)),
            sbs_threshold=float(spec.get("sbsThreshold", 0.01)),
            coherence_drift_max=float(spec.get("coherenceDriftMax", 0.05)),
            phase=status.get("phase", "Pending"),
            ready_replicas=int(status.get("readyReplicas", 0)),
            sbs_violation_rate=float(status.get("sbsViolationRate", 0.0)),
            coherence_drift=float(status.get("coherenceDrift", 0.0)),
            quorum_safe=bool(status.get("quorumSafe", False)),
            current_version=status.get("currentVersion", "7.0.0"),
            nodes=node_states,
            conditions=status.get("conditions", []),
        )

"""
Cluster Health Graph — per-node state: reachable / lag / last_seen / violation_score.
"""
import threading
import time
from dataclasses import dataclass
from enum import Enum


class NodeState(Enum):
    UNKNOWN = "unknown"
    REACHABLE = "reachable"
    LAGGING = "lagging"
    UNREACHABLE = "unreachable"
    VIOLATION = "violation"


@dataclass
class PeerHealth:
    peer_id: str
    state: NodeState = NodeState.UNKNOWN
    last_seen: float = 0.0
    lag_ms: float = 0.0
    violation_score: float = 0.0
    consecutive_fails: int = 0
    last_ping_ok: bool = False

    def mark_ok(self, lag_ms: float):
        self.last_seen = time.time()
        self.lag_ms = lag_ms
        self.consecutive_fails = 0
        self.last_ping_ok = True
        if self.violation_score > 0:
            self.violation_score = max(0, self.violation_score - 0.1)
        if self.state in (NodeState.UNREACHABLE, NodeState.LAGGING):
            self.state = NodeState.REACHABLE if lag_ms < 100 else NodeState.LAGGING

    def mark_fail(self):
        self.consecutive_fails += 1
        self.last_ping_ok = False
        if self.consecutive_fails >= 3:
            self.state = NodeState.UNREACHABLE

    def mark_violation(self, weight: float = 1.0):
        self.violation_score = min(10.0, self.violation_score + weight)
        if self.violation_score >= 3.0:
            self.state = NodeState.VIOLATION

    def to_dict(self) -> dict:
        return {
            "peer_id": self.peer_id,
            "state": self.state.value,
            "last_seen": self.last_seen,
            "lag_ms": self.lag_ms,
            "violation_score": self.violation_score,
            "consecutive_fails": self.consecutive_fails,
            "last_ping_ok": self.last_ping_ok,
        }


class ClusterHealthGraph:
    """
    Maintains live health state for all peers of a node.

    Usage:
        health = ClusterHealthGraph("node-a", ["node-b", "node-c"])
        health.mark_ok("node-b", lag_ms=12.4)
        health.mark_violation("node-c")
        print(health.get_all())
    """

    DEGRADED_LAG_MS = 100.0   # >100ms = lagging
    VIOLATION_THRESHOLD = 3.0

    def __init__(self, node_id: str, peers: list[str]):
        self.node_id = node_id
        self._peers: dict[str, PeerHealth] = {
            p: PeerHealth(peer_id=p) for p in peers
        }
        self._lock = threading.RLock()

    def mark_ok(self, peer_id: str, lag_ms: float = 0.0):
        with self._lock:
            if peer_id in self._peers:
                self._peers[peer_id].mark_ok(lag_ms)
                if lag_ms > self.DEGRADED_LAG_MS:
                    self._peers[peer_id].state = NodeState.LAGGING

    def mark_fail(self, peer_id: str):
        with self._lock:
            if peer_id in self._peers:
                self._peers[peer_id].mark_fail()

    def mark_violation(self, peer_id: str, weight: float = 1.0):
        with self._lock:
            if peer_id in self._peers:
                self._peers[peer_id].mark_violation(weight)
                if self._peers[peer_id].violation_score >= self.VIOLATION_THRESHOLD:
                    self._peers[peer_id].state = NodeState.VIOLATION

    def get(self, peer_id: str) -> PeerHealth | None:
        with self._lock:
            return self._peers.get(peer_id)

    def get_all(self) -> dict[str, dict]:
        with self._lock:
            return {pid: p.to_dict() for pid, p in self._peers.items()}

    def summary(self) -> dict:
        with self._lock:
            states = [p.state for p in self._peers.values()]
            return {
                "node_id": self.node_id,
                "total_peers": len(self._peers),
                "reachable": sum(1 for s in states if s == NodeState.REACHABLE),
                "lagging": sum(1 for s in states if s == NodeState.LAGGING),
                "unreachable": sum(1 for s in states if s == NodeState.UNREACHABLE),
                "violation": sum(1 for s in states if s == NodeState.VIOLATION),
                "unknown": sum(1 for s in states if s == NodeState.UNKNOWN),
            }

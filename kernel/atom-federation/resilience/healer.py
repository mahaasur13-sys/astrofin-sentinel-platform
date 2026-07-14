"""
SelfHealingControlPlane v6.4 — Node lifecycle + reconfiguration.

Healing actions:
  - EVICT_NODE         → graceful removal + quorum reconfiguration
  - RESTORE_NODE       → bring node back to full service
  - TRIGGER_RE_ELECTION → force leader re-election
  - ISOLATE_BYZANTINE  → quarantine malicious node
  - RECONFIGURE_QUORUM → recalculate F2 quorum membership
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto

__all__ = ["HealingAction", "HealingResult", "SelfHealingControlPlane"]


class HealingAction(Enum):
    EVICT_NODE = auto()
    RESTORE_NODE = auto()
    TRIGGER_RE_ELECTION = auto()
    ISOLATE_BYZANTINE = auto()
    RECONFIGURE_QUORUM = auto()
    DRAIN_NODE = auto()
    INITIATE_NODE_JOIN = auto()


@dataclass
class HealingResult:
    action: HealingAction
    target: str | None
    success: bool
    duration_ms: float
    details: dict = field(default_factory=dict)
    error: str | None = None

    def __repr__(self) -> str:
        status = "✓" if self.success else "✗"
        return (
            f"HealingResult({self.action.name} {status}"
            + (f" target={self.target}" if self.target else "")
            + f" {self.duration_ms:.1f}ms)"
            + (f" err={self.error!r}" if self.error else "")
        )


class QuorumConfig:
    __slots__ = ('last_reconfigured', 'members', 'required_ratio')
    def __init__(self, members=None, required_ratio=0.71, last_reconfigured=0.0):
        object.__setattr__(self, 'members', list(members) if members else [])
        object.__setattr__(self, 'required_ratio', float(required_ratio))
        object.__setattr__(self, 'last_reconfigured', float(last_reconfigured))
    def quorum_size(self) -> int:
        return max(1, int(len(self.members) * self.required_ratio))
    def is_quorate(self) -> bool:
        return len(self.members) >= self.quorum_size()
    def __repr__(self):
        return f'QuorumConfig(members={self.members!r}, ratio={self.required_ratio})'
    def __eq__(self, other):
        if not isinstance(other, QuorumConfig): return NotImplemented
        return (self.members == other.members and
                self.required_ratio == other.required_ratio and
                self.last_reconfigured == other.last_reconfigured)


class SelfHealingControlPlane:
    """
    Executes healing actions on the cluster.
    Acts as the "executor" layer for ResilienceReactor callbacks.
    """

    def __init__(
        self,
        node_id: str,
        peers: list[str],
        grpc_stub_factory: Callable[[str], object] | None = None,
    ) -> None:
        self.node_id = node_id
        self.peers = list(peers)
        self._grpc_factory = grpc_stub_factory
        self._quorum = QuorumConfig(members=list(peers + [node_id]))
        self._quorum_lock = threading.RLock()
        self._evicted: set[str] = set()
        self._byzantine: set[str] = set()
        self._drained: set[str] = set()
        self._heal_queue: list[tuple[HealingAction, str | None, Callable | None]] = []
        self._heal_thread: threading.Thread | None = None
        self._heal_lock = threading.Lock()
        self._running = False
        self._result_cbs: list[Callable[[HealingResult], None]] = []
        self._log: list[dict] = []
        self._heal_count = 0

    def start(self) -> None:
        self._running = True
        self._heal_thread = threading.Thread(target=self._heal_loop, daemon=True)
        self._heal_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._heal_thread:
            self._heal_thread.join(timeout=3.0)

    def on_result(self, cb: Callable[[HealingResult], None]) -> None:
        self._result_cbs.append(cb)

    def heal(
        self,
        action: HealingAction,
        target: str | None = None,
        result_cb: Callable[[HealingResult], None] | None = None,
    ) -> None:
        with self._heal_lock:
            self._heal_queue.append((action, target, result_cb))

    def heal_sync(self, action: HealingAction, target: str | None = None) -> HealingResult:
        return self._execute(action, target)

    def _heal_loop(self) -> None:
        while self._running:
            time.sleep(0.1)
            with self._heal_lock:
                if not self._heal_queue:
                    continue
                action, target, result_cb = self._heal_queue.pop(0)
            result = self._execute(action, target)
            for cb in self._result_cbs:
                try:
                    cb(result)
                except Exception:
                    pass
            if result_cb:
                try:
                    result_cb(result)
                except Exception:
                    pass

    def _execute(self, action: HealingAction, target: str | None) -> HealingResult:
        self._heal_count += 1
        start = time.monotonic()
        try:
            if action == HealingAction.EVICT_NODE:
                return self._evict_node(target)
            elif action == HealingAction.RESTORE_NODE:
                return self._restore_node(target)
            elif action == HealingAction.TRIGGER_RE_ELECTION:
                return self._trigger_reelection()
            elif action == HealingAction.ISOLATE_BYZANTINE:
                return self._isolate_byzantine(target)
            elif action == HealingAction.RECONFIGURE_QUORUM:
                return self._reconfigure_quorum()
            elif action == HealingAction.DRAIN_NODE:
                return self._drain_node(target)
            elif action == HealingAction.INITIATE_NODE_JOIN:
                return self._initiate_node_join(target)
            else:
                return HealingResult(action, target, False, (time.monotonic() - start) * 1000,
                                     error=f"Unknown action: {action}")
        except Exception as exc:
            return HealingResult(action, target, False, (time.monotonic() - start) * 1000,
                                 error=str(exc))

    def _evict_node(self, node: str | None) -> HealingResult:
        if not node:
            return HealingResult(HealingAction.EVICT_NODE, None, False, 0, error="no target")
        start = time.monotonic()
        self._evicted.add(node)
        with self._quorum_lock:
            if node in self._quorum.members:
                self._quorum.members.remove(node)
            self._quorum.last_reconfigured = start
        self._update_drl_routing()
        self._log_event("evict_node", node, True)
        return HealingResult(HealingAction.EVICT_NODE, node, True, (time.monotonic() - start) * 1000,
                             details={"quorum_size": len(self._quorum.members),
                                      "quorum_members": list(self._quorum.members)})

    def _restore_node(self, node: str | None) -> HealingResult:
        if not node:
            return HealingResult(HealingAction.RESTORE_NODE, None, False, 0, error="no target")
        start = time.monotonic()
        self._evicted.discard(node)
        self._drained.discard(node)
        with self._quorum_lock:
            if node not in self._quorum.members:
                self._quorum.members.append(node)
            self._quorum.last_reconfigured = start
        self._update_drl_routing()
        self._log_event("restore_node", node, True)
        return HealingResult(HealingAction.RESTORE_NODE, node, True, (time.monotonic() - start) * 1000,
                             details={"quorum_members": list(self._quorum.members)})

    def _trigger_reelection(self) -> HealingResult:
        start = time.monotonic()
        for peer in self._active_peers():
            self._notify_peer(peer, "start_election")
        self._log_event("trigger_reelection", None, True)
        return HealingResult(HealingAction.TRIGGER_RE_ELECTION, None, True,
                             (time.monotonic() - start) * 1000,
                             details={"notified": len(self._active_peers())})

    def _isolate_byzantine(self, node: str | None) -> HealingResult:
        if not node:
            return HealingResult(HealingAction.ISOLATE_BYZANTINE, None, False, 0, error="no target")
        start = time.monotonic()
        self._byzantine.add(node)
        self._evicted.add(node)
        with self._quorum_lock:
            if node in self._quorum.members:
                self._quorum.members.remove(node)
        self._update_drl_routing()
        for peer in self._active_peers():
            self._notify_peer(peer, "quarantine", {"node": node})
        self._log_event("isolate_byzantine", node, True)
        return HealingResult(HealingAction.ISOLATE_BYZANTINE, node, True,
                             (time.monotonic() - start) * 1000,
                             details={"byzantine_set": list(self._byzantine)})

    def _reconfigure_quorum(self) -> HealingResult:
        start = time.monotonic()
        with self._quorum_lock:
            old = list(self._quorum.members)
            self._quorum.members = [
                n for n in (self.peers + [self.node_id])
                if n not in self._evicted and n not in self._byzantine
            ]
            self._quorum.last_reconfigured = start
        self._update_drl_routing()
        self._log_event("reconfigure_quorum", None, True)
        return HealingResult(HealingAction.RECONFIGURE_QUORUM, None, True,
                             (time.monotonic() - start) * 1000,
                             details={"old": len(old), "new": len(self._quorum.members),
                                      "members": list(self._quorum.members),
                                      "quorum_size": self._quorum.quorum_size(),
                                      "is_quorate": self._quorum.is_quorate()})

    def _drain_node(self, node: str | None) -> HealingResult:
        if not node:
            return HealingResult(HealingAction.DRAIN_NODE, None, False, 0, error="no target")
        start = time.monotonic()
        self._drained.add(node)
        self._update_drl_routing()
        self._log_event("drain_node", node, True)
        return HealingResult(HealingAction.DRAIN_NODE, node, True, (time.monotonic() - start) * 1000)

    def _initiate_node_join(self, new_node: str | None) -> HealingResult:
        if not new_node:
            return HealingResult(HealingAction.INITIATE_NODE_JOIN, None, False, 0, error="no target")
        start = time.monotonic()
        self._evicted.discard(new_node)
        self._drained.discard(new_node)
        if new_node not in self.peers:
            self.peers.append(new_node)
        self._reconfigure_quorum()
        for peer in self._active_peers():
            self._notify_peer(peer, "node_join", {"node": new_node})
        self._log_event("node_join", new_node, True)
        return HealingResult(HealingAction.INITIATE_NODE_JOIN, new_node, True,
                             (time.monotonic() - start) * 1000)

    def _active_peers(self) -> list[str]:
        return [p for p in self.peers
                if p not in self._evicted and p not in self._byzantine and p not in self._drained]

    def _notify_peer(self, peer: str, action: str, payload: dict | None = None) -> bool:
        if not self._grpc_factory:
            return False
        try:
            self._grpc_factory(peer)
            return True
        except Exception:
            return False

    def _update_drl_routing(self) -> None:
        active = self._active_peers()
        self._log_event("drl_routing_update", None, True, {"active": active})

    def _log_event(self, op: str, target: str | None, success: bool,
                   details: dict | None = None) -> None:
        self._log.append({"ts": time.monotonic(), "op": op, "target": target,
                          "success": success, "details": details or {},
                          "heal_n": self._heal_count})

    def get_evicted(self) -> set[str]:
        return set(self._evicted)

    def get_byzantine(self) -> set[str]:
        return set(self._byzantine)

    def get_quorum(self) -> QuorumConfig:
        with self._quorum_lock:
            return QuorumConfig(members=list(self._quorum.members),
                                required_ratio=self._quorum.required_ratio,
                                last_reconfigured=self._quorum.last_reconfigured)

    def is_quorate(self) -> bool:
        return self._quorum.is_quorate()

    def get_quorum_members(self) -> list[str]:
        with self._quorum_lock:
            return list(self._quorum.members)

    def heal_count(self) -> int:
        return self._heal_count

    def get_log(self, last_n: int | None = None) -> list[dict]:
        log = list(reversed(self._log))
        return log[:last_n] if last_n is not None else log

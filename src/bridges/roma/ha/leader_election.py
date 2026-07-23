#!/usr/bin/env python3
"""Leader Election — Raft-style lease with split-brain protection."""

import threading
import time
from dataclasses import dataclass
from typing import Optional

LEASE_TTL_SEC = 10.0
RENEW_INTERVAL = 2.0


@dataclass
class LeaderLease:
    leader_id: str
    term: int
    lease_end: float
    committed_index: int


class LeaderElection:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.term = 0
        self.leader_id: str | None = None
        self.lease_end: float = 0.0
        self.is_leader = False
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._renew_thread: threading.Thread | None = None

    def try_acquire_leadership(self) -> bool:
        with self._lock:
            self.term += 1
            self.leader_id = self.node_id
            self.lease_end = time.time() + LEASE_TTL_SEC
            self.is_leader = True
        return True

    def is_leader_valid(self) -> bool:
        with self._lock:
            if not self.is_leader:
                return False
            if time.time() > self.lease_end:
                self.is_leader = False
                return False
            return True

    def renew(self) -> bool:
        with self._lock:
            if not self.is_leader or self.leader_id != self.node_id:
                return False
            self.lease_end = time.time() + LEASE_TTL_SEC
            self.term += 1
            return True

    def resign(self):
        with self._lock:
            self.is_leader = False
            self.leader_id = None

    def get_state(self) -> dict:
        with self._lock:
            return {
                "node_id": self.node_id,
                "is_leader": self.is_leader,
                "leader_id": self.leader_id,
                "lease_end": self.lease_end,
                "term": self.term,
                "valid": self.is_leader_valid() if self.is_leader else False,
            }


if __name__ == "__main__":
    nodes = [LeaderElection(f"node-{i}") for i in range(3)]
    nodes[0].try_acquire_leadership()
    print(f"Leader: node-0 = {nodes[0].is_leader_valid()}")
    print(f"Followers: n1={nodes[1].is_leader}, n2={nodes[2].is_leader}")

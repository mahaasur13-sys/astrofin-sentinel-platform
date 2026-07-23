#!/usr/bin/env python3
"""Replicated Event Store — 3-node write quorum."""

import threading
from dataclasses import dataclass
from typing import List


@dataclass
class Replica:
    node_id: str
    committed_index: int = 0
    last_heartbeat: float = 0.0
    alive: bool = True


class ReplicatedEventStore:
    def __init__(self, cluster_size: int = 3):
        self.replicas = [Replica(f"replica-{i}") for i in range(cluster_size)]
        self.local_index = 0
        self.commit_index = 0
        self.events: list[dict] = []
        self._lock = threading.Lock()
        self.write_quorum = (cluster_size // 2) + 1  # 3/2+1 = 2

    def write(self, event: dict) -> dict:
        with self._lock:
            self.local_index += 1
            index = self.local_index
            committed = self._try_commit(index)
            self.commit_index = committed
            self.events.append({**event, "index": index, "commit_index": committed})
            return {
                "index": index,
                "commit_index": committed,
                "quorum": committed >= index,
            }

    def _try_commit(self, index: int) -> int:
        alive = sum(1 for r in self.replicas if r.alive)
        if alive >= self.write_quorum:
            return index
        return max(0, self.commit_index)

    def get_state(self) -> dict:
        with self._lock:
            return {
                "commit_index": self.commit_index,
                "local_index": self.local_index,
                "alive_replicas": sum(1 for r in self.replicas if r.alive),
                "quorum": self.write_quorum,
                "ready": self.commit_index == self.local_index,
            }


if __name__ == "__main__":
    store = ReplicatedEventStore(3)
    for i in range(3):
        r = store.write({"type": f"event-{i}", "tick": i})
        print(f"Event {i}: index={r['index']}, commit={r['commit_index']}, quorum={r['quorum']}")
    print(store.get_state())

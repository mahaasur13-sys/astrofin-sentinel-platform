#!/usr/bin/env python3
"""Split-Brain Protection — majority quorum enforcement."""

import time
from typing import Dict


class SplitBrainProtection:
    def __init__(self, cluster_nodes: int = 3):
        self.majority = (cluster_nodes // 2) + 1
        self.node_status: Dict[str, dict] = {}
        self.active_nodes: set = set()

    def register_heartbeat(self, node_id: str) -> bool:
        now = time.time()
        self.node_status[node_id] = {"last_seen": now, "alive": True}
        self.active_nodes = {n for n, s in self.node_status.items() if s["alive"] and now - s["last_seen"] < 15}
        return len(self.active_nodes) >= self.majority

    def is_majority(self) -> bool:
        return len(self.active_nodes) >= self.majority

    def can_write(self) -> bool:
        return self.is_majority()

    def get_status(self) -> dict:
        return {
            "active_nodes": list(self.active_nodes),
            "majority": self.majority,
            "can_write": self.can_write(),
            "quorum_met": len(self.active_nodes) >= self.majority,
        }


if __name__ == "__main__":
    sbp = SplitBrainProtection(3)
    print(sbp.get_status())
    for i in range(3):
        sbp.register_heartbeat(f"node-{i}")
    print(sbp.get_status())

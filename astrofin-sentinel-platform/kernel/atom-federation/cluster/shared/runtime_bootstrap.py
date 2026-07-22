"""
Runtime bootstrap — wires ClusterNode from components.
"""
import os
import sys

import logging
log = logging.getLogger(__name__)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# DRLBridge lives in shared/ alongside this file — use relative import

from cluster.node.node import ClusterNode


class BootstrapNode:
    def __init__(self, node_id: str, peers: list[str]):
        self.node_id = node_id
        self.peers = peers
        self.node = None
        self._running = False

    def start(self):
        log.info(f"[BOOT] {self.node_id} starting with peers: {self.peers}")

        self.node = ClusterNode(node_id=self.node_id, peers=self.peers)
        self.node.start()

        self._running = True
        log.info(f"[BOOT] {self.node_id} fully ready (ClusterNode + all layers)")

    def stop(self):
        self._running = False
        if self.node:
            self.node.stop()
        log.info(f"[SHUTDOWN] {self.node_id} stopped")

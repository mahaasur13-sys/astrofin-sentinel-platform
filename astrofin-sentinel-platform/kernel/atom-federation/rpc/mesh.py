"""
Node mesh — manages the full connection graph of an ATOM cluster.
Discovers peers, routes messages, handles reconnection.
"""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass
from typing import Any

from .client import RPCClient
from .proto import atom_pb2


@dataclass
class NodeEndpoint:
    """Static or dynamically discovered peer."""
    node_id: str
    address: str
    port: int
    client: RPCClient | None = None
    online: bool = False
    last_seen: float = 0.0

    def url(self) -> str:
        return f"{self.address}:{self.port}"


class NodeMesh:
    """
    Full-mesh or star topology RPC manager.
    Each NodeMesh instance is owned by one local node.
    """

    def __init__(self, self_node_id: str, self_address: str = "localhost") -> None:
        self.self_node_id = self_node_id
        self.self_address = self_address
        self._endpoints: dict[str, NodeEndpoint] = {}
        self._lock = threading.RLock()
        self._routing_lock = asyncio.Lock()

    def add_peer(self, node_id: str, address: str, port: int) -> None:
        with self._lock:
            ep = NodeEndpoint(node_id=node_id, address=address, port=port)
            self._endpoints[node_id] = ep

    def remove_peer(self, node_id: str) -> None:
        with self._lock:
            ep = self._endpoints.pop(node_id, None)
            if ep and ep.client:
                ep.client.close()

    def connect_all(self) -> None:
        """Eager-connect to all registered peers."""
        with self._lock:
            for ep in self._endpoints.values():
                if ep.client is None:
                    ep.client = RPCClient(ep.url(), self.self_node_id)
                    ep.online = True
                    ep.last_seen = time.time()

    def send_to(self, node_id: str, msg: atom_pb2.AtomMessage) -> bool:
        """
        Unicast — send to a specific peer.
        Returns True if ack received.
        """
        with self._lock:
            ep = self._endpoints.get(node_id)
        if ep is None or ep.client is None:
            return False
        ack = ep.client.send(msg)
        if ack and ack.ok:
            ep.online = True
            ep.last_seen = time.time()
            return True
        return False

    def broadcast(self, msg: atom_pb2.AtomMessage) -> dict[str, bool]:
        """
        Fan-out to all connected peers.
        Returns {node_id: success}.
        """
        results = {}
        with self._lock:
            endpoints = list(self._endpoints.items())
        for node_id, ep in endpoints:
            if ep.client is None:
                results[node_id] = False
                continue
            ack = ep.client.send(msg)
            ok = ack is not None and ack.ok
            results[node_id] = ok
            with self._lock:
                ep.online = ok
                if ok:
                    ep.last_seen = time.time()
        return results

    def get_endpoint(self, node_id: str) -> NodeEndpoint | None:
        with self._lock:
            return self._endpoints.get(node_id)

    def get_online_peers(self) -> list[str]:
        with self._lock:
            return [nid for nid, ep in self._endpoints.items() if ep.online]

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "self": self.self_node_id,
                "peers": {
                    nid: {
                        "address": ep.url(),
                        "online": ep.online,
                        "last_seen": ep.last_seen,
                        **(ep.client.get_stats() if ep.client else {}),
                    }
                    for nid, ep in self._endpoints.items()
                },
            }

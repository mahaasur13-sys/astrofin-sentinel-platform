"""
gRPC client — node-to-node unidirectional send.
Thread-safe, connection-pooled, handles reconnection.
"""

from __future__ import annotations

import random
import threading
import time
from typing import Any

import grpc
from grpc import Channel

from .proto import atom_pb2, atom_pb2_grpc


class RPCClient:
    """
    Stateful connection to a single remote AtomNode.
    Thread-safe: multiple threads may call send() concurrently.
    """

    def __init__(
        self,
        address: str,
        node_id: str,
        max_retries: int = 3,
        timeout_sec: float = 5.0,
    ) -> None:
        self.address = address
        self.node_id = node_id
        self.max_retries = max_retries
        self.timeout_sec = timeout_sec

        self._lock = threading.Lock()
        self._channel: Channel | None = None
        self._stub: atom_pb2_grpc.AtomNodeStub | None = None
        self._stats = {"ok": 0, "fail": 0, "latency_ms": []}

    def _ensure_channel(self) -> Channel:
        with self._lock:
            if self._channel is None:
                self._channel = grpc.insecure_channel(
                    self.address,
                    options=[
                        ("grpc.max_send_message_length", 50 * 1024 * 1024),
                        ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                        ("grpc.keepalive_time_ms", 10000),
                        ("grpc.http2.min_time_between_pings_ms", 10000),
                    ],
                )
                self._stub = atom_pb2_grpc.AtomNodeStub(self._channel)
            return self._channel

    def send(self, msg: atom_pb2.AtomMessage) -> atom_pb2.Ack | None:
        """
        Send an AtomMessage to the remote node.
        Returns Ack on success, None on final failure.
        Retries with backoff on transient errors.
        """
        for attempt in range(self.max_retries):
            try:
                stub = self._ensure_channel()._stub if hasattr(self._ensure_channel(), "_stub") else self._stub
                start = time.monotonic()
                ack = stub.SendMessage(msg, timeout=self.timeout_sec)
                elapsed = (time.monotonic() - start) * 1000
                with self._lock:
                    self._stats["ok"] += 1
                    self._stats["latency_ms"].append(elapsed)
                return ack
            except grpc.RpcError as e:
                code = e.code()
                with self._lock:
                    self._stats["fail"] += 1
                if code in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.RESOURCE_EXHAUSTED):
                    time.sleep(0.1 * (2 ** attempt) + random.uniform(0, 0.05))
                    continue
                return None
        return None

    def send_stream(self, messages: list[atom_pb2.AtomMessage]) -> list[atom_pb2.Ack]:
        """Streaming send for batched delivery."""
        stub = self._stub
        if stub is None:
            return []
        results = []
        for msg in messages:
            ack = self.send(msg)
            if ack is None:
                break
            results.append(ack)
        return results

    def close(self) -> None:
        with self._lock:
            if self._channel is not None:
                self._channel.close()
                self._channel = None
                self._stub = None

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            latencies = self._stats.get("latency_ms", [])
            return {
                "ok": self._stats["ok"],
                "fail": self._stats["fail"],
                "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            }

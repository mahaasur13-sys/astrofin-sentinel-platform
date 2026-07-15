"""
gRPC server — exposes AtomNode service.
Each node process runs one server that handles inbound messages.
"""

from __future__ import annotations

import queue
import threading
from typing import Any

import grpc

from .proto import atom_pb2, atom_pb2_grpc


class AtomServicer(atom_pb2_grpc.AtomNodeServicer):
    """
    gRPC servicer that bridges real network → local runtime receive queue.
    SBS enforcement, ordering, and DRL processing happen upstream in the adapter.
    """

    def __init__(
        self,
        runtime: Any,
        node_id: str,
        inbound_queue: queue.Queue | None = None,
    ) -> None:
        self.runtime = runtime
        self.node_id = node_id
        self._inbound = inbound_queue or queue.Queue()
        self._seq_lock = threading.Lock()
        self._seq: int = 0
        self._peer_stats: dict[str, int] = {}

    @property
    def inbound_queue(self) -> queue.Queue:
        return self._inbound

    def _next_seq(self) -> int:
        with self._seq_lock:
            s = self._seq
            self._seq += 1
            return s

    # ── Unary ─────────────────────────────────────────────────────────────────

    def SendMessage(self, request: atom_pb2.AtomMessage, context: grpc.ServicerContext) -> atom_pb2.Ack:
        self._inbound.put(request)
        seq = self._next_seq()

        src = request.source or "unknown"
        self._peer_stats[src] = self._peer_stats.get(src, 0) + 1

        return atom_pb2.Ack(
            ok=True,
            msg_id=request.msg_id,
            seq=seq,
        )

    # ── Streaming ─────────────────────────────────────────────────────────────

    def StreamMessages(
        self,
        request_iterator: Any,
        context: grpc.ServicerContext,
    ) -> Any:
        for request in request_iterator:
            self._inbound.put(request)
            seq = self._next_seq()
            yield atom_pb2.Ack(
                ok=True,
                msg_id=request.msg_id,
                seq=seq,
            )

    def get_peer_stats(self) -> dict[str, int]:
        return dict(self._peer_stats)


def create_server(
    runtime: Any,
    node_id: str,
    port: int = 50051,
    inbound_queue: queue.Queue | None = None,
) -> grpc.Server:
    """
    Build and return a gRPC server bound to [::]:port.
    """
    server = grpc.server(
        _futures := __import__("concurrent.futures", fromlist=["futures"]).ThreadPoolExecutor(
            max_workers=10,
        ),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ("grpc.keepalive_time_ms", 10000),
            ("grpc.keepalive_timeout_ms", 3000),
        ],
    )
    atom_pb2_grpc.add_AtomNodeServicer_to_server(
        AtomServicer(runtime, node_id, inbound_queue),
        server,
    )
    server.add_insecure_port(f"[::]:{port}")
    return server


def serve_forever(
    runtime: Any,
    node_id: str,
    port: int = 50051,
    inbound_queue: queue.Queue | None = None,
) -> None:
    """
    Synchronous entrypoint — blocks the calling thread.
    Use inside a daemon thread for non-blocking behaviour.
    """
    server = create_server(runtime, node_id, port, inbound_queue)
    server.start()
    print(f"[atom.server:{node_id}] listening on [::{port}]")
    server.wait_for_termination()

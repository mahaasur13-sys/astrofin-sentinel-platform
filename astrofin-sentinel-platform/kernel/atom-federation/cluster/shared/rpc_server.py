"""
gRPC RPC Server — real TCP connections between cluster nodes.

v6.2 changes:
  • Fixed ports per node (from NODE_PORT env)
  • Connection pool (cached channels per peer)
  • Retry/backoff on peer calls
  • Outbound peer discovery via broadcast
"""
import os
import random
import sys
import threading
import time
from concurrent import futures

import grpc

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import proto.atom_os_pb2 as pb2
import proto.atom_os_pb2_grpc as pb2_grpc

# Fixed port map — must match docker-compose.yml
PORT_MAP = {
    "node-a": 50051,
    "node-b": 50052,
    "node-c": 50053,
}
DEFAULT_PORT = 50051


class ConnectionPool:
    """
    Thread-safe gRPC channel pool per peer.
    Avoids repeated channel creation overhead.
    """

    def __init__(self, max_workers: int = 10):
        self._channels: dict[str, grpc.Channel] = {}
        self._stubs: dict[str, pb2_grpc.NodeRPCStub] = {}
        self._lock = threading.RLock()
        self._max_workers = max_workers

    def get_stub(self, peer_id: str, target: str) -> pb2_grpc.NodeRPCStub:
        with self._lock:
            if peer_id not in self._channels:
                channel = grpc.insecure_channel(
                    target,
                    options=[
                        ("grpc.max_send_message_length", 10 * 1024 * 1024),
                        ("grpc.max_receive_message_length", 10 * 1024 * 1024),
                        ("grpc.enable_retries", 1),
                        ("grpc.keepalive_time_ms", 20000),
                        ("grpc.keepalive_timeout_ms", 5000),
                    ],
                )
                self._channels[peer_id] = channel
                self._stubs[peer_id] = pb2_grpc.NodeRPCStub(channel)
            return self._stubs[peer_id]

    def close_all(self):
        with self._lock:
            for ch in self._channels.values():
                ch.close()
            self._channels.clear()
            self._stubs.clear()


class NodeRPCServicer(pb2_grpc.NodeRPCServicer):
    """gRPC servicer — handles inbound RPCs from peers."""

    def __init__(self, node_id: str, peers: list[str]):
        self.node_id = node_id
        self.peers = peers
        self._app = None  # set via set_app()
        self._forwarded = 0

    def set_app(self, app):
        self._app = app

    # ── Unary RPC ──────────────────────────────────────────────────────────

    def Ping(self, request, context):
        return pb2.Pong(
            node_id=self.node_id,
            term=getattr(self._app, "current_term", lambda: 0)(),
            ok=True,
        )

    def Forward(self, request, context):
        """Forward a command to the local node's SBS engine."""
        if request.command == "__state_query__":
            # State sync query
            result = getattr(self._app, "get_state_query", lambda: "state:{}")()
            return pb2.ForwardResponse(success=True, result=result)

        result = getattr(self._app, "handle_forward", lambda c: f"no-app:{c}")(request.command)
        self._forwarded += 1
        return pb2.ForwardResponse(success=True, result=result)

    # ── Streaming RPC ───────────────────────────────────────────────────────

    def StreamEvents(self, request, context):
        """Server-side stream: push events to subscriber."""
        for i in range(200):
            if context.is_active():
                yield pb2.Event(node_id=self.node_id, seq=i, type="heartbeat")
                time.sleep(3)
            else:
                break


class RPCServer:
    """
    Manages gRPC server lifecycle, peer connections, and broadcasting.

    v6.2:
      • Listens on fixed port from PORT_MAP or NODE_PORT env
      • Uses ConnectionPool for outbound peer calls
      • call_peer() with retry/backoff
      • broadcast() parallel calls to all peers
    """

    def __init__(self, node_id: str, peers: list[str]):
        self.node_id = node_id
        self.peers = peers

        # Determine port
        env_port = os.getenv("NODE_PORT")
        if env_port:
            self.port = int(env_port)
        else:
            self.port = PORT_MAP.get(node_id, DEFAULT_PORT)

        self._server = None
        self._thread: threading.Thread | None = None
        self._servicer = NodeRPCServicer(node_id, peers)
        self._pool = ConnectionPool()
        self._calls = 0
        self._errors = 0

    # ── Server lifecycle ────────────────────────────────────────────────────

    def start(self):
        self._server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=self._pool._max_workers),
        )
        pb2_grpc.add_NodeRPCServicer_to_server(self._servicer, self._server)
        self._server.add_insecure_port(f"[::]:{self.port}")
        self._server.start()
        self._thread = threading.Thread(target=self._serve_loop, daemon=True)
        self._thread.start()
        print(f"[RPC] {self.node_id} listening on :{self.port}")

    def set_app(self, app):
        self._servicer.set_app(app)

    def _serve_loop(self):
        try:
            self._server.wait_for_termination()
        except Exception as e:
            print(f"[RPC] {self.node_id} server error: {e}")

    def stop(self):
        if self._server:
            self._server.stop(grace=5)
        self._pool.close_all()
        print(f"[RPC] {self.node_id} server stopped (calls={self._calls} errors={self._errors})")

    # ── Outbound peer calls ────────────────────────────────────────────────

    def _peer_target(self, peer_id: str) -> str:
        """Resolve peer container hostname + port."""
        peer_port = PORT_MAP.get(peer_id, DEFAULT_PORT)
        return f"atom-{peer_id}:{peer_port}"

    def call_peer(self, peer_id: str, command: str, timeout: float = 3.0) -> str:
        """
        Call a peer's Forward RPC with retry/backoff.
        Returns result string or "error:CODE".
        """
        target = self._peer_target(peer_id)
        stub = self._pool.get_stub(peer_id, target)

        for attempt in range(3):
            try:
                resp = stub.Forward(
                    pb2.ForwardRequest(command=command, origin_node=self.node_id),
                    timeout=timeout,
                )
                self._calls += 1
                return resp.result
            except grpc.RpcError as e:
                self._errors += 1
                if attempt < 2:
                    wait = (2 ** attempt) * 0.1 + random.uniform(0, 0.1)
                    time.sleep(wait)
                else:
                    return f"rpc-error:{e.code().name}"

        return "rpc-error:max-retries"

    def ping_peer(self, peer_id: str, timeout: float = 2.0) -> tuple[bool, float]:
        """
        Ping a peer. Returns (ok, latency_ms).
        """
        target = self._peer_target(peer_id)
        stub = self._pool.get_stub(peer_id, target)
        try:
            start = time.monotonic()
            resp = stub.Ping(pb2.PingRequest(), timeout=timeout)
            lag_ms = (time.monotonic() - start) * 1000
            return (resp.ok, lag_ms)
        except grpc.RpcError:
            return (False, 0.0)

    def broadcast(self, command: str, timeout: float = 3.0) -> dict[str, str]:
        """
        Broadcast command to all peers in parallel.
        Returns {peer_id: result}.
        """
        results: dict[str, str] = {}
        lock = threading.Lock()

        def call(peer):
            r = self.call_peer(peer, command, timeout=timeout)
            with lock:
                results[peer] = r

        threads = [threading.Thread(target=call, args=(p,)) for p in self.peers]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=timeout * len(self.peers) + 1)

        return results

    def broadcast_stream_events(self, peer_id: str):
        """
        Subscribe to peer's event stream (one-shot read of up to 10 events).
        """
        target = self._peer_target(peer_id)
        stub = self._pool.get_stub(peer_id, target)
        try:
            for event in stub.StreamEvents(pb2.EventRequest(), timeout=10.0):
                print(f"[STREAM] {self.node_id} ← {event.node_id} seq={event.seq} type={event.type}")
        except grpc.RpcError as e:
            print(f"[STREAM] {self.node_id} stream error from {peer_id}: {e.code().name}")

"""
ClusterNode — full node with health graph, SBS client, observability.
"""
import os
import sys
import threading
import time

import grpc

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

import proto.atom_os_pb2 as pb2
import proto.atom_os_pb2_grpc as pb2_grpc
from cluster.node.health import ClusterHealthGraph, NodeState
from cluster.shared.drl_bridge import DRLBridge
from cluster.shared.observability import ClusterLogger, MetricsCollector
from cluster.shared.rpc_server import RPCServer
from cluster.shared.sbs_client import SBSDistributedClient
from sbs.boundary_spec import SystemBoundarySpec

# SBS lives at repo-root/sbs/ — import directly
from sbs.global_invariant_engine import GlobalInvariantEngine
from sbs.runtime import SBS_MODE, SBSRuntimeEnforcer


class ClusterNode:
    """
    Full cluster node: RPC + DRL + SBS + Health + Observability.

    Lifecycle:
        start()          → init all layers, start RPC server, begin health loop
        join_handshake() → register with peers, exchange initial state
        execute(cmd)     → run command through SBS enforcer
        stop()           → graceful shutdown
    """

    def __init__(self, node_id: str, peers: list[str]):
        self.node_id = node_id
        self.peers = peers

        # ── Core layers ──────────────────────────────────────────────────
        self.drl = DRLBridge(node_id)
        self.rpc = RPCServer(node_id, peers)
        self.health = ClusterHealthGraph(node_id, peers)
        self.logger = ClusterLogger(node_id)
        self.metrics = MetricsCollector(node_id)

        # ── SBS ──────────────────────────────────────────────────────────
        self.spec = SystemBoundarySpec()
        self.engine = GlobalInvariantEngine(self.spec)
        self.sbs = SBSRuntimeEnforcer(
            boundary_spec=self.spec,
            invariant_engine=self.engine,
            mode=SBS_MODE.ENFORCED,
        )
        self.sbs_client = SBSDistributedClient(node_id, peers)

        # ── State ────────────────────────────────────────────────────────
        self.current_term = 0
        self.commit_index = 0
        self.is_leader = False
        self._running = False
        self._health_thread: threading.Thread | None = None
        self._sbs_thread: threading.Thread | None = None
        self._forwarded_count = 0

        # Init metrics for all peers
        for p in peers:
            self.metrics.init_peer(p)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def start(self):
        """Start all layers and background threads."""
        self.logger.info("node_start", peers=self.peers)
        print(f"[NODE] {self.node_id} starting...")

        # Boot layers
        self._init_layers()

        # Start RPC server
        self.rpc.set_app(self)
        self.rpc.start()

        # Boot handshake
        self._join_handshake()

        # Background threads
        self._running = True
        self._health_thread = threading.Thread(target=self._health_loop, daemon=True)
        self._health_thread.start()

        self._sbs_thread = threading.Thread(target=self._sbs_loop, daemon=True)
        self._sbs_thread.start()

        self.logger.info("node_ready")
        print(f"[NODE] {self.node_id} READY — peers={self.peers}")

    def _init_layers(self):
        self.logger.debug("init_layers")

    def _join_handshake(self):
        """
        On boot, each node:
          1. Waits briefly for peers to also boot
          2. Pings all peers to populate health graph
          3. Syncs initial term + state
        """
        time.sleep(1.5)  # let peers start

        self.logger.info("handshake_start")
        for peer in self.peers:
            pong_ok, lag_ms = self._ping_peer(peer)
            if pong_ok:
                self.health.mark_ok(peer, lag_ms)
                self.metrics.record_pong(peer, lag_ms)
                self.logger.info("peer_reachable", peer=peer, lag_ms=lag_ms)
            else:
                self.health.mark_fail(peer)
                self.logger.warn("peer_unreachable", peer=peer)

        reachable = sum(
            1 for p in self.peers
            if self.health.get(p) and self.health.get(p).state == NodeState.REACHABLE
        )
        self.logger.info("handshake_done", reachable_peers=reachable)
        print(f"[NODE] {self.node_id} handshake: {reachable}/{len(self.peers)} reachable")

    def stop(self):
        self.logger.info("node_stop")
        self._running = False
        if self._health_thread:
            self._health_thread.join(timeout=2)
        if self._sbs_thread:
            self._sbs_thread.join(timeout=2)
        self.rpc.stop()
        print(f"[NODE] {self.node_id} stopped")

    # ── Health ─────────────────────────────────────────────────────────────

    def _health_loop(self):
        """Background: ping peers every 5s, update health graph."""
        while self._running:
            time.sleep(5)
            for peer in self.peers:
                pong_ok, lag_ms = self._ping_peer(peer)
                if pong_ok:
                    self.health.mark_ok(peer, lag_ms)
                    self.metrics.record_pong(peer, lag_ms)
                else:
                    self.health.mark_fail(peer)
                    self.logger.warn("peer_ping_fail", peer=peer)

    def _ping_peer(self, peer: str) -> tuple[bool, float]:
        """Send a Ping to peer, return (ok, lag_ms)."""
        peer_port = 50000 + sum(ord(c) for c in peer) % 1000
        target = f"atom-{peer}:{peer_port}"
        channel = grpc.insecure_channel(target, options=[
            ("grpc.lb_policy_name", "pick_first"),
            ("grpc.enable_retries", 0),
        ])
        stub = pb2_grpc.NodeRPCStub(channel)
        try:
            start = time.monotonic()
            resp = stub.Ping(pb2.PingRequest(), timeout=3.0)
            lag_ms = (time.monotonic() - start) * 1000
            return (resp.ok, lag_ms)
        except grpc.RpcError:
            return (False, 0.0)
        finally:
            channel.close()

    # ── SBS ───────────────────────────────────────────────────────────────

    def _sbs_loop(self):
        """Background: periodic cross-node SBS evaluation every 10s."""
        while self._running:
            time.sleep(10)
            self._run_sbs_check()

    def _run_sbs_check(self):
        """Collect peer states + evaluate SBS invariants."""
        peer_states = {}

        for peer in self.peers:
            peer_state = self._collect_peer_state(peer)
            if peer_state:
                peer_states[peer] = peer_state

        if not peer_states:
            self.logger.debug("sbs_check_skip_no_peers")
            return

        # Run quorum evaluation
        ok = self.sbs_client.evaluate_quorum(peer_states)

        # Update local layers with our own state
        local_state = {
            "drl": {"term": self.current_term, "leader": self.node_id if self.is_leader else None},
            "ccl": {"term": self.current_term},
            "f2": {"commit_index": self.commit_index, "quorum_ratio": 0.71},
            "desc": {"commit_index": self.commit_index, "term": self.current_term},
        }
        self.sbs_client.update_local_layer("drl", local_state["drl"])
        self.sbs_client.update_local_layer("ccl", local_state["ccl"])
        self.sbs_client.update_local_layer("f2", local_state["f2"])
        self.sbs_client.update_local_layer("desc", local_state["desc"])

        if not ok:
            violations = self.sbs_client.get_violations()
            for v in violations:
                self.logger.error("sbs_violation", violation=v)
                for peer in peer_states:
                    self.health.mark_violation(peer, weight=0.5)
                    self.metrics.record_violation(peer)
        else:
            self.logger.debug("sbs_check_ok", peers=len(peer_states))

    def _collect_peer_state(self, peer: str) -> dict | None:
        """Ask peer for its current layer state via Forward RPC."""
        peer_port = 50000 + sum(ord(c) for c in peer) % 1000
        target = f"atom-{peer}:{peer_port}"
        try:
            channel = grpc.insecure_channel(target, options=[("grpc.enable_retries", 0)])
            stub = pb2_grpc.NodeRPCStub(channel)
            resp = stub.Forward(pb2.ForwardRequest(
                command="__state_query__",
                origin_node=self.node_id,
            ), timeout=2.0)
            channel.close()
            if resp.success and resp.result.startswith("state:"):
                import json
                state_str = resp.result[6:]
                return json.loads(state_str)
        except Exception:
            pass
        return None

    # ── Command execution ─────────────────────────────────────────────────

    # NOTE: execute() REMOVED in v9.0
    # All mutations MUST route through ExecutionGateway only.
    # RPC handlers use _gateway_forward() below.

    def _gateway_forward(self, command: str) -> str:
        """
        Thin proxy: forwards command to ExecutionGateway.
        Node layer produces NO state mutations — only routing.
        """
        try:
            from orchestration.ExecutionGateway.execution_gateway import ExecutionGateway
            gw = ExecutionGateway()
            result = gw.execute(command)
            if not result.final_passed:
                return f"BLOCKED by {result.block_gate}: {result.block_reason}"
            return f"ok({self.node_id}): {command}"
        except Exception as e:
            return f"gateway_error({self.node_id}): {e}"

    def _build_state(self) -> dict:
        return {
            "drl": {"term": self.current_term, "leader": self.node_id if self.is_leader else None},
            "ccl": {"term": self.current_term, "leader": self.node_id if self.is_leader else None},
            "f2": {"commit_index": self.commit_index, "quorum_ratio": 0.71},
            "desc": {"commit_index": self.commit_index, "term": self.current_term},
        }

    # ── App interface (called by RPC server) ───────────────────────────────

    def current_term(self) -> int:
        return self.current_term

    def handle_forward(self, command: str) -> str:
        """Handle inbound Forward RPC."""
        self._forwarded_count += 1
        return self._gateway_forward(command)

    def get_state_query(self) -> str:
        """Return serialized state for peer state sync."""
        import json
        state = {
            "drl": {"term": self.current_term, "leader": self.node_id if self.is_leader else None},
            "ccl": {"term": self.current_term},
            "f2": {"commit_index": self.commit_index},
            "desc": {"commit_index": self.commit_index, "term": self.current_term},
        }
        return f"state:{json.dumps(state)}"

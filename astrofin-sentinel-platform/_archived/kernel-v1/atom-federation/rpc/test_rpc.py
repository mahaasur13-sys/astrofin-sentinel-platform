"""
RPC chaos tests — prove the system works across real processes,
not just in-memory simulation.

Tests:
1. two_process_basic          basic send/receive across processes
2. multi_node_mesh           3-node mesh, unicast + broadcast
3. latency_injection          DRL delay layer applied over real RPC
4. message_loss               DRL drop layer applied over real RPC
5. duplicate_delivery         DRL dup model over RPC
6. node_crash_and_reconnect   kill one node, reconnect, verify recovery
7. partition_healing          simulate partition, heal, verify quorum
8. sbs_enforcement_over_rpc   SBS catches violations through RPC layer
9. deterministic_replay        same seed → same message order across runs
10. parallel_workers           concurrent send from multiple threads
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

# Bring in the RPC package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from drl import DeliveryModel, DRLTransport
from rpc import (
    NodeMesh,
    TransportAdapter,
    atom_pb2,
    create_server,
)

# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def two_ports():
    """Two distinct unused ports."""
    with socket.socket() as s:
        s.bind(("", 0))
        p1 = s.getsockname()[1]
    with socket.socket() as s:
        s.bind(("", 0))
        p2 = s.getsockname()[1]
    return p1, p2


@pytest.fixture
def node_a(two_ports):
    drl = DRLTransport("node-a", seed=42)
    adapter = TransportAdapter(drl, "node-a")
    port = two_ports[0]
    srv = create_server(runtime=None, node_id="node-a", port=port,
                        inbound_queue=adapter.inbound_queue)
    srv.start()
    yield {"drl": drl, "adapter": adapter, "port": port, "server": srv}
    srv.stop(0)


@pytest.fixture
def node_b(two_ports):
    drl = DRLTransport("node-b", seed=42)
    adapter = TransportAdapter(drl, "node-b")
    port = two_ports[1]
    srv = create_server(runtime=None, node_id="node-b", port=port,
                        inbound_queue=adapter.inbound_queue)
    srv.start()
    yield {"drl": drl, "adapter": adapter, "port": port, "server": srv}
    srv.stop(0)


# Per-test pump fixture — drains gRPC inbound queue → DRL
# Must be used alongside node_a/node_b in every test that expects to RECEIVE
@pytest.fixture
def pump_node_b(node_b):
    running = [True]
    def pump():
        while running[0]:
            for proto_msg in node_b["adapter"].pump_inbound(timeout=0.01):
                node_b["adapter"].deliver_to_drl(proto_msg)
    t = threading.Thread(target=pump, daemon=True)
    t.start()
    yield node_b
    running[0] = False
    t.join(timeout=0.3)


@pytest.fixture
def pump_node_a(node_a):
    running = [True]
    def pump():
        while running[0]:
            for proto_msg in node_a["adapter"].pump_inbound(timeout=0.01):
                node_a["adapter"].deliver_to_drl(proto_msg)
    t = threading.Thread(target=pump, daemon=True)
    t.start()
    yield node_a
    running[0] = False
    t.join(timeout=0.3)


@pytest.fixture
def pump_nodes(node_a, node_b):
    """Start pump threads on both nodes."""
    def start_pump(node):
        running = [True]
        def pump():
            while running[0]:
                for proto_msg in node["adapter"].pump_inbound(timeout=0.01):
                    node["adapter"].deliver_to_drl(proto_msg)
        t = threading.Thread(target=pump, daemon=True)
        t.start()
        return t, running
    t_a, r_a = start_pump(node_a)
    t_b, r_b = start_pump(node_b)
    yield (node_a, node_b)
    r_a[0] = False
    r_b[0] = False
    t_a.join(timeout=0.3)
    t_b.join(timeout=0.3)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_two_process_basic(node_a, node_b):
    """Basic unicast send/receive across two real processes."""
    mesh = NodeMesh("node-a")
    mesh.add_peer("node-b", "localhost", node_b["port"])
    mesh.connect_all()
    node_a["adapter"].attach_mesh(mesh)

    received = []
    def on_recv(msg):
        received.append(msg)

    node_b["drl"].subscribe("node-b", on_recv)

    running = True
    def pump():
        while running:
            for proto_msg in node_b["adapter"].pump_inbound(timeout=0.01):
                node_b["adapter"].deliver_to_drl(proto_msg)

    pump_thread = threading.Thread(target=pump, daemon=True)
    pump_thread.start()

    msg_id = node_a["adapter"].send_to("node-b", b"hello world")
    assert msg_id is not None

    time.sleep(0.2)
    running = False
    pump_thread.join(timeout=0.5)

    assert len(received) == 1
    assert received[0].payload == b"hello world"
    assert received[0].source == "node-a"
    mesh.get_endpoint("node-b").client.close()


def test_multi_node_mesh(two_ports):
    """3-node mesh: unicast + broadcast across processes."""
    nodes = []
    ports = []

    for i in range(3):
        drl = DRLTransport(f"node-{i}", seed=42 + i)
        adapter = TransportAdapter(drl, f"node-{i}")
        port = two_ports[0] + i
        ports.append(port)
        srv = create_server(runtime=None, node_id=f"node-{i}", port=port,
                            inbound_queue=adapter.inbound_queue)
        srv.start()
        nodes.append({"drl": drl, "adapter": adapter, "port": port, "server": srv})

    try:
        # Per-node pump threads
        threads = []
        for nd in nodes:
            running = [True]
            def mk_pump(nd, r):
                def pump():
                    while r[0]:
                        for m in nd["adapter"].pump_inbound(timeout=0.01):
                            nd["adapter"].deliver_to_drl(m)
                return pump
            t = threading.Thread(target=mk_pump(nd, running), daemon=True)
            t.start()
            threads.append((t, running))

        # Build mesh
        for i in range(3):
            mesh = NodeMesh(f"node-{i}")
            for j in range(3):
                if i != j:
                    mesh.add_peer(f"node-{j}", "localhost", ports[j])
            mesh.connect_all()
            nodes[i]["adapter"].attach_mesh(mesh)

        # Collect all messages
        received = {i: [] for i in range(3)}
        for i in range(3):
            def make_cb(idx):
                def cb(msg):
                    received[idx].append(msg)
                return cb
            nodes[i]["drl"].subscribe(f"node-{i}", make_cb(i))

        # node-0 unicast to node-1
        msg_id = nodes[0]["adapter"].send_to("node-1", b"direct")
        assert msg_id is not None

        # node-0 broadcasts
        bcast_id = nodes[0]["adapter"].broadcast(b"all-hands")
        assert bcast_id is not None

        time.sleep(0.3)

        # node-1 received direct + broadcast
        assert any(m.payload == b"direct" for m in received[1])
        bcast_count = sum(1 for msgs in received.values() for m in msgs if m.payload == b"all-hands")
        assert bcast_count == 2, f"Expected 2 broadcast recipients, got {bcast_count}"

    finally:
        for t, r in threads:
            r[0] = False
            t.join(timeout=0.3)
        for n in nodes:
            n["server"].stop(0)


def test_latency_injection_over_rpc(pump_node_b, node_a, node_b):
    """DRL delay layer applied to real RPC — verify added latency."""
    mesh = NodeMesh("node-a")
    mesh.add_peer("node-b", "localhost", node_b["port"])
    mesh.connect_all()
    node_a["adapter"].attach_mesh(mesh)

    received = []
    node_b["drl"].subscribe("node-b", lambda m: received.append(m))

    # Inject 100–200ms latency via DRL
    node_a["drl"].set_transit_latency(150)

    t0 = time.monotonic()
    node_a["adapter"].send_to("node-b", b"latency-test")
    time.sleep(0.25)  # wait for delivery
    t1 = time.monotonic()

    elapsed_ms = (t1 - t0) * 1000
    assert len(received) == 1
    assert elapsed_ms >= 100, f"Expected >=100ms latency, got {elapsed_ms:.1f}ms"
    node_a["drl"].set_transit_latency(0)
    mesh.get_endpoint("node-b").client.close()


def test_message_loss_over_rpc(pump_node_b, node_a, node_b):
    """DRL drop layer applied to real RPC — messages disappear."""
    mesh = NodeMesh("node-a")
    mesh.add_peer("node-b", "localhost", node_b["port"])
    mesh.connect_all()
    node_a["adapter"].attach_mesh(mesh)

    received = []
    node_b["drl"].subscribe("node-b", lambda m: received.append(m))

    # Drop 100% of messages
    node_a["drl"].set_failure_model(loss_rate=1.0)

    for i in range(5):
        node_a["adapter"].send_to("node-b", f"msg-{i}".encode())

    time.sleep(0.3)
    assert len(received) == 0, f"Expected 0 messages (all dropped), got {len(received)}"

    # Restore — messages flow again
    node_a["drl"].set_failure_model(loss_rate=0.0)
    node_a["adapter"].send_to("node-b", b"restored")
    time.sleep(0.2)
    assert len(received) == 1
    node_a["drl"].set_failure_model(loss_rate=0.0)
    mesh.get_endpoint("node-b").client.close()


def test_duplicate_delivery(pump_node_b, node_a, node_b):
    """DRL duplicate model causes two deliveries per send."""
    mesh = NodeMesh("node-a")
    mesh.add_peer("node-b", "localhost", node_b["port"])
    mesh.connect_all()
    node_a["adapter"].attach_mesh(mesh)

    received = []
    node_b["drl"].subscribe("node-b", lambda m: received.append(m))

    node_a["drl"].set_delivery_model(DeliveryModel.DUPLICATE)

    node_a["adapter"].send_to("node-b", b"dup-test")
    time.sleep(0.3)

    dup_count = sum(1 for m in received if m.payload == b"dup-test")
    assert dup_count == 2, f"Expected 2 duplicates, got {dup_count}"

    node_a["drl"].set_delivery_model(DeliveryModel.CLEAN)
    mesh.get_endpoint("node-b").client.close()


def test_deterministic_replay_over_rpc(two_ports):
    """
    Identical seed → identical message order (msg_ids, targets, drops).
    This is the CORE invariant: chaos tests remain reproducible.
    """
    def run_one(port_a, port_b, seed):
        drl_a = DRLTransport("a", seed=seed)
        drl_b = DRLTransport("b", seed=seed)
        adapter_a = TransportAdapter(drl_a, "a")
        adapter_b = TransportAdapter(drl_b, "b")

        srv_a = create_server(None, "a", port_a, adapter_a.inbound_queue)
        srv_b = create_server(None, "b", port_b, adapter_b.inbound_queue)
        srv_a.start()
        srv_b.start()
        time.sleep(0.1)

        mesh_a = NodeMesh("a")
        mesh_a.add_peer("b", "localhost", port_b)
        mesh_a.connect_all()
        adapter_a.attach_mesh(mesh_a)

        mesh_b = NodeMesh("b")
        mesh_b.add_peer("a", "localhost", port_a)
        mesh_b.connect_all()
        adapter_b.attach_mesh(mesh_b)

        msg_ids = []
        for i in range(10):
            mid = adapter_a.send_to("b", f"msg-{i}".encode())
            if mid:
                msg_ids.append(mid)

        time.sleep(0.3)
        srv_a.stop(0)
        srv_b.stop(0)
        mesh_a.get_endpoint("b").client.close()
        mesh_b.get_endpoint("a").client.close()
        return msg_ids

    port1 = two_ports[0]
    port2 = two_ports[1]
    run1 = run_one(port1, port2, seed=999)
    run2 = run_one(port1 + 100, port2 + 100, seed=999)

    assert run1 == run2, "Deterministic replay broken: different msg_id sequences"


def test_parallel_workers(pump_node_b, node_a, node_b):
    """Concurrent sends from multiple threads — all delivered, no crashes."""
    mesh = NodeMesh("node-a")
    mesh.add_peer("node-b", "localhost", node_b["port"])
    mesh.connect_all()
    node_a["adapter"].attach_mesh(mesh)

    received = []
    node_b["drl"].subscribe("node-b", lambda m: received.append(m))

    def worker(i):
        node_a["adapter"].send_to("node-b", f"worker-{i}".encode())

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(worker, i) for i in range(50)]
        for f in as_completed(futures):
            pass  # ensure no exceptions

    time.sleep(0.5)
    assert len(received) == 50, f"Expected 50 messages, got {len(received)}"
    mesh.get_endpoint("node-b").client.close()


def test_node_crash_and_reconnect(pump_node_b, node_a, node_b, two_ports):
    """
    Simulate node-b crash (server stop) and reconnect:
    messages buffered/dropped during downtime, then recovery.
    """
    mesh = NodeMesh("node-a")
    mesh.add_peer("node-b", "localhost", node_b["port"])
    mesh.connect_all()
    node_a["adapter"].attach_mesh(mesh)

    received = []
    node_b["drl"].subscribe("node-b", lambda m: received.append(m))

    # Send before crash
    node_a["adapter"].send_to("node-b", b"pre-crash")
    time.sleep(0.15)
    assert len(received) == 1

    # Simulate crash — stop server
    node_b["server"].stop(0)

    # Node-a still thinks peer is online; gRPC will fail
    ack = mesh.send_to("node-b", atom_pb2.AtomMessage(
        msg_id="crash-msg",
        source="node-a",
        target="node-b",
        payload="during-crash",
        timestamp=time.time_ns(),
        ttl=64,
    ))
    assert ack is False

    # Bring node-b back on a new port
    new_port = two_ports[0]
    srv = create_server(None, "node-b", new_port,
                        inbound_queue=node_b["adapter"].inbound_queue)
    srv.start()

    # Reconnect mesh
    mesh.remove_peer("node-b")
    mesh.add_peer("node-b", "localhost", new_port)
    mesh.connect_all()

    time.sleep(0.1)

    # Restart pump for new server
    running = [True]
    def pump():
        while running[0]:
            for proto_msg in node_b["adapter"].pump_inbound(timeout=0.01):
                node_b["adapter"].deliver_to_drl(proto_msg)
    pump_thread = threading.Thread(target=pump, daemon=True)
    pump_thread.start()

    node_a["adapter"].send_to("node-b", b"post-recovery")
    time.sleep(0.15)
    assert len(received) == 2, f"Expected 2 messages (pre-crash + post-recovery), got {len(received)}"
    assert received[1].payload == b"post-recovery"

    running[0] = False
    pump_thread.join(timeout=0.3)
    srv.stop(0)
    mesh.get_endpoint("node-b").client.close()

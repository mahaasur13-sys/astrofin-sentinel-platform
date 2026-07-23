"""
TransportAdapter — BRIDGE between DRL (fault layer) and real gRPC network.

CRITICAL PRINCIPLE: DRL is NOT replaced.
DRL stays as the fault injection layer ON TOP of real RPC.
Chaos tests continue to work because they drive DRL, not raw gRPC.

Layout (per node):
    CCL/submit()
        → DRL.process_outgoing()  ← fault injection HERE
            → TransportAdapter.send()
                → RPCClient.send()
                    → wire (real network)
                        → remote AtomServicer.receive()
                            → remote inbound_queue
                                → remote DRL.receive()  ← fault detection
                                    → SBS enforcement
"""

from __future__ import annotations

import queue
import time
from typing import Any

from drl import DeliveryModel

from .mesh import NodeMesh
from .proto import atom_pb2


class TransportAdapter:
    """
    Bridges local DRL fault layer to remote nodes via gRPC.

    DRL remains the authority on:
      - message ID generation (deterministic UUIDs)
      - fault injection (drop/delay/dup/reorder/partition/corrupt)
      - ordering semantics
      - replay log

    This adapter translates DRL's decisions to real network I/O.
    """

    def __init__(
        self,
        drl: Any,            # DRLTransport instance (fault authority)
        node_id: str,
        inbound_queue: queue.Queue | None = None,
    ) -> None:
        self.drl = drl
        self.node_id = node_id
        self._inbound = inbound_queue or queue.Queue()
        self._mesh: NodeMesh | None = None
        self._processing = False
        self._dispatcher: dict[str, callable] = {}

    def attach_mesh(self, mesh: NodeMesh) -> None:
        self._mesh = mesh

    @property
    def inbound_queue(self) -> queue.Queue:
        """Remote messages land here after gRPC receive."""
        return self._inbound

    # ── Outgoing ──────────────────────────────────────────────────────────────

    def send_to(self, target: str, payload: bytes | str, msg_id: str | None = None) -> str | None:
        """
        High-level send: DRL generates msg_id and applies faults,
        then adapter sends the result over real RPC.
        """
        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        # ── DRL fault injection layer ──────────────────────────────────────────
        # This is where drop/delay/dup/reorder/corrupt happen.
        # DRL returns None if it swallowed the message (dropped).
        drl_result = self.drl.send_to(target, payload, msg_id=msg_id)
        if drl_result is None:
            # DRL chose to drop — do NOT send anything
            return None

        # DRL assigned the msg_id (may differ from requested if None was passed)
        actual_msg_id = drl_result

        # ── Real network send ─────────────────────────────────────────────────
        if self._mesh is None:
            return actual_msg_id

        msg = atom_pb2.AtomMessage(
            msg_id=actual_msg_id,
            source=self.node_id,
            target=target,
            payload=payload.decode("utf-8", errors="replace"),
            timestamp=time.time_ns(),
            ttl=64,
        )

        # DUPLICATE model: DRL already queued 2 copies locally;
        # we must send 2 copies over the wire too.
        count = 2 if self.drl._delivery_model == DeliveryModel.DUPLICATE else 1
        ok = True
        for _ in range(count):
            if not self._mesh.send_to(target, msg):
                ok = False
                break
        return actual_msg_id if ok else None

    def broadcast(self, payload: bytes | str, msg_id: str | None = None) -> str | None:
        """Broadcast via DRL → RPC mesh."""
        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        actual_msg_id = self.drl.broadcast(payload, msg_id=msg_id)
        if actual_msg_id is None:
            return None

        if self._mesh is None:
            return actual_msg_id

        msg = atom_pb2.AtomMessage(
            msg_id=actual_msg_id,
            source=self.node_id,
            target="",
            payload=payload.decode("utf-8", errors="replace"),
            timestamp=time.time_ns(),
            ttl=64,
        )

        self._mesh.broadcast(msg)
        return actual_msg_id

    # ── Incoming ──────────────────────────────────────────────────────────────

    def pump_inbound(self, timeout: float = 0.01) -> list[Any]:
        """
        Drain messages from the gRPC inbound queue.
        Called by the local node's event loop.
        """
        messages = []
        while True:
            try:
                proto_msg = self._inbound.get(timeout=timeout)
                messages.append(proto_msg)
            except queue.Empty:
                break
        return messages

    def deliver_to_drl(self, proto_msg: atom_pb2.AtomMessage) -> None:
        """
        Called by the local gRPC server's AtomServicer when a message arrives.
        Translates protobuf → DRL Message and delivers to local DRL receive().
        """
        # Import Message from the drl package
        import drl
        msg = drl.Message.from_proto(proto_msg)
        self.drl.receive(msg)

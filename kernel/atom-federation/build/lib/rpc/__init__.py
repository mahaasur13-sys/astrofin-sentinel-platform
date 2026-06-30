"""
RPC package — real network transport for ATOMFederationOS.

Modules
-------
proto        generated protobuf modules (atom_pb2, atom_pb2_grpc)
server       AtomServicer + gRPC server factory
client       RPCClient (connection to one peer)
mesh         NodeMesh (full connection graph)
adapter      TransportAdapter (DRL ↔ gRPC bridge)

Usage
-----
    # Node 0 (server side)
    from drl import DRLTransport
    from rpc.server import serve_forever
    from rpc.adapter import TransportAdapter

    drl = DRLTransport("node-0", seed=42)
    adapter = TransportAdapter(drl, "node-0")
    serve_forever(runtime=None, node_id="node-0", port=50051,
                  inbound_queue=adapter.inbound_queue)

    # Node 1 (client side)
    from rpc.client import RPCClient
    from rpc.mesh import NodeMesh

    mesh = NodeMesh("node-1")
    mesh.add_peer("node-0", "localhost", 50051)
    mesh.connect_all()
"""

from .adapter import TransportAdapter
from .client import RPCClient
from .mesh import NodeEndpoint, NodeMesh
from .proto import atom_pb2, atom_pb2_grpc
from .server import AtomServicer, create_server, serve_forever

__all__ = [
    "AtomServicer",
    "NodeEndpoint",
    "NodeMesh",
    "RPCClient",
    "TransportAdapter",
    "atom_pb2",
    "atom_pb2_grpc",
    "create_server",
    "serve_forever",
]

"""
Node entrypoint — runs inside container.

Usage (inside container):
    python entrypoint.py
Environment:
    NODE_ID=e.g. "node-a"
    PEERS=comma-separated peer IDs
"""
import os
import signal
import sys
import time

sys.path.insert(0, "/app")

from cluster.shared.runtime_bootstrap import BootstrapNode

NODE_ID = os.getenv("NODE_ID", "unknown")
PEERS = [p.strip() for p in os.getenv("PEERS", "").split(",") if p.strip()]

print(f"[ENTRY] {NODE_ID} booting — NODE_ID={NODE_ID}, PEERS={PEERS}")

node = BootstrapNode(node_id=NODE_ID, peers=PEERS)


def shutdown(signum, frame):
    print(f"\n[SHUTDOWN] {NODE_ID} stopping gracefully...")
    node.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

node.start()

print(f"[READY] {NODE_ID} — health loop running, press Ctrl+C to stop")

while True:
    time.sleep(1)

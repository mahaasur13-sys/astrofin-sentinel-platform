#!/usr/bin/env python3
"""
WireGuard Prometheus Exporter
Exports: peer status, bytes transferred, latest handshake
Endpoint: /metrics  (text format for Prometheus)
"""
import logging
import re
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

log = logging.getLogger(__name__)


WG_INTERFACE = "wg0"

def parse_wg_show() -> dict:
    """Parse `wg show wg0` output."""
    try:
        out = subprocess.check_output(["wg", "show", WG_INTERFACE], text=True, timeout=3)
    except Exception:
        return {"peers": [], "interface": {}}

    peers = []
    current_peer = None
    for line in out.strip().split("\n"):
        line = line.strip()
        if line.startswith("peer:"):
            if current_peer:
                peers.append(current_peer)
            current_peer = {"public_key": line.split(":", 1)[1].strip()}
        elif line.startswith("endpoint:"):
            if current_peer:
                current_peer["endpoint"] = line.split(":", 1)[1].strip()
        elif line.startswith("allowed ips:"):
            if current_peer:
                current_peer["allowed_ips"] = line.split(":", 1)[1].strip()
        elif line.startswith("latest handshake:"):
            if current_peer:
                current_peer["handshake"] = line.split(":", 1)[1].strip()
        elif line.startswith("transfer:"):
            if current_peer:
                parts = line.split(":", 1)[1].strip().split(",")
                for p in parts:
                    k, v = p.strip().split("=")
                    current_peer[f"tx_{k.strip()}"] = v.strip().split()[0]
                    current_peer[f"rx_{k.strip()}"] = v.strip().split()[0]
        elif "interface:" in line:
            if current_peer:
                peers.append(current_peer)
                current_peer = None

    if current_peer:
        peers.append(current_peer)

    return {"peers": peers}

def build_metrics() -> str:
    wg = parse_wg_show()
    lines = [
        "# HELP wg_peer_count Number of connected peers",
        "# TYPE wg_peer_count gauge",
        f"wg_peer_count {len(wg['peers'])}",
        "# HELP wg_peer_handshake_seconds Time since last handshake",
        "# TYPE wg_peer_handshake_seconds gauge",
    ]

    for peer in wg.get("peers", []):
        allowed = peer.get("allowed_ips", "unknown").replace("/", "_").replace(".", "_")
        # Parse handshake age
        handshake = peer.get("handshake", "0 seconds ago")
        age_seconds = 0
        if "second" in handshake:
            m = re.search(r'(\d+)\s*second', handshake)
            age_seconds = int(m.group(1)) if m else 0
        elif "minute" in handshake:
            m = re.search(r'(\d+)\s*minute', handshake)
            age_seconds = int(m.group(1)) * 60 if m else 0
        elif "hour" in handshake:
            m = re.search(r'(\d+)\s*hour', handshake)
            age_seconds = int(m.group(1)) * 3600 if m else 0

        rx_bytes = peer.get("rx_KiB", 0)
        tx_bytes = peer.get("tx_KiB", 0)

        labels = f'peer="{allowed}"'
        lines.append(f'wg_peer_handshake_seconds{{{labels}}} {age_seconds}')
        lines.append(f'wg_peer_rx_bytes{{{labels}}} {rx_bytes}')
        lines.append(f'wg_peer_tx_bytes{{{labels}}} {tx_bytes}')

    return "\n".join(lines) + "\n"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(build_metrics().encode())
        else:
            self.send_response(404)
        return
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9343), Handler)
    log.info("WireGuard exporter listening on :9343/metrics")
    server.serve_forever()

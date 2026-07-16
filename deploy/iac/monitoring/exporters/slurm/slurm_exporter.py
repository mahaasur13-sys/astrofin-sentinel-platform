import os

#!/usr/bin/env python3
"""
Slurm Prometheus Exporter
Exports: queue depth, node state, GPU allocation, job states
Endpoint: /metrics  (text format for Prometheus)
"""

import re
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

SLURMCTL_HOST = "10.20.20.10"
SLURMCTL_PORT = 6817

METRICS = {}


def get_slurm_queue() -> dict:
    """Parse squeue output."""
    try:
        out = subprocess.check_output(
            ["squeue", "--format=%i|%j|%T|%P|%u|%g|%M|%L|%N", "-a"],
            text=True,
            timeout=5,
        )
    except Exception:
        return {"total_jobs": 0, "running": 0, "pending": 0, "nodes": {}}

    lines = out.strip().split("\n")
    metrics = {"total_jobs": 0, "running": 0, "pending": 0, "nodes": {}}
    re.compile(r"^(.+?)\s+(.+?)\s+(COMPLETING|RUNNING|PENDING|FAILED|CANCELLED)\s+(.*)$")

    for line in lines[1:]:
        parts = line.split("|")
        if len(parts) < 3:
            continue
        _job_id, _name, state = parts[0], parts[1], parts[2]
        metrics["total_jobs"] += 1
        if state == "RUNNING":
            metrics["running"] += 1
        elif state == "PENDING":
            metrics["pending"] += 1

    return metrics


def get_slurm_nodes() -> dict:
    """Parse sinfo output."""
    try:
        out = subprocess.check_output(["sinfo", "-N", "--format=%N|%A|%a|%c|%m|%e|%G|%T"], text=True, timeout=5)
    except Exception:
        return {}

    nodes = {}
    for line in out.strip().split("\n")[1:]:
        parts = line.split("|")
        if len(parts) < 7:
            continue
        hostname, avail, up, cpus, _mem, _free_mem, gpus, state = (
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            parts[4],
            parts[5],
            parts[6],
            parts[7],
        )
        nodes[hostname] = {
            "state": state.strip(),
            "cpus": int(cpus),
            "gpus": int(gpus) if gpus != "0" else 0,
            "available": "up" in up.lower() or "alloc" in avail.lower(),
        }
    return nodes


def build_metrics() -> str:
    """Build Prometheus text metrics."""
    queue = get_slurm_queue()
    nodes = get_slurm_nodes()

    lines = [
        "# HELP slurm_queue_total Total jobs in Slurm queue",
        "# TYPE slurm_queue_total gauge",
        f"slurm_queue_total {queue['total_jobs']}",
        f"slurm_queue_running {queue['running']}",
        f"slurm_queue_pending {queue['pending']}",
        "# HELP slurm_node_available Node availability",
        "# TYPE slurm_node_available gauge",
    ]

    for name, info in nodes.items():
        labels = f'node="{name}"'
        lines.append(f"slurm_node_available{{{labels}}} {1 if info['available'] else 0}")
        lines.append(f"slurm_node_gpus{{{labels}}} {info['gpus']}")
        lines.append(
            f"slurm_node_state{{{labels}}} 1" if info["state"] == "alloc" else f"slurm_node_state{{{labels}}} 0"
        )

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
        pass  # silence request logs


if __name__ == "__main__":
    server = HTTPServer((os.environ.get("BIND_HOST", "127.0.0.1"), 9341), Handler)
    print("Slurm exporter listening on :9341/metrics")
    server.serve_forever()

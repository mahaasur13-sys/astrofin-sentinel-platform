#!/usr/bin/env python3
"""
Ceph Prometheus Exporter
Exports: OSD up/down, PG states, storage utilization, MON quorum
Endpoint: /metrics  (text format for Prometheus)
"""

import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

CEPH_CMD = ["ceph", "-f", "json"]
METRICS = {}


def get_ceph_status() -> dict:
    """ceph status --format json"""
    try:
        out = subprocess.check_output(CEPH_CMD + ["status"], text=True, timeout=5)
        return json.loads(out)
    except Exception:  # noqa: BLE001
        return {}


def get_ceph_osd_dump() -> list:
    """ceph osd dump --format json"""
    try:
        out = subprocess.check_output(CEPH_CMD + ["osd", "dump"], text=True, timeout=5)
        data = json.loads(out)
        return data.get("osds", [])
    except Exception:  # noqa: BLE001
        return []


def get_ceph_pg_dump() -> dict:
    """ceph pg dump --format json"""
    try:
        out = subprocess.check_output(CEPH_CMD + ["pg", "dump", "--format=json"], text=True, timeout=5)
        return json.loads(out)
    except Exception:  # noqa: BLE001
        return {}


def get_ceph_df() -> dict:
    """ceph df --format json"""
    try:
        out = subprocess.check_output(CEPH_CMD + ["df", "json"], text=True, timeout=5)
        return json.loads(out)
    except Exception:  # noqa: BLE001
        return {}


def build_metrics() -> str:
    status = get_ceph_status()
    osds = get_ceph_osd_dump()
    pgs = get_ceph_pg_dump()
    df = get_ceph_df()

    health = status.get("health", {})
    mon_quorum = status.get("monmap", {}).get("quorum", [])

    lines = [
        "# HELP ceph_cluster_health Cluster health status",
        "# TYPE ceph_cluster_health gauge",
        f'ceph_cluster_health{{status="{health.get("status", "UNKNOWN")}"}} 1',
        "# HELP ceph_mon_quorum_size MON quorum count",
        "# TYPE ceph_mon_quorum_size gauge",
        f"ceph_mon_quorum_size {len(mon_quorum)}",
        "# HELP ceph_osd_up OSD up status",
        "# TYPE ceph_osd_up gauge",
    ]

    # OSD metrics
    osd_up = 0
    osd_down = 0
    for osd in osds:
        up = osd.get("up", 0)
        if up:
            osd_up += 1
        else:
            osd_down += 1
        osd_id = osd.get("osd", "unknown")
        lines.append(f'ceph_osd_up{{osd="{osd_id}"}} {up}')

    lines.append("# HELP ceph_osd_summary OSD summary")
    lines.append("# TYPE ceph_osd_summary gauge")
    lines.append(f"ceph_osd_up_total {osd_up}")
    lines.append(f"ceph_osd_down_total {osd_down}")

    # PG states
    pg_states = {}
    for pg in pgs.get("pg_stats", []):
        state = pg.get("state", "unknown")
        pg_states[state] = pg_states.get(state, 0) + 1

    lines.append("# HELP ceph_pg_count PG count by state")
    lines.append("# TYPE ceph_pg_count gauge")
    for state, count in pg_states.items():
        lines.append(f'ceph_pg_count{{state="{state}"}} {count}')

    # Storage
    pool_stats = df.get("pools", [])
    total_bytes = sum(p.get("stats", {}).get("stored", 0) for p in pool_stats)
    total_bytes_avail = sum(p.get("stats", {}).get("max_avail", 0) for p in pool_stats)

    lines.append("# HELP ceph_storage Storage bytes")
    lines.append("# TYPE ceph_storage gauge")
    lines.append(f"ceph_storage_used_bytes {total_bytes}")
    lines.append(f"ceph_storage_available_bytes {total_bytes_avail}")

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
    server = HTTPServer(("0.0.0.0", 9342), Handler)
    print("Ceph exporter listening on :9342/metrics")
    server.serve_forever()

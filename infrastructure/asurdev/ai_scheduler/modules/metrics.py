#!/usr/bin/env python3
"""
AI Scheduler v2 — Metrics Layer
Prometheus integration: query live node metrics for scheduling decisions.
"""
import os
import requests
from typing import Optional

PROM = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
TIMEOUT = 5


def query(q: str) -> float:
    """Execute Prometheus instant query, return first value or 0."""
    try:
        r = requests.get(f"{PROM}/api/v1/query", params={"query": q}, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()["data"]["result"]
        if not data:
            return 0.0
        return float(data[0]["value"][1])
    except Exception:
        return 0.0


def gpu_util(instance: str) -> float:
    """GPU utilization % (DCGM)"""
    return query(f'DCGM_FI_DEV_GPU_UTIL{{instance="{instance}:9400"}}')


def gpu_mem_util(instance: str) -> float:
    """GPU memory utilization %"""
    return query(f'DCGM_FI_DEV_FB_USED{{instance="{instance}:9400"}}')


def gpu_temp(instance: str) -> float:
    """GPU temperature (C)"""
    return query(f'DCGM_FI_DEV_GPU_TEMP{{instance="{instance}:9400"}}')


def cpu_util(instance: str) -> float:
    """CPU utilization %"""
    idle = query(f'avg by(instance)(rate(node_cpu_seconds_total{{mode="idle",instance="{instance}:9100"}}[1m])) * 100')
    return max(0.0, 100.0 - idle)


def mem_util(instance: str) -> float:
    """Memory utilization %"""
    total = query(f'node_memory_MemTotal_bytes{{instance="{instance}:9100"}}')
    avail = query(f'node_memory_MemAvailable_bytes{{instance="{instance}:9100"}}')
    if total == 0:
        return 0.0
    return max(0.0, min(100.0, (1 - avail / total) * 100))


def disk_io_time(instance: str) -> float:
    """Disk I/O time %"""
    return query(f'node_disk_io_time_seconds_total{{instance="{instance}:9100"}}')


def network_latency(from_node: str, to_node: str) -> float:
    """Network latency estimate via prometheus blackbox or node_network_*"""
    tx_queue = query(f'node_network_transmit_queue_length{{instance="{from_node}:9100"}}')
    return tx_queue


def ceph_osd_latency() -> float:
    """Ceph OSD apply latency ms"""
    return query("ceph_osd_apply_latency_ms")


def ceph_osd_replication_latency() -> float:
    """Ceph OSD replication latency ms"""
    return query("ceph_osd_recovery_latency_ms")


def ceph_storage_used() -> float:
    """Ceph storage used (bytes)"""
    return query("ceph_osd_stat_bytes_used")


def ceph_storage_total() -> float:
    """Ceph storage total (bytes)"""
    return query("ceph_osd_stat_bytes")


def slurm_queue_depth(partition: str = "gpu") -> int:
    """Number of pending jobs in Slurm partition"""
    val = query(f'slurm_jobs_pending{{partition="{partition}"}}')
    return int(val)


def slurm_node_state(instance: str) -> str:
    """Slurm node state (UP/DOWN/DRAIN)"""
    val = query(f'slurm_node_state{{instance="{instance}"}}')
    state_map = {0: "UP", 1: "DOWN", 2: "DRAIN"}
    return state_map.get(int(val), "UNKNOWN")


def ray_active_workers(instance: str) -> int:
    """Ray active workers"""
    val = query(f'ray_runtime_metrics{{instance="{instance}:8265"}}')
    return int(val)


def wg_peer_handshake_age(peer: str) -> float:
    """WireGuard peer handshake age (seconds)"""
    return query(f'wireguard_peer_last_handshake_seconds{{peer="{peer}"}}')


def wg_peer_rx_bytes(peer: str) -> float:
    """WireGuard peer received bytes"""
    return query(f'wireguard_peer_rx_bytes_total{{peer="{peer}"}}')


def wg_peer_tx_bytes(peer: str) -> float:
    """WireGuard peer transmitted bytes"""
    return query(f'wireguard_peer_tx_bytes_total{{peer="{peer}"}}')


def get_node_metrics(node: str) -> dict:
    """Collect all metrics for a node."""
    return {
        "gpu_util": gpu_util(node),
        "gpu_mem_util": gpu_mem_util(node),
        "gpu_temp": gpu_temp(node),
        "cpu_util": cpu_util(node),
        "mem_util": mem_util(node),
        "disk_io_time": disk_io_time(node),
        "network_latency": network_latency(node, "gateway"),
        "slurm_queue": slurm_queue_depth(),
        "ray_workers": ray_active_workers(node),
    }

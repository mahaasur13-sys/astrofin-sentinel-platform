#!/usr/bin/env python3
"""
Failure Orchestrator — Detectors
Monitors cluster health: Slurm, Ceph, Ray, WireGuard, node reachability.
Each detector returns (is_down: bool, reason: str, severity: str)
"""
import subprocess
import time
import socket
from typing import Tuple


def slurm_controller_down() -> Tuple[bool, str, str]:
    """Check if Slurm controller is responsive."""
    try:
        out = subprocess.check_output(
            ["sinfo", "--nohead", "-N1"], timeout=5
        ).decode().strip()
        if not out:
            return True, "slurm_controller_no_response", "critical"
        return False, "", "ok"
    except subprocess.TimeoutExpired:
        return True, "slurm_controller_timeout", "critical"
    except FileNotFoundError:
        return True, "slurm_not_installed", "critical"
    except subprocess.CalledProcessError as e:
        return True, f"slurm_error_{e.returncode}", "critical"
    except Exception as e:
        return True, f"slurm_unknown_{e}", "warning"


def slurm_worker_down(node: str = "rk3576") -> Tuple[bool, str, str]:
    """Check if a Slurm compute node is DOWN or DRAINED."""
    try:
        out = subprocess.check_output(
            ["sinfo", "-N", "-o", "%T|%n", "--noheader"], timeout=5
        ).decode().strip()
        for line in out.splitlines():
            state, name = line.split("|")
            if name.strip() == node:
                if state.strip() in ("DOWN", "DRAIN", "DRAIN*"):
                    return True, f"slurm_node_{state.strip().lower()}_{node}", "critical"
                return False, "", "ok"
        return True, f"slurm_node_not_found_{node}", "warning"
    except Exception as e:
        return True, f"slurm_worker_check_failed_{e}", "warning"


def ceph_health_degraded() -> Tuple[bool, str, str]:
    """Check Ceph cluster health status."""
    try:
        out = subprocess.check_output(["ceph", "-s"], timeout=5).decode()
        if "HEALTH_OK" in out:
            return False, "", "ok"
        elif "HEALTH_WARN" in out:
            return True, "ceph_health_warn", "warning"
        elif "HEALTH_ERR" in out:
            return True, "ceph_health_err", "critical"
        return True, "ceph_unknown_state", "critical"
    except FileNotFoundError:
        return True, "ceph_not_installed", "critical"
    except subprocess.CalledProcessError as e:
        return True, f"ceph_command_failed_{e.returncode}", "critical"
    except Exception as e:
        return True, f"ceph_check_failed_{e}", "critical"


def ceph_osd_down(osd_id: str = "0") -> Tuple[bool, str, str]:
    """Check if a specific Ceph OSD is down."""
    try:
        out = subprocess.check_output(
            ["ceph", "osd", "status", osd_id, "--format", "json"], timeout=5
        ).decode()
        import json
        data = json.loads(out)
        if data.get("up", "0") == "0":
            return True, f"ceph_osd_{osd_id}_down", "critical"
        return False, "", "ok"
    except Exception:
        return False, "", "ok"


def ray_head_down() -> Tuple[bool, str, str]:
    """Check if Ray head is responsive."""
    try:
        out = subprocess.check_output(["ray", "status"], timeout=5).decode()
        if "RAY_CLUSTER" in out.upper() or "head" in out.lower():
            return False, "", "ok"
        return True, "ray_status_unexpected", "warning"
    except subprocess.TimeoutExpired:
        return True, "ray_timeout", "critical"
    except subprocess.CalledProcessError:
        return True, "ray_not_running", "critical"
    except FileNotFoundError:
        return True, "ray_not_installed", "critical"
    except Exception as e:
        return True, f"ray_check_failed_{e}", "warning"


def wireguard_peer_down(peer: str = "wg0") -> Tuple[bool, str, str]:
    """Check if WireGuard interface or peer is down."""
    try:
        out = subprocess.check_output(["wg", "show", peer], timeout=5).decode()
        if "latest handshake" in out:
            return False, "", "ok"
        return True, f"wg_{peer}_no_handshake", "warning"
    except FileNotFoundError:
        return True, "wg_not_installed", "warning"
    except subprocess.CalledProcessError:
        return True, f"wg_{peer}_interface_missing", "warning"
    except Exception as e:
        return True, f"wg_check_failed_{e}", "warning"


def node_unreachable(host: str, port: int = 22, timeout: int = 3) -> Tuple[bool, str, str]:
    """Check if a node is reachable via TCP (ssh port check)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return False, "", "ok"
        return True, f"node_{host}_port_{port}_unreachable", "warning"
    except Exception as e:
        return True, f"node_{host}_unreachable_{e}", "warning"


def gpu_available() -> Tuple[bool, str, str]:
    """Check if GPU is accessible and not in failure state."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=gpu_name,temperature.gpu,utilization.gpu",
             "--format=csv,noheader"], timeout=5
        ).decode()
        temp = int(out.strip().split(",")[1].strip())
        if temp > 90:
            return True, f"gpu_overheat_{temp}c", "critical"
        return False, "", "ok"
    except FileNotFoundError:
        return True, "nvidia_smi_missing", "critical"
    except subprocess.CalledProcessError:
        return True, "nvidia_smi_failed", "critical"
    except Exception as e:
        return True, f"gpu_check_failed_{e}", "warning"


def all_detectors() -> dict:
    """Run all detectors, return dict of results."""
    return {
        "slurm_controller": slurm_controller_down(),
        "slurm_worker_rk3576": slurm_worker_down("rk3576"),
        "ceph_health": ceph_health_degraded(),
        "ray_head": ray_head_down(),
        "wireguard_wg0": wireguard_peer_down("wg0"),
        "gpu": gpu_available(),
    }

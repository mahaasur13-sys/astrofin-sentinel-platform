#!/usr/bin/env python3
"""
Failure Orchestrator — Recovery Actions
Targeted recovery procedures per failure type.
Each function returns (success: bool, message: str)
"""
import subprocess
import time
import logging
from typing import Tuple

log = logging.getLogger("recovery")


def _run(cmd: list, timeout: int = 30) -> Tuple[bool, str]:
    try:
        result = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def restart_slurm_controller() -> Tuple[bool, str]:
    log.warning("Recovery: restarting slurmctld")
    ok, msg = _run(["systemctl", "restart", "slurmctld"])
    if ok:
        time.sleep(3)
        ok2, _ = _run(["systemctl", "is-active", "slurmctld"])
        if ok2:
            return True, "slurmctld restarted successfully"
    return False, f"slurmctld restart failed: {msg}"


def restart_slurm_worker(node: str = "rk3576") -> Tuple[bool, str]:
    log.warning(f"Recovery: restarting slurmd on {node}")
    ok, _ = _run(["ssh", node, "systemctl", "restart", "slurmd"])
    if not ok:
        return False, f"ssh or slurmd restart failed on {node}"
    time.sleep(3)
    ok2, _ = _run(["ssh", node, "systemctl", "is-active", "slurmd"])
    if ok2:
        return True, f"slurmd restarted successfully on {node}"
    return False, f"slurmd check failed on {node}"


def restart_ceph_osd(osd_id: str = "0") -> Tuple[bool, str]:
    log.warning(f"Recovery: restarting ceph-osd.{osd_id}")
    ok, msg = _run(["systemctl", "restart", f"ceph-osd@{osd_id}"])
    if ok:
        time.sleep(5)
        return True, f"ceph-osd.{osd_id} restarted"
    return False, f"ceph-osd.{osd_id} restart failed: {msg}"


def restart_ceph_mon(mon_id: str = "a") -> Tuple[bool, str]:
    log.warning(f"Recovery: restarting ceph-mon.{mon_id}")
    ok, msg = _run(["systemctl", "restart", f"ceph-mon@{mon_id}"])
    if ok:
        time.sleep(5)
        return True, f"ceph-mon.{mon_id} restarted"
    return False, f"ceph-mon.{mon_id} restart failed: {msg}"


def restart_ceph_manager() -> Tuple[bool, str]:
    log.warning("Recovery: restarting ceph-mgr")
    ok, msg = _run(["systemctl", "restart", "ceph-mgr@$(hostname)"])
    if ok:
        time.sleep(3)
        return True, "ceph-mgr restarted"
    return False, f"ceph-mgr restart failed: {msg}"


def restart_ceph() -> Tuple[bool, str]:
    log.warning("Recovery: full ceph cluster health check + repair")
    ok1, _ = _run(["ceph", "osd", "set", "noout"])
    ok2, msg = _run(["ceph", "osd", "out", "all"])
    ok3, _ = _run(["ceph", "health", "detail"])
    ok4, msg2 = _run(["ceph", "pg", "repair", "--all"])
    if ok3 or ok4:
        return True, "ceph repair commands sent"
    return False, f"ceph repair failed: {msg} {msg2}"


def restart_ray_head() -> Tuple[bool, str]:
    log.warning("Recovery: restarting Ray head")
    _run(["ray", "stop"])
    time.sleep(2)
    ok, msg = _run(["ray", "start", "--head", "--port=6379", "--dashboard-host=0.0.0.0", "-f"])
    if ok:
        return True, "ray head started"
    return False, f"ray start failed: {msg}"


def restart_ray_worker(node: str = "rk3576") -> Tuple[bool, str]:
    log.warning(f"Recovery: restarting Ray worker on {node}")
    ray_head_ip = "10.20.20.10"
    ok, _ = _run(["ssh", node, "ray", "stop"])
    if not ok:
        return False, f"ray stop failed on {node}"
    time.sleep(2)
    ok2, msg = _run([
        "ssh", node, "ray", "start", "--address", ray_head_ip, "--num-cpus=4"
    ])
    if ok2:
        return True, f"ray worker started on {node}"
    return False, f"ray worker start failed on {node}: {msg}"


def restart_wireguard(interface: str = "wg0") -> Tuple[bool, str]:
    log.warning(f"Recovery: restarting WireGuard interface {interface}")
    ok, msg = _run(["wg-quick", "down", interface])
    if not ok:
        pass
    time.sleep(2)
    ok2, msg2 = _run(["wg-quick", "up", interface])
    if ok2:
        return True, f"wireguard {interface} brought up"
    return False, f"wg-quick up failed: {msg2}"


def restart_nvidia_driver() -> Tuple[bool, str]:
    log.warning("Recovery: reloading NVIDIA driver")
    ok, msg = _run(["nvidia-smi"])
    if not ok:
        return False, "nvidia-smi not responding"
    ok2, msg2 = _run(["systemctl", "nvidia-smi"])
    if ok2:
        return True, "nvidia driver reloaded"
    return False, f"nvidia driver reload failed: {msg2}"


def reboot_node(node: str) -> Tuple[bool, str]:
    log.warning(f"Recovery: rebooting node {node}")
    ok, msg = _run(["ssh", node, "reboot"])
    if not ok:
        return False, f"reboot failed on {node}: {msg}"
    return True, f"reboot initiated on {node}"

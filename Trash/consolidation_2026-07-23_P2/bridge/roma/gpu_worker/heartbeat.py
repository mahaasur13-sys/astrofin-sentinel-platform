#!/usr/bin/env python3
"""GPU Worker Heartbeat Client — runs on each GPU node"""
import socket
import threading
import time
from typing import Optional

import requests


class HeartbeatClient:
    def __init__(
        self,
        worker_id: str,
        roma_control_plane: str,
        interval: int = 5,
        gpu_info: dict | None = None,
    ):
        self.worker_id = worker_id
        self.roma_url = roma_control_plane.rstrip("/")
        self.interval = interval
        self.gpu_info = gpu_info or self._probe_gpu()
        self._running = False
        self._thread: threading.Thread | None = None

    def _probe_gpu(self) -> dict:
        """Probe GPU info (mock for testing)"""
        try:
            import subprocess

            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                util, used, total = result.stdout.strip().split(", ")
                return {
                    "gpu_util": float(util) / 100.0,
                    "vram_used_gb": float(used) / 1024.0,
                    "vram_total_gb": float(total) / 1024.0,
                }
        except Exception:
            pass
        # Mock for testing
        return {"gpu_util": 0.0, "vram_used_gb": 0.0, "vram_total_gb": 8.0}

    def _heartbeat_loop(self):
        while self._running:
            try:
                gpu = self._probe_gpu()
                payload = {
                    "worker_id": self.worker_id,
                    "hostname": socket.gethostname(),
                    "gpu_util": gpu["gpu_util"],
                    "vram_used_gb": round(gpu["vram_used_gb"], 2),
                    "vram_total_gb": round(gpu["vram_total_gb"], 2),
                    "status": "healthy",
                }
                resp = requests.post(f"{self.roma_url}/worker/heartbeat", json=payload, timeout=3)
                if resp.status_code != 200:
                    print(f"[{self.worker_id}] heartbeat rejected: {resp.status_code}")
            except requests.RequestException as e:
                print(f"[{self.worker_id}] heartbeat failed: {e}")
            time.sleep(self.interval)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
        print(f"[{self.worker_id}] Heartbeat client started → {self.roma_url}")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print(f"[{self.worker_id}] Heartbeat client stopped")

    def report_job_start(self, job_id: str):
        """Call after acquiring GPU lock"""
        try:
            requests.post(
                f"{self.roma_url}/worker/job/start",
                json={"worker_id": self.worker_id, "job_id": job_id},
                timeout=3,
            )
        except Exception:
            pass

    def report_job_complete(self, job_id: str, success: bool):
        """Call after job finishes"""
        try:
            requests.post(
                f"{self.roma_url}/worker/job/complete",
                json={
                    "worker_id": self.worker_id,
                    "job_id": job_id,
                    "success": success,
                },
                timeout=3,
            )
        except Exception:
            pass


if __name__ == "__main__":
    # Test mock heartbeat
    client = HeartbeatClient(
        worker_id="gpu-node-test",
        roma_control_plane="http://localhost:8080",
        interval=3,
    )
    print(f"GPU info: {client.gpu_info}")
    print("Heartbeat client module: OK")

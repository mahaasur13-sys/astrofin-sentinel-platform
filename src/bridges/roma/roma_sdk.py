"""
ROMASDK — Python client for ROMA Execution Platform.
Usage:
    from roma_sdk import ROMAClient
    client = ROMAClient(base_url="http://localhost:8000")
    job = client.submit("train YOLOv8 on RTX3060", gpu_required=True)
    status = client.status(job["job_id"])
"""

import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass

API_BASE = "http://localhost:8000"


class ROMAException(Exception):
    pass


@dataclass
class ROMAJob:
    job_id: str
    status: str
    queue_priority: int
    dag: list
    estimated_resources: dict


class ROMAClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")

    def submit(
        self,
        task: str,
        *,
        gpu_required: bool = False,
        priority: int = 5,
        execution_mode: str = "k8s_job",
    ) -> ROMAJob:
        if not task or not task.strip():
            resp = requests.post(f"{self.base_url}/submit", json={"task": ""})
            if resp.status_code == 400:
                data = resp.json()
                raise ROMAException(
                    f"REJECTED: {data['error']['code']} — {data['error']['message']}"
                )
            resp.raise_for_status()

        payload = {
            "task": task,
            "gpu_required": gpu_required,
            "priority": priority,
            "execution_mode": execution_mode,
        }
        resp = requests.post(f"{self.base_url}/submit", json=payload)
        if resp.status_code == 429:
            raise ROMAException("BACKPRESSURE: Queue saturated, retry later")
        if resp.status_code >= 400:
            raise ROMAException(f"HTTP {resp.status_code}: {resp.text}")
        data = resp.json()
        return ROMAJob(
            job_id=data["job_id"],
            status=data["status"],
            queue_priority=data["roma_dispatch"]["queue_priority"],
            dag=data["dag"],
            estimated_resources=data["estimated_resources"],
        )

    def status(self, job_id: str) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/status/{job_id}")
        if resp.status_code == 404:
            raise ROMAException(f"Job {job_id} not found")
        resp.raise_for_status()
        return resp.json()

    def queue_status(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/queue/status")
        resp.raise_for_status()
        return resp.json()

    def health(self) -> bool:
        resp = requests.get(f"{self.base_url}/health")
        return resp.status_code == 200

    def submit_atom_cluster(self, task: str, cluster_spec: dict) -> "ROMAJob":
        """Submit execution as ATOMCluster managed job."""
        resp = requests.post(
            f"{self.base_url}/submit",
            json={
                "task": task,
                "execution_mode": "atom_cluster",
                "cluster_spec": cluster_spec,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return ROMAJob(
            job_id=data["job_id"],
            status=data["status"],
            queue_priority=data.get("queue_priority", 5),
            dag=data.get("dag", []),
            estimated_resources=data.get("estimated_resources", {}),
        )


if __name__ == "__main__":
    client = ROMAClient()
    print("ROMA SDK ready. Usage: client.submit('train YOLOv8')")

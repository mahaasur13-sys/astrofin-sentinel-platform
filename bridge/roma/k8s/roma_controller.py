#!/usr/bin/env python3
"""
ROMA K8s Controller — Reconciliation Loop (lightweight, no operator-sdk).
Watches RomaTask CRDs and dispatches to Execution Bridge.

Usage: python3 roma_controller.py --kubeconfig ~/.kube/config
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Kubernetes client (install via: pip install kubernetes)
try:
    from kubernetes import client, config, watch
    from kubernetes.client.rest import ApiException
    HAS_K8S = True
except ImportError:
    HAS_K8S = False
    print("WARNING: kubernetes client not installed. Controller running in DRY_RUN mode.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("roma-controller")

# =============================================================================
# K8s Client Setup
# =============================================================================

def get_k8s_client():
    if os.path.exists(os.path.expanduser("~/.kube/config")):
        config.load_kube_config()
    else:
        config.load_incluster_config()
    return client

def create_k8s_job_object(romatask: Dict[str, Any]) -> Dict[str, Any]:
    """Compile RomaTask → Kubernetes Job manifest."""
    spec = romatask.get("spec", {})
    task = spec.get("task", "")
    gpu_required = spec.get("gpuRequired", False)
    spec.get("executionMode", "k8s_job")
    spec.get("priority", 5)

    job_name = f"roma-{romatask['metadata']['name']}-{int(time.time())}"
    image = "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime"
    if gpu_required:
        image = "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime"

    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_name,
            "namespace": romatask["metadata"]["namespace"],
            "labels": {
                "app": "roma",
                "romatask-name": romatask["metadata"]["name"],
                "gpu-required": str(gpu_required).lower()
            }
        },
        "spec": {
            "backoffLimit": 0,
            "ttlSecondsAfterFinished": 300,
            "template": {
                "spec": {
                    "restartPolicy": "Never",
                    "nodeSelector": {"gpu": "true"} if gpu_required else {},
                    "containers": [{
                        "name": "roma-executor",
                        "image": image,
                        "command": ["python", "-c",
                            f"print('ROMA Task: {task}')"],
                        "resources": {
                            "limits": {"nvidia.com/gpu": "1"} if gpu_required else {},
                            "requests": {"nvidia.com/gpu": "1"} if gpu_required else {}
                        } if gpu_required else {}
                    }]
                }
            }
        }
    }
    return job_manifest

def update_romatask_status(api: client.ApiClient, romatask: Dict[str, Any], phase: str, job_name: Optional[str] = None, error: Optional[str] = None):
    """Update RomaTask status (PATCH)."""
    try:
        body = {
            "status": {
                "phase": phase,
                "jobId": romatask.get("status", {}).get("jobId", ""),
                "updatedAt": datetime.utcnow().isoformat() + "Z"
            }
        }
        if job_name:
            body["status"]["k8sJobName"] = job_name
        if error:
            body["status"]["error"] = error

        client.CustomObjectsApi(api).patch_namespaced_custom_object_status(
            group="roma.ai",
            version="v1",
            namespace=romatask["metadata"]["namespace"],
            plural="romatasks",
            name=romatask["metadata"]["name"],
            body=body
        )
    except Exception as e:
        log.error(f"Failed to update status: {e}")

# =============================================================================
# Reconciliation Loop
# =============================================================================

def run_controller(dry_run: bool = False):
    log.info("Starting ROMA Controller (dry_run={})".format(dry_run))

    if dry_run or not HAS_K8S:
        log.info("DRY RUN MODE: No real K8s operations")
        while True:
            time.sleep(10)

    api = get_k8s_client()
    custom_api = client.CustomObjectsApi(api)
    batch_api = client.BatchV1Api(api)

    w = watch.Watch()
    log.info("Watching for RomaTask resources...")

    for event in w.stream(custom_api.list_cluster_custom_object, "roma.ai", "v1", "romatasks"):
        romatask = event["object"]
        event_type = event["type"]
        name = romatask["metadata"]["name"]

        log.info(f"Event: {event_type} — RomaTask: {name}")

        if event_type == "ADDED":
            phase = romatask.get("status", {}).get("phase", "Pending")
            if phase == "Pending":
                log.info(f"Dispatching task: {name}")
                try:
                    job_manifest = create_k8s_job_object(romatask)
                    namespace = romatask["metadata"]["namespace"]
                    batch_api.create_namespaced_job(namespace, job_manifest)
                    job_name = job_manifest["metadata"]["name"]
                    update_romatask_status(api, romatask, "Queued", job_name)
                    log.info(f"Job created: {job_name}")
                except ApiException as e:
                    log.error(f"K8s API error: {e}")
                    update_romatask_status(api, romatask, "Failed", error=str(e))
                except Exception as e:
                    log.error(f"Dispatch error: {e}")
                    update_romatask_status(api, romatask, "Failed", error=str(e))

        elif event_type == "MODIFIED":
            # Monitor job completion
            current_phase = romatask.get("status", {}).get("phase", "Pending")
            job_name = romatask.get("status", {}).get("k8sJobName")
            if job_name and current_phase == "Queued":
                try:
                    job = batch_api.read_namespaced_job(job_name, romatask["metadata"]["namespace"])
                    if job.status.succeeded:
                        update_romatask_status(api, romatask, "Completed")
                        log.info(f"Task completed: {name}")
                    elif job.status.failed:
                        update_romatask_status(api, romatask, "Failed", error="Job failed")
                        log.info(f"Task failed: {name}")
                except Exception:
                    pass

        elif event_type == "DELETED":
            log.info(f"Task deleted: {name}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ROMA K8s Controller")
    parser.add_argument("--dry-run", action="store_true", help="Run without K8s connection")
    args = parser.parse_args()

    def sigterm_handler(signum, frame):
        log.info("Received SIGTERM, shutting down...")
        sys.exit(0)
    signal.signal(signal.SIGTERM, sigterm_handler)

    run_controller(dry_run=args.dry_run)

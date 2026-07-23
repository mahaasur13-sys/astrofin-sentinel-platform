"""
ROMA Execution Bridge — JSON → Kubernetes Job Compiler
Fixed: uses nvidia.com/gpu, nodeSelector, restartPolicy: Never
Supports: k8s_job (default) | ray_job fallback
"""

import copy


class K8sCompiler:
    """Transforms ROMA DAG into K8s Job manifest."""

    GPU_RESOURCE = "nvidia.com/gpu"
    GPU_NODE_SELECTOR = {"gpu": "true"}

    def __init__(self, execution_mode: str = "k8s_job"):
        self.execution_mode = execution_mode

    def compile(self, roma_json: dict) -> dict:
        task_id = roma_json.get("task_id", "unknown")
        dag = roma_json.get("dag", [])
        analysis = roma_json.get("analysis", {})
        gpu_required = analysis.get("gpu_required", False)
        resources = roma_json.get("resources", {})

        if self.execution_mode == "ray_job":
            return self._compile_rayjob(task_id, dag, gpu_required, resources)
        return self._compile_k8s_job(task_id, dag, gpu_required, resources)

    def _compile_k8s_job(self, task_id: str, dag: list, gpu_required: bool, resources: dict) -> dict:
        steps = []

        for i, node in enumerate(dag):
            step_name = f"step-{i}-{node['id']}"
            deps = [f"step-{j}-{d}" for j, n in enumerate(dag) for d in node.get("depends_on", []) if d == n["id"]]

            container = {
                "name": step_name,
                "image": node.get("image", "python:3.11-slim"),
                "command": (node.get("command", "").split() if node.get("command") else ["echo", "no command"]),
            }

            # GPU handling
            if gpu_required or node.get("gpu", False):
                container["resources"] = {
                    "limits": {"nvidia.com/gpu": "1"},
                    "requests": {"nvidia.com/gpu": "1"},
                }

            # CPU/RAM handling
            node_res = node.get("resources", {})
            cpu = node_res.get("cpu_cores", resources.get("cpu_cores", 1))
            mem = node_res.get("memory_gb", resources.get("memory_gb", 2))
            if "resources" not in container:
                container["resources"] = {}
            container["resources"].setdefault("requests", {})["cpu"] = f"{cpu}"
            container["resources"]["requests"]["memory"] = f"{mem}Gi"

            step = {
                "name": step_name,
                "container": container,
                "depends_on": deps if deps else None,
            }
            steps.append(step)

        # Build K8s Job (single-pod with init containers for DAG)
        job = self._build_job_manifest(task_id, steps, gpu_required)
        return job

    def _build_job_manifest(self, task_id: str, steps: list, gpu_required: bool) -> dict:
        containers = []
        init_containers = []

        if len(steps) == 1:
            # Single step — regular container
            containers.append(steps[0]["container"])
        else:
            # Multi-step DAG — use init containers + main
            for _i, step in enumerate(steps[:-1]):
                ic = copy.deepcopy(step["container"])
                ic["name"] = f"init-{step['name']}"
                init_containers.append(ic)
            containers.append(steps[-1]["container"])

        pod_spec = {
            "restartPolicy": "Never",
            "containers": containers,
        }
        if init_containers:
            pod_spec["initContainers"] = init_containers

        job_manifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": f"roma-{task_id[:8]}",
                "namespace": "roma-system",
                "labels": {"app": "roma-executor", "task_id": task_id},
            },
            "spec": {
                "backoffLimit": 2,
                "template": {
                    "metadata": {"labels": {"app": "roma-executor", "task_id": task_id}},
                    "spec": pod_spec,
                },
            },
        }

        if gpu_required:
            job_manifest["spec"]["template"]["spec"]["nodeSelector"] = self.GPU_NODE_SELECTOR
            job_manifest["spec"]["template"]["spec"]["tolerations"] = [
                {"key": "gpu", "operator": "Exists", "effect": "NoSchedule"}
            ]

        return job_manifest

    def _compile_rayjob(self, task_id: str, dag: list, gpu_required: bool, resources: dict) -> dict:
        """Fallback to RayJob if cluster uses Ray operator."""
        ray_job = {
            "apiVersion": "ray.io/v1alpha1",
            "kind": "RayJob",
            "metadata": {"name": f"roma-{task_id[:8]}", "namespace": "roma-system"},
            "spec": {
                "rayVersion": "2.9",
                "Entrypoint": dag[0]["command"] if dag else "echo done",
                "RayClusterSpec": {
                    "headGroupSpec": {
                        "replicas": 1,
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": "ray-head",
                                        "image": "rayproject/ray:latest-gpu",
                                        "resources": {
                                            "limits": {"gpu": "1" if gpu_required else "0"},
                                            "memory": "8Gi",
                                        },
                                    }
                                ]
                            }
                        },
                    }
                },
            },
        }
        return ray_job

    def validate(self, manifest: dict) -> tuple[bool, list]:
        """Security + correctness validation."""
        issues = []
        kind = manifest.get("kind", "")

        if kind == "Job":
            pod_spec = manifest["spec"]["template"]["spec"]
            if pod_spec.get("restartPolicy") != "Never":
                issues.append("restartPolicy must be Never for Job")
            if "hostPath" in str(manifest):
                issues.append("hostPath forbidden — security risk")
            if pod_spec.get("privileged", False):
                issues.append("privileged containers forbidden")
        return len(issues) == 0, issues

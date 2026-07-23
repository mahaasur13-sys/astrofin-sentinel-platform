"""
Update main.py to use execution_mode and new compiler.
"""

# In main.py — add execution_mode to SubmitTask request model:

class SubmitTask(BaseModel):
    roma_json: dict
    execution_mode: Literal["k8s_job", "ray_job"] = "k8s_job"  # NEW

# In submit handler — use mode:
@app.post("/submit")
async def submit_task(task: SubmitTask):
    compiler = K8sCompiler(execution_mode=task.execution_mode)
    manifest = compiler.compile(task.roma_json)
    valid, issues = compiler.validate(manifest)
    if not valid:
        raise HTTPException(400, f"Validation failed: {issues}")

    # ... submit to K8s (in-cluster or kubeconfig)
    api = client.BatchV1Api()
    namespace = manifest["metadata"]["namespace"]
    job_name = manifest["metadata"]["name"]
    api.create_namespaced_job(namespace, manifest)
    return {"job_id": job_name, "manifest": manifest, "mode": task.execution_mode}
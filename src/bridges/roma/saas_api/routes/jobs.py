"""ROMA SaaS API — GET /jobs route"""

from fastapi import APIRouter
from control_plane.job_store import JobStore

router = APIRouter()
_job_store = JobStore()


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = _job_store.get(job_id)
    if not job:
        from fastapi import HTTPException

        raise HTTPException(404, {"error": {"code": "NOT_FOUND", "message": f"Job {job_id} not found"}})
    return {"job": job, "logs_url": f"/jobs/{job_id}/logs"}


@router.get("/jobs")
def list_jobs(org_id: str = "demo_org", status: str = "", limit: int = 50):
    jobs = _job_store.list_jobs(org_id)
    if status:
        jobs = [j for j in jobs if j.get("status") == status.upper()]
    return {"jobs": jobs[:limit], "total": len(jobs), "org_id": org_id}


@router.get("/jobs/{job_id}/logs")
def get_job_logs(job_id: str):
    job = _job_store.get(job_id)
    if not job:
        from fastapi import HTTPException

        raise HTTPException(404, {"error": {"code": "NOT_FOUND", "message": f"Job {job_id} not found"}})
    return {"job_id": job_id, "stdout": "[SIMULATED] Running: " + job.get("task", ""), "stderr": "", "exit_code": None}

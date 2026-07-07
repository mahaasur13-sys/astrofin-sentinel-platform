"""ROMA SaaS API — POST /run endpoint"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
import uuid
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from control_plane.registry import WorkerRegistry
from control_plane.job_store import JobStore
from billing.ledger import BillingLedger
from billing.pricing_engine import PricingEngine

router = APIRouter()


class RunRequest(BaseModel):
    task: str
    gpu: Literal["auto", "RTX3060", "RTX4090", "A100", "H100"] = "auto"
    priority: Literal["low", "normal", "high"] = "normal"
    max_budget_usd: Optional[float] = None


class RunResponse(BaseModel):
    job_id: str
    status: str
    gpu: str
    estimated_cost: float
    gpu_seconds: int
    expires_at: int


_worker_reg = WorkerRegistry()
_job_store = JobStore()
_usage = BillingLedger()
_pricing = PricingEngine()


def _select_gpu(gpu: str, priority: str) -> str:
    workers = _worker_reg.list_all()
    if not workers:
        return "RTX4090"
    if gpu != "auto":
        available = [w for w in workers if w.get("gpu_type") == gpu]
        return gpu if available else workers[0].get("gpu_type", "RTX4090")
    for g in ["H100", "A100", "RTX4090", "RTX3060"] if priority == "high" else ["RTX4090", "RTX3060"]:
        available = [w for w in workers if w.get("gpu_type") == g]
        if available:
            return g
    return workers[0].get("gpu_type", "RTX4090")


@router.post("/run", response_model=RunResponse)
def run_endpoint(body: RunRequest):
    org_id = "demo_org"
    gpu_selected = _select_gpu(body.gpu, body.priority)
    gpu_seconds = _pricing.estimate_duration(body.task, gpu_selected)
    base_cost = _pricing.calculate({"task": body.task, "gpu_required": gpu_selected, "gpu_seconds": gpu_seconds})
    tier_markup = {"free": 2.5, "pro": 1.5, "enterprise": 1.0}
    tier = org_id.split("_")[0] if "_" in org_id else "pro"
    total_cost = round(base_cost * tier_markup.get(tier, 1.5), 4)
    if body.max_budget_usd and total_cost > body.max_budget_usd:
        raise HTTPException(422, {"error": {"code": "BUDGET_EXCEEDED", "message": f"Estimated cost {total_cost} > budget {body.max_budget_usd}"}})
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    _job_store.create(
        {
            "job_id": job_id,
            "org_id": org_id,
            "task": body.task,
            "gpu": gpu_selected,
            "gpu_seconds": gpu_seconds,
            "status": "QUEUED",
            "priority": body.priority,
            "cost_usd": total_cost,
            "created_at": time.time(),
        }
    )
    return RunResponse(job_id=job_id, status="queued", gpu=gpu_selected, estimated_cost=total_cost, gpu_seconds=gpu_seconds, expires_at=int(time.time()) + 86400)

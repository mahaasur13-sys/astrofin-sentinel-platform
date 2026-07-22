"""ROMA SaaS API — Health route"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "service": "ROMA SaaS API", "version": "1.0.0"}

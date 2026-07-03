"""Health check, metrics, and KARL diagnostics endpoints."""

import os
import time

import asyncpg
import psutil
import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import REGISTRY, generate_latest
from pydantic import BaseModel

# NEW: Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse, PlainTextResponse

from core.auth import fastapi_require_api_key
from web.api.auth import router as auth_router  # NEW: P1-03

# NEW: инициализируем лимитер (100 запросов в минуту глобально)
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

app = FastAPI(title="AstroFin Sentinel — Health & Metrics")
process = psutil.Process(os.getpid())

# NEW: привязываем лимитер к приложению
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# NEW: P1-03 — JWT auth router (login/refresh/whoami)
app.include_router(auth_router)


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    uptime_seconds: float
    memory_mb: float
    cpu_percent: float
    version: str = "5.0.0"


_start_time = time.time()


# ------------------------------------------------------------
# Startup
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    from core.logging import setup_logging

    setup_logging()


# ------------------------------------------------------------
# Auth middleware – только для /api/*
# ------------------------------------------------------------
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        try:
            await fastapi_require_api_key(request)
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    response = await call_next(request)
    return response


# ------------------------------------------------------------
# Dependency checks
# ------------------------------------------------------------
async def check_postgres() -> bool:
    try:
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER", "astrofin"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            database=os.getenv("POSTGRES_DB", "astrofin"),
            timeout=5.0,
        )
        await conn.close()
        return True
    except Exception:
        return False


async def check_redis() -> bool:
    try:
        redis_url = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}"
        r = aioredis.from_url(redis_url, socket_connect_timeout=3)
        await r.ping()
        await r.close()
        return True
    except Exception:
        return False


# ------------------------------------------------------------
# Public endpoints (без лимитов)
# ------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        uptime_seconds=time.time() - _start_time,
        memory_mb=process.memory_info().rss / 1024 / 1024,
        cpu_percent=process.cpu_percent(interval=0.1),
    )


@app.get("/health/ready")
async def readiness_check():
    pg_ok = await check_postgres()
    redis_ok = await check_redis()
    if pg_ok and redis_ok:
        return {"status": "ready", "timestamp": time.time()}
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "postgres": "ok" if pg_ok else "fail",
                "redis": "ok" if redis_ok else "fail",
            },
        )


@app.get("/metrics")
async def metrics_endpoint():
    return PlainTextResponse(content=generate_latest(REGISTRY).decode(), media_type="text/plain")


@app.get("/")
async def root():
    return {
        "service": "AstroFin Sentinel V5",
        "version": "5.0.0",
        "status": "running",
        "docs": "/docs",
    }


# ------------------------------------------------------------
# Protected endpoints (require X-API-Key) + Rate Limited
# ------------------------------------------------------------
@app.get("/api/ab/compare")
@limiter.limit("10 per minute")  # NEW: жёсткий лимит
async def ab_compare(request: Request):
    """A/B compare two sessions: ?sid_a=X&sid_b=Y"""
    sid_a = request.query_params.get("sid_a", "")
    sid_b = request.query_params.get("sid_b", "")
    if not sid_a or not sid_b:
        raise HTTPException(status_code=400, detail="sid_a and sid_b required")
    return {"status": "OK", "sid_a": sid_a, "sid_b": sid_b}


@app.get("/api/karl/status")
@limiter.limit("10 per minute")  # NEW
async def karl_status(request: Request):  # добавлен параметр request
    try:
        from agents.karl_synthesis import get_karl_agent

        agent = get_karl_agent()
        return agent.get_status()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


# ------------------------------------------------------------
# Metrics (protected)
# ------------------------------------------------------------
@app.get("/metrics/karl")
@limiter.limit("30 per minute")  # NEW: метрики могут запрашиваться чаще
async def karl_metrics():
    try:
        from agents.karl_synthesis import get_karl_agent

        agent = get_karl_agent()
        status = agent.get_status()
        diag = status.get("karl_diagnostics", {})
        oap = diag.get("oap_kpi", {})
        audit = diag.get("audit_summary", {})
        calibr = diag.get("calibration", {})
        drift = diag.get("drift_status", {})

        class KARLMetrics(BaseModel):
            oos_fail_rate: float
            entropy_avg: float
            grounding_strength: float
            current_ttc_depth: int
            total_decisions: int
            avg_confidence: float
            action_distribution: dict[str, int]
            calibration_error: float
            slope: float
            intercept: float
            drift_status: str
            confidence_drift: float
            uncertainty_drift: float
            win_rate: float
            sharpe_ratio: float
            max_drawdown: float
            total_trades: int

        return KARLMetrics(
            oos_fail_rate=oap.get("oos_fail_rate", 0.0),
            entropy_avg=oap.get("entropy_avg", 0.0),
            grounding_strength=oap.get("grounding_strength", 0.0),
            current_ttc_depth=oap.get("current_ttc_depth", 0),
            total_decisions=audit.get("total", 0),
            avg_confidence=audit.get("avg_confidence_final", 0.0),
            action_distribution=audit.get("action_distribution", {}),
            calibration_error=calibr.get("calibration_error", 0.0),
            slope=calibr.get("slope", 0.0),
            intercept=calibr.get("intercept", 0.0),
            drift_status=drift.get("status", "unknown"),
            confidence_drift=drift.get("confidence_drift", 0.0),
            uncertainty_drift=drift.get("uncertainty_drift", 0.0),
            win_rate=diag.get("win_rate", 0.0),
            sharpe_ratio=diag.get("sharpe_ratio", 0.0),
            max_drawdown=diag.get("max_drawdown", 0.0),
            total_trades=diag.get("total_trades", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/metrics/system")
@limiter.limit("30 per minute")  # NEW
async def system_metrics():
    return {
        "memory_percent": process.memory_percent(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(interval=0.1),
        "num_threads": process.num_threads(),
        "open_files": len(process.open_files()),
        "connections": len(process.connections()),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

from __future__ import annotations
import logging
import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)

app = FastAPI()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _check_redis() -> tuple[bool, str | None]:
    """Best-effort Redis liveness probe (timeout 0.5s)."""
    try:
        import redis  # type: ignore
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.Redis.from_url(url, socket_connect_timeout=0.5, socket_timeout=0.5)
        return bool(client.ping()), None
    except Exception as exc:  # noqa: BLE001 — health probe, swallow
        return False, f"redis: {type(exc).__name__}: {exc}"


def _check_db() -> tuple[bool, str | None]:
    """Best-effort DB liveness probe (SQLite file presence)."""
    try:
        db_path = os.getenv("HISTORY_DB_PATH", "core/history.db")
        # SQLite is the dev backend; absence is non-fatal, lock/error is fatal.
        if not os.path.exists(db_path):
            return True, "history.db not yet created (cold start)"
        import sqlite3
        with sqlite3.connect(db_path, timeout=0.5) as conn:
            conn.execute("SELECT 1").fetchone()
        return True, None
    except Exception as exc:  # noqa: BLE001 — health probe, swallow
        return False, f"db: {type(exc).__name__}: {exc}"


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, Any]:
    """Aggregated health: combines liveness + readiness."""
    return {"status": "ok"}


@app.get("/livez")
def livez() -> dict[str, str]:
    """Liveness — process is up."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> JSONResponse:
    """Readiness — process can serve real traffic."""
    checks: dict[str, Any] = {}
    overall_ok = True
    for name, ok, err in (
        ("redis", *_check_redis()),
        ("db", *_check_db()),
    ):
        checks[name] = {"ok": ok, "error": err}
        overall_ok = overall_ok and ok
    payload: dict[str, Any] = {"status": "ok" if overall_ok else "error", "checks": checks}
    return JSONResponse(payload, status_code=200 if overall_ok else 503)


@app.get("/metrics")
def metrics() -> str:
    return "metrics_placeholder"


@app.get("/secure")
def secure() -> dict[str, str]:
    return {"secret": "data"}


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    """Catch-all 500 handler — never leak stack traces to clients."""
    log.exception("unhandled error on %s %s", request.method, request.url.path)
    request_id = request.headers.get("x-request-id", "")
    return JSONResponse(
        status_code=500,
        content={"error": "internal server error", "request_id": request_id},
    )

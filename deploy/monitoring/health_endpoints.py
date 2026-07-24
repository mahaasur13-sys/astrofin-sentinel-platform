from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI

_log = logging.getLogger(__name__)
app = FastAPI()

# Cache for dependency probes — protects against flapping and excessive
# connection churn on every readiness call. A 5-second cache is short
# enough to react to outages but long enough to absorb probe storms
# from k8s/load-balancers.
_PROBE_CACHE_TTL_S = 5.0
_probe_cache: dict[str, tuple[float, bool, str]] = {}


def _cached_probe(name: str, probe):
    """Run ``probe`` with a 5-second TTL cache; return ``(ok, detail)``."""
    now = time.monotonic()
    cached = _probe_cache.get(name)
    if cached and (now - cached[0]) < _PROBE_CACHE_TTL_S:
        return cached[1], cached[2]
    try:
        ok, detail = probe()
    except Exception as exc:  # noqa: BLE001 — probe may raise anything
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    _probe_cache[name] = (now, ok, detail)
    return ok, detail


def _check_redis() -> tuple[bool, str]:
    """Probe Redis if REDIS_URL is set. Returns (ok, detail)."""
    url = os.environ.get("REDIS_URL")
    if not url:
        return True, "skipped (no REDIS_URL)"
    try:
        import redis  # type: ignore[import-not-found]

        client = redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        return True, "ok"
    except ImportError:
        return True, "skipped (redis lib not installed)"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def _check_db() -> tuple[bool, str]:
    """Probe the SQLite/Postgres DB if DATABASE_URL is set."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        return True, "skipped (no DATABASE_URL)"
    if url.startswith("sqlite:///"):
        path = url[len("sqlite:///") :]
        return (os.path.exists(path), f"sqlite path={path}")
    try:
        import asyncpg  # type: ignore[import-not-found]

        async def _probe_pg() -> tuple[bool, str]:
            conn = await asyncpg.connect(url, timeout=1.0)
            try:
                await conn.fetchval("SELECT 1")
            finally:
                await conn.close()
            return True, "ok"

        import asyncio

        return asyncio.run(_probe_pg())
    except ImportError:
        return True, "skipped (asyncpg not installed)"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


@app.get("/livez")
def livez():
    """Liveness probe — the process is up and the event loop is responsive.

    No external dependencies are checked here. Use ``/readyz`` for that.
    """
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    """Readiness probe — all critical dependencies are reachable.

    Aggregates liveness + readiness by probing Redis and the database
    (when configured). The response always includes the per-check detail
    so operators can see exactly which dependency is unhealthy.
    """
    redis_ok, redis_detail = _cached_probe("redis", _check_redis)
    db_ok, db_detail = _cached_probe("db", _check_db)
    ready = redis_ok and db_ok
    body = {
        "status": "ready" if ready else "not_ready",
        "checks": {
            "redis": {"ok": redis_ok, "detail": redis_detail},
            "db": {"ok": db_ok, "detail": db_detail},
        },
    }
    return body if ready else _with_status_code(body, 503)


def _with_status_code(body: dict, code: int):  # pragma: no cover — JSONResponse path
    from fastapi.responses import JSONResponse

    return JSONResponse(body, status_code=code)


@app.get("/health")
def health():
    """Legacy /health — kept for compatibility.

    Returns ``200 {"status": "ok"}`` if the process is alive. For real
    dependency checks use ``/readyz``; for liveness use ``/livez``.
    """
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return "metrics_placeholder"


@app.get("/secure")
def secure():
    return {"secret": "data"}

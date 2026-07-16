#!/usr/bin/env python3
"""ROMA SaaS API — HTTP API server with /run endpoint
Runs as: python3 -m saas_api.server
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from saas_api.middleware import LogRequestMiddleware
from saas_api.routes.health import router as health_router
from saas_api.routes.jobs import router as jobs_router
from saas_api.routes.run import router as run_router

app = FastAPI(title="ROMA SaaS API", version="1.0.0")

app.add_middleware(LogRequestMiddleware)

app.include_router(health_router)
app.include_router(run_router, prefix="/run", tags=["run"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

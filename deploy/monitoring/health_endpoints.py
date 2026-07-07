from __future__ import annotations
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return "metrics_placeholder"


@app.get("/secure")
def secure():
    return {"secret": "data"}

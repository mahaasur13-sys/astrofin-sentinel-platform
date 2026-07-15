#!/usr/bin/env python3
"""
ML Inference API — FastAPI service for online predictions.
POST /predict          — single node prediction
POST /predict/batch    — multi-node batch
GET  /health           — health check
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Inference API", version="5.0.0")

FAILURE_MODEL_PATH = os.environ.get(
    "FAILURE_MODEL_PATH",
    "/home/workspace/home-cluster-iac/ml_engine/registry/models/failure_model.pkl",
)
LOAD_MODEL_PATH = os.environ.get(
    "LOAD_MODEL_PATH",
    "/home/workspace/home-cluster-iac/ml_engine/registry/models/load_model.pkl",
)

_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        from ml_engine.inference.predictor import Predictor

        _predictor = Predictor(
            failure_model_path=(
                Path(FAILURE_MODEL_PATH) if Path(FAILURE_MODEL_PATH).exists() else None
            ),
            load_model_path=(
                Path(LOAD_MODEL_PATH) if Path(LOAD_MODEL_PATH).exists() else None
            ),
        )
    return _predictor


class PredictRequest(BaseModel):
    node_id: str
    features: dict | None = None


class BatchPredictRequest(BaseModel):
    node_ids: list[str]


class PredictResponse(BaseModel):
    node_id: str
    failure_probability: float
    load_forecast_queue: float
    load_forecast_gpu: float
    risk_score: float
    recommendation: str
    model_version: str


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    predictor = get_predictor()
    result = predictor.predict(req.node_id, req.features)
    return PredictResponse(node_id=req.node_id, **result)


@app.post("/predict/batch")
def predict_batch(req: BatchPredictRequest):
    predictor = get_predictor()
    results = predictor.predict_batch(req.node_ids)
    return {"predictions": [{"node_id": nid, **r} for nid, r in results.items()]}


@app.get("/health")
def health():
    return {"status": "ok", "version": "5.0.0"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("ML_API_PORT", 8081))
    uvicorn.run(app, host=os.environ.get("BIND_HOST", "127.0.0.1"), port=port)

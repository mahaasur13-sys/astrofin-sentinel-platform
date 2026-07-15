"""
ML Inference API — FastAPI application for real-time risk scoring.

Endpoints:
    POST /predict   — returns risk_score (probability of failure)
    GET  /explain/{prediction_id}  — returns SHAP explanations
    GET  /health    — liveness + model status
    GET  /metrics   — Prometheus-compatible metrics

Startup:
    Loads model + feature list once (on startup, not per-request).
    Validates that all expected features are present before accepting traffic.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query

from ml_engine.inference.schemas import (
    ExplainResponse,
    HealthResponse,
    MetricsInput,
    MetricsResponse,
    PredictionResponse,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("ml_inference")

# ---------------------------------------------------------------------------
# Paths — resolved relative to ml_engine/inference/ → repo root
# ---------------------------------------------------------------------------
_INFERENCE_DIR = Path(__file__).parent
_REPO_ROOT = _INFERENCE_DIR.parent.parent
_MODEL_DIR = _REPO_ROOT / "models"

_MODEL_PATH = os.environ.get("ML_MODEL_PATH", str(_MODEL_DIR / "failure_xgb_v2.pkl"))
_FEATURES_PATH = os.environ.get("ML_FEATURES_PATH", str(_MODEL_DIR / "features.txt"))

# ---------------------------------------------------------------------------
# Global state (set once at startup)
# ---------------------------------------------------------------------------
_model: Any = None
_feature_names: list[str] = []
_feature_cols_set: set[str] = set()
_model_version: str = "unknown"
_model_load_time_ms: float = 0.0
_start_time: float = time.time()

# Request statistics
_stats_total = 0
_stats_cache_hits = 0
_stats_cache_misses = 0
_stats_errors = 0
_stats_latencies_ms: list[float] = []

# In-memory prediction store for SHAP explainability
_predictions_store: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# SHAP (optional — loaded lazily)
# ---------------------------------------------------------------------------
_shap_available = False
_shap_explainer: Any = None


def _init_shap() -> None:
    """Lazily initialize SHAP explainer after model is loaded."""
    global _shap_available, _shap_explainer
    try:
        import shap

        if _model is None:
            logger.warning("SHAP init skipped — model not yet loaded")
            return

        _shap_explainer = shap.Explainer(_model, X_train_sample())
        _shap_available = True
        logger.info("SHAP explainer initialised")
    except Exception as exc:
        logger.warning("SHAP not available: %s", exc)


def X_train_sample(n: int = 500) -> pd.DataFrame:
    """Return a synthetic sample for SHAP tree explainer initialisation."""
    base = {
        "cpu_load_1": 0.3,
        "cpu_load_5": 0.3,
        "mem_used_pct": 50.0,
        "gpu_util": 50.0,
        "disk_usage_pct": 40.0,
    }
    rows = []
    for _ in range(n):
        row = {k: float(v) + np.random.normal(0, 0.05) for k, v in base.items()}
        row["node_id"] = "synthetic"
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
def load_model() -> tuple[Any, list[str], float]:
    """Load XGBoost model + feature list. Returns (model, feature_names, load_time_ms)."""
    t0 = time.perf_counter()

    import pickle

    model_path = Path(_MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    features_path = Path(_FEATURES_PATH)
    if not features_path.exists():
        raise FileNotFoundError(f"Features list not found: {features_path}")

    with open(features_path) as f:
        feature_names = [line.strip() for line in f if line.strip()]

    load_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "Model loaded in %.1f ms | features=%d | model=%s",
        load_ms,
        len(feature_names),
        model_path.name,
    )
    return model, feature_names, load_ms


def _on_startup() -> None:
    """Called by FastAPI lifespan on startup."""
    global _model, _feature_names, _feature_cols_set, _model_version, _model_load_time_ms

    logger.info("Loading model from %s …", _MODEL_PATH)
    _model, _feature_names, _model_load_time_ms = load_model()
    _model_version = _MODEL_PATH
    _feature_cols_set = set(_feature_names)

    logger.info("Validating feature columns (%d expected) …", len(_feature_names))
    _validate_features()

    _init_shap()
    logger.info("API startup complete — /health will return 'alive'")


def _validate_features() -> None:
    """Ensure the model was trained with all features that build_advanced_features produces."""
    try:
        from ml_engine.training.feature_builder import build_advanced_features

        # Synthetic row with all raw fields
        raw = pd.DataFrame([{
            "cpu_load_1": 0.3,
            "cpu_load_5": 0.3,
            "mem_used_pct": 50.0,
            "gpu_util": 50.0,
            "gpu_mem_used_pct": 50.0,
            "gpu_temp": 60.0,
            "gpu_power_draw": 150.0,
            "disk_read_bytes_sec": 1_000_000.0,
            "disk_write_bytes_sec": 500_000.0,
            "disk_usage_pct": 40.0,
            "net_recv_bytes_sec": 1_000_000.0,
            "net_send_bytes_sec": 500_000.0,
            "slurm_queue_depth": 5,
            "slurm_running_jobs": 2,
            "num_processes": 200,
            "open_files": 1000,
            "swap_used_pct": 0.0,
            "node_id": "validation_node",
            "timestamp": 0.0,
        }])

        df = build_advanced_features(raw, horizon_minutes=30)
        raw_feature_cols = {c for c in df.columns if c not in {
            "time", "node_id", "time_bucket", "label_bucket",
            "label_failure", "label_queue_depth", "label_gpu_util", "timestamp"
        }}

        missing = _feature_cols_set - raw_feature_cols
        extra = raw_feature_cols - _feature_cols_set

        if missing:
            logger.error("Model expects features NOT produced by build_advanced_features: %s", missing)
        if extra:
            logger.warning("build_advanced_features produces features NOT in model: %s", extra)

        if missing:
            raise RuntimeError(f"Feature mismatch — missing in feature builder: {missing}")

        logger.info("Feature validation passed (%d features)", len(_feature_cols_set))

    except Exception as exc:
        logger.error("Feature validation failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ML Inference API",
    description="Real-time failure risk scoring powered by XGBoost + SHAP",
    version="1.0.0",
    lifespan=None,  # manual startup below
)

# Register startup hook manually (works with uvicorn --reload too)
@app.on_event("startup")
def startup_event():
    _on_startup()


# ---------------------------------------------------------------------------
# Prometheus instrumentation (optional)
# ---------------------------------------------------------------------------
try:
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator().instrument(app).expose(app, endpoint="/prometheus")
    logger.info("Prometheus instrumentation enabled at /prometheus")
except ImportError:
    logger.warning("prometheus-fastapi-instrumentator not installed — /prometheus disabled")

Instrumentator = None  # placeholder if import fails


# ---------------------------------------------------------------------------
# Prediction cache (5-second TTL per input hash)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1024)
def _cached_predict(input_hash: str) -> float:
    """Cache lookup — returns cached risk_score for a given input hash."""
    return float("nan")  # sentinel — actual prediction stored separately


_cache_store: dict[str, tuple[float, float]] = {}  # hash → (score, timestamp)


def _get_cache_ttl() -> int:
    return 5


def _input_hash(data: dict) -> str:
    """Deterministic hash of the input metrics dict."""
    import hashlib
    import json
    safe = {k: v for k, v in data.items() if k not in ("node_id",)}
    return hashlib.sha256(json.dumps(safe, sort_keys=True).encode()).hexdigest()[:16]


def _cache_get(data: dict) -> float | None:
    h = _input_hash(data)
    if h in _cache_store:
        score, ts = _cache_store[h]
        if time.time() - ts < _get_cache_ttl():
            return score
        del _cache_store[h]
    return None


def _cache_put(data: dict, score: float) -> None:
    h = _input_hash(data)
    _cache_store[h] = (score, time.time())
    # Evict old entries
    now = time.time()
    for k in list(_cache_store.keys()):
        if now - _cache_store[k][1] > _get_cache_ttl() * 2:
            del _cache_store[k]


# ---------------------------------------------------------------------------
# /predict
# ---------------------------------------------------------------------------
@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Score failure risk for a node snapshot",
    tags=["inference"],
)
def predict(
    payload: MetricsInput,
    explain: bool = Query(False, description="Include SHAP explanations in response"),
) -> PredictionResponse:
    """
    Accept raw system metrics → build advanced features → return risk_score.

    The prediction is cached for 5 seconds to avoid redundant computation
    for the same input snapshot.
    """
    global _stats_total, _stats_cache_hits, _stats_cache_misses, _stats_errors, _stats_latencies_ms

    t0 = time.perf_counter()
    prediction_id = str(uuid.uuid4())[:8]

    try:
        payload_dict = payload.model_dump()

        # --- cache check ---
        cached = _cache_get(payload_dict)
        if cached is not None:
            _stats_cache_hits += 1
            latency_ms = (time.perf_counter() - t0) * 1000
            _stats_latencies_ms.append(latency_ms)
            return PredictionResponse(
                risk_score=cached,
                status="ok",
                prediction_id=prediction_id,
                explain_url=f"/explain/{prediction_id}" if explain else None,
                latency_ms=latency_ms,
            )

        _stats_cache_misses += 1

        # --- build features ---
        df = pd.DataFrame([payload_dict])

        from ml_engine.training.feature_builder import build_advanced_features

        df_feat = build_advanced_features(df, horizon_minutes=30)

        # Align columns to model feature order
        for col in _feature_names:
            if col not in df_feat.columns:
                df_feat[col] = 0.0
        df_feat = df_feat[_feature_names]

        # --- predict ---
        risk_score = float(_model.predict_proba(df_feat)[0, 1])

        # --- cache ---
        _cache_put(payload_dict, risk_score)

        # --- store for SHAP ---
        _predictions_store[prediction_id] = {
            "risk_score": risk_score,
            "df_feat": df_feat,
            "payload": payload_dict,
        }

        latency_ms = (time.perf_counter() - t0) * 1000
        _stats_latencies_ms.append(latency_ms)
        _stats_total += 1

        return PredictionResponse(
            risk_score=risk_score,
            status="ok",
            prediction_id=prediction_id,
            explain_url=f"/explain/{prediction_id}" if explain else None,
            latency_ms=latency_ms,
        )

    except Exception as exc:
        _stats_errors += 1
        logger.exception("Prediction failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Prediction error: {exc}")


# ---------------------------------------------------------------------------
# /explain/{prediction_id}
# ---------------------------------------------------------------------------
@app.get(
    "/explain/{prediction_id}",
    response_model=ExplainResponse,
    summary="Get SHAP explanation for a past prediction",
    tags=["inference"],
)
def explain_prediction(prediction_id: str) -> ExplainResponse:
    """Return SHAP values for a previously made prediction."""
    if not _shap_available:
        raise HTTPException(
            status_code=503,
            detail="SHAP is not available. Set SHAP_AVAILABLE=1 and restart.",
        )

    if prediction_id not in _predictions_store:
        raise HTTPException(status_code=404, detail=f"Prediction ID {prediction_id} not found")

    entry = _predictions_store[prediction_id]
    df_feat = entry["df_feat"]
    risk_score = entry["risk_score"]

    try:

        shap_values = _shap_explainer(df_feat)
        # shap_values.values shape: (1, n_features)
        sv = shap_values.values[0]
        names = list(df_feat.columns)

        sv_dict = {n: float(sv[i]) for i, n in enumerate(names)}
        abs_sv = {n: abs(v) for n, v in sv_dict.items()}
        top_pos = sorted([n for n, v in sv_dict.items() if v > 0], key=lambda n: sv_dict[n], reverse=True)[:5]
        top_neg = sorted([n for n, v in sv_dict.items() if v < 0], key=lambda n: sv_dict[n])[:5]

        return ExplainResponse(
            prediction_id=prediction_id,
            risk_score=risk_score,
            shap_values=sv_dict,
            feature_importance=abs_sv,
            top_positive_features=top_pos,
            top_negative_features=top_neg,
        )
    except Exception as exc:
        logger.exception("SHAP explanation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"SHAP error: {exc}")


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Liveness probe — returns 'alive' when model is loaded."""
    status = "alive" if _model is not None else "dead"
    return HealthResponse(
        status=status,
        model_loaded=_model is not None,
        feature_count=len(_feature_names),
        model_version=_model_version,
        uptime_seconds=time.time() - _start_time,
    )


# ---------------------------------------------------------------------------
# /metrics  (Prometheus text format)
# ---------------------------------------------------------------------------
@app.get("/metrics", response_model=MetricsResponse, tags=["monitoring"])
def metrics() -> MetricsResponse:
    """Custom application metrics in JSON (Prometheus-style fields)."""
    avg_lat = float(np.mean(_stats_latencies_ms)) if _stats_latencies_ms else 0.0
    return MetricsResponse(
        total_requests=_stats_total,
        cache_hits=_stats_cache_hits,
        cache_misses=_stats_cache_misses,
        avg_latency_ms=avg_lat,
        error_count=_stats_errors,
        model_load_time_ms=_model_load_time_ms,
    )


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
@app.get("/", tags=["info"])
def root():
    return {
        "service": "ML Inference API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "predict": "/predict",
    }

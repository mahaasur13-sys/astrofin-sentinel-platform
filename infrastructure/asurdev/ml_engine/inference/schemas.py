"""
Pydantic schemas for ML Inference API.

Defines input/output models for /predict, /explain, /health endpoints.
All fields map 1:1 to raw metrics used by build_advanced_features().
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class MetricsInput(BaseModel):
    """Raw system metrics — single snapshot from a node."""

    # === Time & identity ===
    timestamp: Optional[float] = None  # unix timestamp, auto-filled if missing
    node_id: str = "unknown"

    # === CPU ===
    cpu_load_1: float = Field(0.0, ge=0.0, le=1.0, description="CPU 1-min load avg (0-1)")
    cpu_load_5: float = Field(0.0, ge=0.0, le=1.0, description="CPU 5-min load avg (0-1)")

    # === Memory ===
    mem_used_pct: float = Field(0.0, ge=0.0, le=100.0, description="Memory used %")
    swap_used_pct: float = Field(0.0, ge=0.0, le=100.0, description="Swap used %")

    # === GPU ===
    gpu_util: float = Field(0.0, ge=0.0, le=100.0, description="GPU utilization %")
    gpu_mem_used_pct: float = Field(0.0, ge=0.0, le=100.0, description="GPU memory used %")
    gpu_temp: Optional[float] = Field(None, ge=0.0, le=120.0, description="GPU temperature °C")
    gpu_power_draw: Optional[float] = Field(None, ge=0.0, description="GPU power draw W")

    # === Disk I/O ===
    disk_read_bytes_sec: float = Field(0.0, ge=0.0, description="Disk read bytes/s")
    disk_write_bytes_sec: float = Field(0.0, ge=0.0, description="Disk write bytes/s")
    disk_usage_pct: float = Field(0.0, ge=0.0, le=100.0, description="Disk usage %")

    # === Network ===
    net_recv_bytes_sec: float = Field(0.0, ge=0.0, description="Network received bytes/s")
    net_send_bytes_sec: float = Field(0.0, ge=0.0, description="Network sent bytes/s")

    # === Queue depth (Slurm) ===
    slurm_queue_depth: int = Field(0, ge=0, description="Slurm pending+runnable jobs")
    slurm_running_jobs: int = Field(0, ge=0, description="Slurm running jobs")

    # === Process stats ===
    num_processes: int = Field(1, ge=1, description="Number of running processes")
    open_files: Optional[int] = Field(None, ge=0, description="Open file descriptors")

    # === Historical lag features (optional — auto-filled by API if not provided) ===
    cpu_load_lag1: Optional[float] = None
    mem_used_pct_lag1: Optional[float] = None
    gpu_util_lag1: Optional[float] = None
    disk_usage_pct_lag1: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "rtx3060-node-01",
                "cpu_load_1": 0.45,
                "cpu_load_5": 0.38,
                "mem_used_pct": 72.5,
                "swap_used_pct": 0.0,
                "gpu_util": 85.0,
                "gpu_mem_used_pct": 91.2,
                "gpu_temp": 67.0,
                "gpu_power_draw": 180.5,
                "disk_read_bytes_sec": 1024000.0,
                "disk_write_bytes_sec": 512000.0,
                "disk_usage_pct": 55.0,
                "net_recv_bytes_sec": 1048576.0,
                "net_send_bytes_sec": 524288.0,
                "slurm_queue_depth": 12,
                "slurm_running_jobs": 4,
                "num_processes": 312,
                "open_files": 1847,
            }
        }


class PredictionResponse(BaseModel):
    """Response from POST /predict."""

    risk_score: float = Field(..., ge=0.0, le=1.0, description="Probability of failure (0-1)")
    status: str = Field("ok", description="Status: 'ok', 'error', 'degraded'")
    prediction_id: str = Field(..., description="Unique ID for this prediction (for debugging)")
    explain_url: Optional[str] = Field(
        None, description="URL to get SHAP explanations (if explain=true)"
    )
    latency_ms: float = Field(..., description="Prediction latency in milliseconds")


class ExplainResponse(BaseModel):
    """Response from GET /explain/{prediction_id}."""

    prediction_id: str
    risk_score: float
    shap_values: dict[str, float] = Field(
        ..., description="SHAP values per feature — positive = pushes toward failure"
    )
    feature_importance: dict[str, float] = Field(
        ..., description="Absolute mean |SHAP| per feature"
    )
    top_positive_features: list[str] = Field(
        ..., description="Features most pushing toward failure"
    )
    top_negative_features: list[str] = Field(
        ..., description="Features most pushing away from failure"
    )


class HealthResponse(BaseModel):
    """Response from GET /health."""

    status: str = Field("alive", description="'alive' or 'degraded' or 'dead'")
    model_loaded: bool
    feature_count: int
    model_version: Optional[str] = None
    uptime_seconds: float


class MetricsResponse(BaseModel):
    """Response from GET /metrics — mirrors Prometheus format."""

    total_requests: int
    cache_hits: int
    cache_misses: int
    avg_latency_ms: float
    error_count: int
    model_load_time_ms: float

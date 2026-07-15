#!/usr/bin/env python3
"""
Feature Registry — declarative, versioned, reproducible feature definitions.
Transforms pipeline into deterministic function compiler.
"""
from typing import Dict, Any

# =============================================================================
# FEATURE REGISTRY — declarative specification
# =============================================================================
# Each feature: { "source": metric_name, "window": seconds, "agg": aggregation }
# Aggregation options: mean, std, min, max, slope, derivative, p95, count

FEATURE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # --- GPU features ---
    "gpu_mean_1m":     {"source": "gpu_util",      "window": 60,   "agg": "mean"},
    "gpu_mean_5m":     {"source": "gpu_util",      "window": 300,  "agg": "mean"},
    "gpu_mean_15m":    {"source": "gpu_util",      "window": 900,  "agg": "mean"},
    "gpu_std_5m":      {"source": "gpu_util",      "window": 300,  "agg": "std"},
    "gpu_slope_15m":   {"source": "gpu_util",      "window": 900,  "agg": "slope"},
    "gpu_p95_5m":      {"source": "gpu_util",      "window": 300,  "agg": "p95"},
    "gpu_max_15m":     {"source": "gpu_util",      "window": 900,  "agg": "max"},
    "gpu_temp_mean_5m": {"source": "gpu_temp",     "window": 300,  "agg": "mean"},

    # --- CPU features ---
    "cpu_mean_1m":     {"source": "cpu_util",      "window": 60,   "agg": "mean"},
    "cpu_mean_5m":     {"source": "cpu_util",      "window": 300,  "agg": "mean"},
    "cpu_std_5m":      {"source": "cpu_util",      "window": 300,  "agg": "std"},
    "cpu_slope_15m":   {"source": "cpu_util",      "window": 900,  "agg": "slope"},
    "cpu_max_15m":     {"source": "cpu_util",      "window": 900,  "agg": "max"},

    # --- Memory features ---
    "mem_mean_5m":     {"source": "mem_util",      "window": 300,  "agg": "mean"},
    "mem_p95_5m":      {"source": "mem_util",      "window": 300,  "agg": "p95"},
    "mem_max_15m":     {"source": "mem_util",      "window": 900,  "agg": "max"},
    "mem_growth_10m":  {"source": "mem_util",      "window": 600,  "agg": "derivative"},

    # --- Queue features ---
    "queue_depth":         {"source": "queue_size",     "window": 60,  "agg": "latest"},
    "queue_mean_5m":       {"source": "queue_size",     "window": 300, "agg": "mean"},
    "queue_derivative_5m": {"source": "queue_size",     "window": 300, "agg": "derivative"},
    "queue_p95_5m":        {"source": "queue_size",     "window": 300, "agg": "p95"},

    # --- Storage features ---
    "ceph_util_mean_5m":  {"source": "ceph_util",   "window": 300, "agg": "mean"},
    "ceph_iops_5m":       {"source": "ceph_iops",   "window": 300, "agg": "mean"},
    "ceph_latency_mean_5m": {"source": "ceph_lat", "window": 300, "agg": "mean"},

    # --- Network features ---
    "wg_latency_mean_1m":  {"source": "wg_latency", "window": 60,  "agg": "mean"},
    "wg_latency_std_5m":  {"source": "wg_latency", "window": 300, "agg": "std"},
    "wg_bytes_sent_5m":   {"source": "wg_sent",    "window": 300, "agg": "sum"},
    "wg_bytes_recv_5m":   {"source": "wg_recv",     "window": 300, "agg": "sum"},

    # --- Failure features ---
    "failure_count_1h":    {"source": "failure_events", "window": 3600, "agg": "count"},
    "failure_count_24h":   {"source": "failure_events", "window": 86400,"agg": "count"},
    "last_failure_age_min":{"source": "failure_events", "window": 86400,"agg": "last_age_min"},
    "consecutive_failures":{"source": "failure_events", "window": 86400,"agg": "consecutive"},

    # --- Ray features ---
    "ray_pending_tasks_5m":   {"source": "ray_pending",  "window": 300, "agg": "mean"},
    "ray_active_actors_5m":   {"source": "ray_actors",   "window": 300, "agg": "mean"},
    "ray_failed_tasks_1h":    {"source": "ray_failures", "window": 3600,"agg": "sum"},

    # --- Slurm features ---
    "slurm_queued_jobs_5m":   {"source": "slurm_queued",  "window": 300, "agg": "max"},
    "slurm_running_jobs_5m":  {"source": "slurm_running", "window": 300, "agg": "mean"},

    # --- Composite features ---
    "overload_score":    {"source": "gpu_util",  "window": 300, "agg": "overload_composite"},
    "health_score":      {"source": "cpu_util",  "window": 300, "agg": "health_composite"},
    "queue_volatility_5m": {"source": "queue_size", "window": 300, "agg": "volatility"},
}

# =============================================================================
# REGISTRY HELPERS
# =============================================================================

def get_feature_names() -> list:
    return list(FEATURE_REGISTRY.keys())

def get_features_by_source(source: str) -> Dict[str, Dict]:
    return {k: v for k, v in FEATURE_REGISTRY.items() if v["source"] == source}

def get_features_by_window(window_seconds: int) -> Dict[str, Dict]:
    return {k: v for k, v in FEATURE_REGISTRY.items() if v["window"] == window_seconds}

def get_registry_version() -> str:
    return "1.0.0"

def validate_registry() -> bool:
    for name, spec in FEATURE_REGISTRY.items():
        assert "source" in spec, f"Missing source in {name}"
        assert "window" in spec, f"Missing window in {name}"
        assert "agg" in spec, f"Missing agg in {name}"
        assert spec["window"] > 0, f"Window must be > 0 in {name}"
    return True

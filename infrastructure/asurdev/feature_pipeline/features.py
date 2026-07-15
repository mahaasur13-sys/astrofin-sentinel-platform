#!/usr/bin/env python3
"""
Feature Definitions — complete set of ML-ready features per node.
Each feature is a callable that returns a float from raw metrics.
"""
from typing import Callable, Dict, List

FeatureFunc = Callable[[Dict], float]


class Feature:
    """Typed feature with name, description, unit."""
    def __init__(self, name: str, fn: FeatureFunc, unit: str = "", description: str = ""):
        self.name = name
        self.fn = fn
        self.unit = unit
        self.description = description

    def __call__(self, ctx: Dict) -> float:
        return self.fn(ctx)


# =============================================================================
# GPU FEATURES
# =============================================================================
GPU_FEATURES: List[Feature] = [
    Feature(
        name="gpu_mean_5m",
        fn=lambda c: c.get("gpu_util", {}).get("5m", {}).get("mean", 0.0),
        unit="percent",
        description="GPU utilization mean over 5 min",
    ),
    Feature(
        name="gpu_slope_15m",
        fn=lambda c: c.get("gpu_util", {}).get("15m", {}).get("slope", 0.0),
        unit="percent_per_min",
        description="GPU trend direction over 15 min",
    ),
    Feature(
        name="gpu_p95_5m",
        fn=lambda c: c.get("gpu_util", {}).get("5m", {}).get("p95", 0.0),
        unit="percent",
        description="GPU 95th percentile over 5 min",
    ),
    Feature(
        name="gpu_max_15m",
        fn=lambda c: c.get("gpu_util", {}).get("15m", {}).get("max", 0.0),
        unit="percent",
        description="GPU max over 15 min",
    ),
    Feature(
        name="gpu_std_5m",
        fn=lambda c: c.get("gpu_util", {}).get("5m", {}).get("std", 0.0),
        unit="percent",
        description="GPU utilization variance",
    ),
]

# =============================================================================
# CPU FEATURES
# =============================================================================
CPU_FEATURES: List[Feature] = [
    Feature(
        name="cpu_mean_5m",
        fn=lambda c: c.get("cpu_util", {}).get("5m", {}).get("mean", 0.0),
        unit="percent",
        description="CPU utilization mean over 5 min",
    ),
    Feature(
        name="cpu_slope_15m",
        fn=lambda c: c.get("cpu_util", {}).get("15m", {}).get("slope", 0.0),
        unit="percent_per_min",
        description="CPU trend over 15 min",
    ),
    Feature(
        name="cpu_spike_1m",
        fn=lambda c: max(0.0, c.get("cpu_util", {}).get("1m", {}).get("mean", 0.0) -
                          c.get("cpu_util", {}).get("5m", {}).get("mean", 0.0)),
        unit="percent",
        description="CPU sudden increase (1m vs 5m delta)",
    ),
]

# =============================================================================
# MEMORY FEATURES
# =============================================================================
MEM_FEATURES: List[Feature] = [
    Feature(
        name="mem_mean_5m",
        fn=lambda c: c.get("mem_util", {}).get("5m", {}).get("mean", 0.0),
        unit="percent",
        description="Memory utilization mean",
    ),
    Feature(
        name="mem_pressure_1m",
        fn=lambda c: c.get("mem_util", {}).get("1m", {}).get("max", 0.0),
        unit="percent",
        description="Memory peak in last minute",
    ),
]

# =============================================================================
# QUEUE FEATURES
# =============================================================================
QUEUE_FEATURES: List[Feature] = [
    Feature(
        name="queue_depth",
        fn=lambda c: c.get("queue_depth", 0),
        unit="jobs",
        description="Current Slurm queue depth",
    ),
    Feature(
        name="queue_derivative",
        fn=lambda c: c.get("queue_derivative", 0.0),
        unit="jobs_per_min",
        description="Queue growth rate",
    ),
    Feature(
        name="queue_p95_5m",
        fn=lambda c: c.get("queue_p95_5m", 0),
        unit="jobs",
        description="Queue 95th percentile over 5 min",
    ),
]

# =============================================================================
# STORAGE FEATURES
# =============================================================================
STORAGE_FEATURES: List[Feature] = [
    Feature(
        name="ceph_iops_mean_5m",
        fn=lambda c: c.get("ceph_iops", {}).get("5m", {}).get("mean", 0.0),
        unit="iops",
        description="Ceph IOPS mean over 5 min",
    ),
    Feature(
        name="ceph_latency_ms_mean_5m",
        fn=lambda c: c.get("ceph_latency_ms", {}).get("5m", {}).get("mean", 0.0),
        unit="ms",
        description="Ceph write latency mean",
    ),
]

# =============================================================================
# NETWORK FEATURES
# =============================================================================
NETWORK_FEATURES: List[Feature] = [
    Feature(
        name="wg_handshake_age",
        fn=lambda c: c.get("wg_handshake_age", 0),
        unit="seconds",
        description="WireGuard peer handshake age (0=connected, large=stale)",
    ),
    Feature(
        name="node_latency_ms_mean_5m",
        fn=lambda c: c.get("node_latency_ms", {}).get("5m", {}).get("mean", 0.0),
        unit="ms",
        description="Node round-trip latency",
    ),
]

# =============================================================================
# FAILURE FEATURES
# =============================================================================
FAILURE_FEATURES: List[Feature] = [
    Feature(
        name="failure_count_1h",
        fn=lambda c: c.get("failure_count_1h", 0),
        unit="count",
        description="Node failures in last hour",
    ),
    Feature(
        name="failure_count_24h",
        fn=lambda c: c.get("failure_count_24h", 0),
        unit="count",
        description="Node failures in last 24h",
    ),
    Feature(
        name="last_failure_age_min",
        fn=lambda c: c.get("last_failure_age_min", -1),
        unit="minutes",
        description="Minutes since last failure (-1 = never)",
    ),
    Feature(
        name="consecutive_failures",
        fn=lambda c: c.get("consecutive_failures", 0),
        unit="count",
        description="Consecutive failure count",
    ),
]

# =============================================================================
# COMPOSITE FEATURES
# =============================================================================
COMPOSITE_FEATURES: List[Feature] = [
    Feature(
        name="overload_score",
        fn=lambda c: (
            c.get("gpu_util", {}).get("5m", {}).get("mean", 0.0) * 0.5 +
            c.get("cpu_util", {}).get("5m", {}).get("mean", 0.0) * 0.3 +
            c.get("mem_util", {}).get("5m", {}).get("mean", 0.0) * 0.2
        ),
        unit="percent",
        description="Composite system overload indicator",
    ),
    Feature(
        name="health_score",
        fn=lambda c: max(0.0, 100.0 - c.get("failure_count_1h", 0) * 10.0),
        unit="percent",
        description="Node health score (100 = healthy)",
    ),
]

ALL_FEATURES = (
    GPU_FEATURES + CPU_FEATURES + MEM_FEATURES +
    QUEUE_FEATURES + STORAGE_FEATURES + NETWORK_FEATURES +
    FAILURE_FEATURES + COMPOSITE_FEATURES
)

FEATURE_NAMES = [f.name for f in ALL_FEATURES]

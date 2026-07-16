#!/usr/bin/env python3
"""
Window Engine — sliding aggregation core for feature pipeline.
Builds time windows: 1m, 5m, 15m, 1h with typed aggregates.
"""
import math
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# =============================================================================
# AGGREGATION FUNCTIONS
# =============================================================================


def _mean(data: list[float]) -> float:
    return sum(data) / len(data) if data else 0.0


def _std(data: list[float]) -> float:
    if len(data) < 2:
        return 0.0
    m = _mean(data)
    variance = sum((x - m) ** 2 for x in data) / (len(data) - 1)
    return math.sqrt(variance)


def _min(data: list[float]) -> float:
    return min(data) if data else 0.0


def _max(data: list[float]) -> float:
    return max(data) if data else 0.0


def _slope(data: list[float]) -> float:
    """Linear regression slope over data points."""
    if len(data) < 2:
        return 0.0
    n = len(data)
    t = list(range(n))
    sum_t = sum(t)
    sum_y = sum(data)
    sum_tt = sum(ti * ti for ti in t)
    sum_ty = sum(ti * yi for ti, yi in zip(t, data))
    denom = n * sum_tt - sum_t * sum_t
    if abs(denom) < 1e-10:
        return 0.0
    slope = (n * sum_ty - sum_t * sum_y) / denom
    return slope


def _derivative(data: list[float]) -> float:
    """Rate of change: (last - first) / count."""
    if len(data) < 2:
        return 0.0
    return (data[-1] - data[0]) / len(data)


def _p95(data: list[float]) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    idx = int(len(s) * 0.95)
    return s[min(idx, len(s) - 1)]


def _latest(data: list[float]) -> float:
    return data[-1] if data else 0.0


def _count(data: list[float]) -> float:
    return float(len(data))


def _last_age_min(timestamps: list[datetime]) -> float:
    """Age of last failure in minutes."""
    if not timestamps:
        return -1.0
    return (datetime.now() - timestamps[-1]).total_seconds() / 60.0


def _consecutive(data: list[str]) -> float:
    """Count consecutive failures ending at current time."""
    count = 0
    for val in reversed(data):
        if val == "failure":
            count += 1
        else:
            break
    return float(count)


AGG_FUNCTIONS: dict[str, Callable] = {
    "mean": _mean,
    "std": _std,
    "min": _min,
    "max": _max,
    "slope": _slope,
    "derivative": _derivative,
    "p95": _p95,
    "latest": _latest,
    "count": _count,
    "last_age_min": _last_age_min,
}

# =============================================================================
# TIME WINDOW CONFIG
# =============================================================================

WINDOW_SIZES_SECONDS = [60, 300, 900, 3600]  # 1m, 5m, 15m, 1h


@dataclass
class WindowConfig:
    name: str
    size_seconds: int
    aggregates: list[str]  # which agg functions to apply


DEFAULT_WINDOWS = [
    WindowConfig(name="1m", size_seconds=60, aggregates=["mean", "std", "min", "max", "latest"]),
    WindowConfig(
        name="5m",
        size_seconds=300,
        aggregates=["mean", "std", "min", "max", "latest", "slope", "p95"],
    ),
    WindowConfig(name="15m", size_seconds=900, aggregates=["mean", "std", "max", "slope"]),
    WindowConfig(name="1h", size_seconds=3600, aggregates=["mean", "std", "max"]),
]

# =============================================================================
# SLIDING WINDOW
# =============================================================================


@dataclass
class SlidingWindow:
    """Sliding window for a single metric on a single node."""

    node_id: str
    metric_name: str
    window_seconds: int
    _buffer: deque = field(default_factory=lambda: deque(maxlen=3600))  # 1h max
    _timestamps: deque = field(default_factory=lambda: deque(maxlen=3600))

    def push(self, value: float, timestamp: datetime | None = None) -> None:
        ts = timestamp or datetime.now()
        self._buffer.append(value)
        self._timestamps.append(ts)

    def get_window(self, cutoff: datetime) -> list[float]:
        """Get all values within window ending at cutoff."""
        start = cutoff - timedelta(seconds=self.window_seconds)
        result = []
        for i, ts in enumerate(self._timestamps):
            if ts >= start:
                result.append(self._buffer[i])
        return result

    def get_values(self) -> list[float]:
        return list(self._buffer)

    def get_timestamps(self) -> list[datetime]:
        return list(self._timestamps)

    def aggregate(self, agg: str) -> float:
        """Apply aggregation to current buffer (all data in window)."""
        if agg not in AGG_FUNCTIONS:
            return 0.0
        return AGG_FUNCTIONS[agg](list(self._buffer))

    def clear(self) -> None:
        self._buffer.clear()
        self._timestamps.clear()


# =============================================================================
# WINDOW ENGINE
# =============================================================================


class WindowEngine:
    """
    Central window management: stores SlidingWindows per (node, metric),
    computes aggregations on demand.
    """

    def __init__(self, windows: list[WindowConfig] | None = None):
        self.windows_configs: list[WindowConfig] = windows or DEFAULT_WINDOWS
        # _storage: {(node_id, metric_name): SlidingWindow}
        self._storage: dict[tuple, SlidingWindow] = {}
        self._sources = [
            "gpu_util",
            "gpu_temp",
            "cpu_util",
            "mem_util",
            "queue_size",
            "ceph_util",
            "ceph_iops",
            "ceph_lat",
            "wg_latency",
            "wg_sent",
            "wg_recv",
            "failure_events",
            "ray_pending",
            "ray_actors",
            "ray_failures",
            "slurm_queued",
            "slurm_running",
        ]

    def _get_or_create_window(self, node_id: str, metric: str, window_seconds: int) -> SlidingWindow:
        key = (node_id, metric, window_seconds)
        if key not in self._storage:
            self._storage[key] = SlidingWindow(node_id, metric, window_seconds)
        return self._storage[key]

    def push(self, node_id: str, metric: str, value: float, timestamp: datetime | None = None) -> None:
        """Push a metric value for a node."""
        for wc in self.windows_configs:
            w = self._get_or_create_window(node_id, metric, wc.size_seconds)
            w.push(value, timestamp)

    def get_window_data(self, node_id: str, metric: str, window_seconds: int) -> list[float]:
        key = (node_id, metric, window_seconds)
        if key not in self._storage:
            return []
        return self._storage[key].get_values()

    def get_aggregated(self, node_id: str, metric: str, window_seconds: int, agg: str) -> float:
        key = (node_id, metric, window_seconds)
        if key not in self._storage:
            return 0.0
        return self._storage[key].aggregate(agg)

    def get_all_windows_for_node(self, node_id: str) -> dict[str, dict[str, float]]:
        """Get all aggregated features for a node across all metrics/windows/aggregates."""
        result = {}
        for (nid, metric, ws), window in self._storage.items():
            if nid != node_id:
                continue
            for agg_name, agg_fn in AGG_FUNCTIONS.items():
                val = window.aggregate(agg_name)
                key = f"{metric}_{agg_name}_{ws}s"
                result[key] = val
        return result

    def clear_node(self, node_id: str) -> None:
        """Clear all windows for a node."""
        to_delete = [k for k in self._storage if k[0] == node_id]
        for k in to_delete:
            del self._storage[k]

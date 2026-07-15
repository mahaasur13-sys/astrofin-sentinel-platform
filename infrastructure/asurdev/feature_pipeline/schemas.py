#!/usr/bin/env python3
"""
Feature Schemas — typed definitions for ML-ready feature vectors.
Provides Pydantic models and dataclasses for feature consistency.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class NodeRole(Enum):
    GPU   = "gpu"      # RTX 3060 compute node
    CPU   = "cpu"      # RK3576 lightweight
    ARM   = "arm"      # additional ARM nodes
    VPS   = "vps"      # cloud VPS (Ceph MON)
    UNKNOWN = "unknown"

class JobType(Enum):
    GPU_BATCH    = "gpu_batch"
    CPU_BATCH    = "cpu_batch"
    INFERENCE    = "inference"
    TRAINING     = "training"
    DATA_LOAD    = "data_load"
    UNKNOWN      = "unknown"

class LabelType(Enum):
    HEALTHY   = 0
    DEGRADED  = 1
    FAILED    = 2

# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class FeatureVector:
    """A single feature vector at a point in time for a specific node."""
    node_id: str
    timestamp: datetime
    features: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "timestamp": self.timestamp.isoformat(),
            "features": self.features,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "FeatureVector":
        ts = d["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            node_id=d["node_id"],
            timestamp=ts,
            features=d["features"],
            metadata=d.get("metadata", {}),
        )

@dataclass
class LabeledExample:
    """A supervised learning example: features → label."""
    node_id: str
    timestamp: datetime
    horizon_minutes: int  # how far ahead we're predicting
    features: Dict[str, float]
    label: int  # 0=healthy, 1=degraded, 2=failed
    job_id: Optional[str] = None

    def to_ml_dict(self) -> Dict:
        """Convert to flat dict for CSV export."""
        row = {
            "node_id": self.node_id,
            "timestamp": self.timestamp.isoformat(),
            "horizon_min": self.horizon_minutes,
            "label": self.label,
        }
        if self.job_id:
            row["job_id"] = self.job_id
        row.update({f"feat_{k}": v for k, v in self.features.items()})
        return row

@dataclass
class FeatureSpec:
    """Specification for a single feature."""
    name: str
    source: str
    window_seconds: int
    aggregation: str
    description: str = ""
    unit: str = ""
    typical_range: tuple = (0.0, 100.0)  # (min, max) typical values

@dataclass
class NodeProfile:
    """Node hardware + workload profile for embedding."""
    node_id: str
    role: NodeRole
    gpu_capacity: float       # TFLOPS or similar
    cpu_cores: int
    memory_gb: int
    storage_gb: int
    network_mbps: int
    historical_failure_rate: float  # failures per day
    avg_latency_ms: float
    queue_volatility: float   # std of queue size over 24h

    def to_embedding_vector(self) -> List[float]:
        return [
            self.gpu_capacity,
            float(self.cpu_cores),
            float(self.memory_gb),
            float(self.storage_gb),
            float(self.network_mbps),
            self.historical_failure_rate,
            self.avg_latency_ms,
            self.queue_volatility,
        ]

@dataclass
class MLBatch:
    """A batch of labeled examples for training/validation."""
    train: List[LabeledExample]
    val: List[LabeledExample]
    test: List[LabeledExample]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_csv(self, path: str, split: str = "train") -> None:
        """Export a split to CSV."""
        examples = getattr(self, split, [])
        if not examples:
            return
        keys = list(examples[0].to_ml_dict().keys())
        with open(path, "w", newline="") as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for ex in examples:
                writer.writerow(ex.to_ml_dict())

    @property
    def train_size(self) -> int: return len(self.train)
    @property
    def val_size(self) -> int: return len(self.val)
    @property
    def test_size(self) -> int: return len(self.test)
    @property
    def total_size(self) -> int: return self.train_size + self.val_size + self.test_size

# =============================================================================
# SCHEMA VALIDATION
# =============================================================================

FEATURE_SPECS: List[FeatureSpec] = [
    # GPU
    FeatureSpec(name="gpu_mean_1m",  source="gpu_util", window_seconds=60,   aggregation="mean", unit="%", typical_range=(0, 100)),
    FeatureSpec(name="gpu_mean_5m",  source="gpu_util", window_seconds=300,  aggregation="mean", unit="%", typical_range=(0, 100)),
    FeatureSpec(name="gpu_std_5m",   source="gpu_util", window_seconds=300,  aggregation="std",  unit="%", typical_range=(0, 50)),
    FeatureSpec(name="gpu_slope_15m",source="gpu_util", window_seconds=900,  aggregation="slope", unit="%/min", typical_range=(-5, 5)),
    FeatureSpec(name="gpu_p95_5m",   source="gpu_util", window_seconds=300,  aggregation="p95",  unit="%", typical_range=(0, 100)),
    FeatureSpec(name="gpu_max_15m",  source="gpu_util", window_seconds=900,  aggregation="max",  unit="%", typical_range=(0, 100)),
    FeatureSpec(name="gpu_temp_mean_5m", source="gpu_temp", window_seconds=300, aggregation="mean", unit="°C", typical_range=(30, 95)),
    # Queue
    FeatureSpec(name="queue_depth",          source="queue_size", window_seconds=60,  aggregation="latest", unit="jobs", typical_range=(0, 200)),
    FeatureSpec(name="queue_mean_5m",        source="queue_size", window_seconds=300, aggregation="mean",  unit="jobs", typical_range=(0, 200)),
    FeatureSpec(name="queue_derivative_5m",  source="queue_size", window_seconds=300, aggregation="derivative", unit="jobs/min", typical_range=(-20, 20)),
    FeatureSpec(name="queue_p95_5m",         source="queue_size", window_seconds=300, aggregation="p95", unit="jobs", typical_range=(0, 200)),
    # Failure
    FeatureSpec(name="failure_count_1h",    source="failure_events", window_seconds=3600, aggregation="count", unit="failures", typical_range=(0, 50)),
    FeatureSpec(name="failure_count_24h",   source="failure_events", window_seconds=86400,aggregation="count", unit="failures", typical_range=(0, 200)),
    FeatureSpec(name="last_failure_age_min",source="failure_events", window_seconds=86400,aggregation="last_age_min", unit="min", typical_range=(0, 1440)),
    FeatureSpec(name="consecutive_failures",source="failure_events", window_seconds=86400,aggregation="consecutive", unit="failures", typical_range=(0, 10)),
    # Composite
    FeatureSpec(name="overload_score",      source="gpu_util", window_seconds=300, aggregation="overload_composite", unit="score", typical_range=(0, 100)),
    FeatureSpec(name="health_score",        source="cpu_util", window_seconds=300, aggregation="health_composite", unit="score", typical_range=(0, 100)),
    FeatureSpec(name="queue_volatility_5m", source="queue_size", window_seconds=300, aggregation="volatility", unit="score", typical_range=(0, 10)),
]

def validate_feature_vector(fv: FeatureVector) -> List[str]:
    """Validate a feature vector. Returns list of warnings (not errors)."""
    warnings = []
    for spec in FEATURE_SPECS:
        if spec.name in fv.features:
            val = fv.features[spec.name]
            lo, hi = spec.typical_range
            if val < lo or val > hi:
                warnings.append(f"{spec.name}={val:.2f} outside typical range [{lo},{hi}]")
    return warnings

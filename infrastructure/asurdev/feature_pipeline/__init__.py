"""
Feature Pipeline — time-series feature extraction for ML-ready datasets.

Architecture:
    state_store (Postgres/job_events) → window_engine (sliding aggregation)
    → feature_registry (declarative definitions) → builder (computation engine)
    → exporter (train/val/test split) → embedding_layer (node vectors)

Modules:
    window_engine   — sliding windows core (1m/5m/15m/1h)
    feature_registry — declarative, versioned feature specs
    schemas          — typed feature schemas + validation
    builder          — computation engine (registry → feature vectors)
    exporter         — dataset builder (CSV/JSON/Parquet export)
    embedding         — node embedding vectors
    pipeline         — CLI entrypoint
"""
from .window_engine import WindowEngine, SlidingWindow, DEFAULT_WINDOWS
from .feature_registry import FEATURE_REGISTRY, get_feature_names, validate_registry
from .schemas import (
    FeatureVector, LabeledExample, FeatureSpec,
    NodeProfile, MLBatch, NodeRole, JobType, LabelType,
    validate_feature_vector,
)
from .builder import FeatureBuilder, build_features
from .exporter import DatasetExporter

__all__ = [
    # Core
    "WindowEngine", "SlidingWindow", "DEFAULT_WINDOWS",
    "FEATURE_REGISTRY", "get_feature_names", "validate_registry",
    "FeatureBuilder", "build_features",
    # Schemas
    "FeatureVector", "LabeledExample", "FeatureSpec",
    "NodeProfile", "MLBatch", "NodeRole", "JobType", "LabelType",
    "validate_feature_vector",
    # Export
    "DatasetExporter",
]
__version__ = "1.0.0"

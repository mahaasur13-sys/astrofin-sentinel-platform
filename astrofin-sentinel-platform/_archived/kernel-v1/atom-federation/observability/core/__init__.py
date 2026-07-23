"""
Observability Core v7.0.

Dependencies (install before use):
  pip install prometheus_client opentelemetry-api opentelemetry-sdk

Modules:
  metrics_schema  — canonical metric definitions + validation
  event_schema   — structured event model for replay
  atom_metrics   — Prometheus-compatible metrics emitter
  otel_instrumentation — OpenTelemetry setup + span helpers

Usage:
  from observability.core import (
      PrometheusMetrics,
      Event,
      EventType,
      OTelInstrumentation,
      METRICS_SCHEMA,
      get_mandatory_metrics,
  )
"""

from observability.core.atom_metrics import (
    NodeMetricsEmitter,
    PrometheusMetrics,
)
from observability.core.emitter import ObservabilityEmitter
from observability.core.event_schema import (
    CoherenceStateSnapshot,
    Event,
    EventType,
    LatticeSnapshot,
    QuorumSnapshot,
    SBSStateSnapshot,
    validate_payload,
)
from observability.core.metrics_schema import (
    METRICS_SCHEMA,
    get_mandatory_metrics,
    get_metric_def,
    validate_metric_labels,
)
from observability.core.otel_instrumentation import (
    OTelInstrumentation,
    create_span,
    event_to_span,
    get_global_otel,
    set_global_otel,
    traced,
)

__all__ = [
    # metrics_schema
    "METRICS_SCHEMA",
    "get_metric_def",
    "get_mandatory_metrics",
    "validate_metric_labels",
    # event_schema
    "Event",
    "EventType",
    "CoherenceStateSnapshot",
    "LatticeSnapshot",
    "QuorumSnapshot",
    "SBSStateSnapshot",
    "validate_payload",
    # atom_metrics
    "PrometheusMetrics",
    "NodeMetricsEmitter",
    # otel_instrumentation
    "OTelInstrumentation",
    "create_span",
    "traced",
    "event_to_span",
    "set_global_otel",
    "get_global_otel",
    # emitter
    "ObservabilityEmitter",
]

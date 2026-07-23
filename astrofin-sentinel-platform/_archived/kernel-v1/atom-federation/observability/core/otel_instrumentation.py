"""
OpenTelemetry Instrumentation v7.0.

Provides:
  - TracerProvider setup (OTLP exporter ready)
  - Automatic span instrumentation for gRPC, SBS, coherence, healer
  - Event → Span conversion (bridge event_schema → otel spans)
  - Metrics export via OTEL -> Prometheus (via prometheus_otlp)

This is the ONLY module that imports opentelemetry-api/sdk.
All other observability modules use event_schema + atom_metrics only.
"""

from __future__ import annotations

import threading
import time
from functools import wraps
from typing import Any

try:
    from opentelemetry import metrics, trace
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.semconv.resource import ResourceAttributes
    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False


TRACER_NAME = "atom-federation-os"
METRIC_METER_NAME = "atom-federation-os"


class OTelInstrumentation:
    """
    Central OpenTelemetry setup for ATOMFederationOS.

    Usage:
        otel = OTelInstrumentation(node_id="node-a", service_name="atom-node")
        otel.setup()  # call once at startup

        # Then in code:
        tracer = otel.tracer()
        with tracer.start_as_current_span("sbs_check") as span:
            span.set_attribute("atom.node_id", "node-a")
            span.set_attribute("atom.sbs.invariant", "boundary")

        # Emit metrics:
        meter = otel.meter()
        counter = meter.create_counter("atom_sbs_violations_total")
        counter.add(1, {"node_id": "node-a", "violation_type": "boundary"})
    """

    def __init__(
        self,
        node_id: str,
        service_name: str = "atom-node",
        otlp_endpoint: str | None = None,
    ):
        self.node_id = node_id
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self._lock = threading.Lock()
        self._setup = False
        self._tracer: Any | None = None
        self._meter: Any | None = None

    def setup(self) -> None:
        """Initialize OTel providers. Idempotent."""
        if not _HAS_OTEL:
            raise ImportError(
                "OpenTelemetry not installed. Run: pip install opentelemetry-api "
                "opentelemetry-sdk opentelemetry-exporter-otlp"
            )

        with self._lock:
            if self._setup:
                return

            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: self.service_name,
                ResourceAttributes.SERVICE_VERSION: "7.0",
                ResourceAttributes.HOST_NAME: self.node_id,
            })

            tracer_provider = TracerProvider(resource=resource)
            meter_provider = MeterProvider(resource=resource)

            if self.otlp_endpoint:
                try:
                    from opentelemetry.exporter.otlp.proto.grpc.trace import OTLPSpanExporter
                    span_exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
                    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
                except ImportError:
                    pass

            trace.set_tracer_provider(tracer_provider)
            metrics.set_meter_provider(meter_provider)

            self._tracer = trace.get_tracer(TRACER_NAME, "7.0")
            self._meter = metrics.get_meter(METRIC_METER_NAME, "7.0")
            self._setup = True

    def tracer(self) -> Any:
        if not self._setup:
            self.setup()
        return self._tracer

    def meter(self) -> Any:
        if not self._setup:
            self.setup()
        return self._meter


# ── Context variable for global OTel instance ──────────────────────────────────

_global_otel: threading.local = threading.local()


def set_global_otel(instrumentation: OTelInstrumentation) -> None:
    _global_otel.instrumentation = instrumentation


def get_global_otel() -> OTelInstrumentation | None:
    """Get the current thread-local OTelInstrumentation instance."""
    return getattr(_global_otel, "instrumentation", None)


def get_tracer() -> Any:
    """
    Get the current tracer from the global OTelInstrumentation.
    Returns None if OTel is not set up.
    """
    otel = get_global_otel()
    if otel is None:
        return None
    try:
        return otel.tracer()
    except Exception:
        return None


# ── Decorator-based instrumentation ─────────────────────────────────────────────


def traced(
    subsystem: str,
    span_name: str | None = None,
    attributes: dict | None = None,
):
    """
    Decorator to automatically instrument a function as a span.

    Usage:
        @traced("sbs", span_name="check_invariants")
        def check_invariants(node_state):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            otel = get_global_otel()
            if otel is None:
                return func(*args, **kwargs)

            tracer = otel.tracer()
            name = span_name or func.__name__
            span = tracer.start_span(name)
            with span:
                attrs = dict(attributes or {})
                attrs["atom.subsystem"] = subsystem
                for k, v in attrs.items():
                    span.set_attribute(k, v)
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


# ── Event → Span converter ──────────────────────────────────────────────────────


def event_to_span(tracer: Any, event: Any, parent_span: Any | None = None) -> Any:
    """
    Convert an Event (event_schema) to an OTel Span.

    The span carries:
      - event_type as span name
      - event.ts as span start time
      - All payload fields as attributes
      - Subsystem snapshots as attribute annotations
    """
    span_name = f"event.{event.event_type}"
    start_time_s = event.ts / 1e9

    span = tracer.start_span(
        span_name,
        start_time=start_time_s,
    )

    span.set_attribute("atom.event_id", event.event_id)
    span.set_attribute("atom.node_id", event.node_id)
    span.set_attribute("atom.event_type", event.event_type)
    span.set_attribute("atom.version", event.version)

    for key, value in event.payload.items():
        span.set_attribute(f"atom.payload.{key}", str(value) if value is not None else "")

    if event.coherence_state:
        cs = event.coherence_state
        span.set_attribute("atom.coherence.drift_score", cs.drift_score)
        span.set_attribute("atom.coherence.self_model_errors", cs.self_model_errors)

    if event.lattice_snapshot:
        ls = event.lattice_snapshot
        span.set_attribute("atom.lattice.active_nodes", len(ls.active_nodes))
        span.set_attribute("atom.lattice.split_brain", ls.split_brain_detected)

    if event.quorum_snapshot:
        qs = event.quorum_snapshot
        span.set_attribute("atom.quorum.members", len(qs.members))
        span.set_attribute("atom.quorum.health", qs.quorum_health)
        span.set_attribute("atom.quorum.leader", qs.leader or "")

    return span


# ── Standalone span helper ──────────────────────────────────────────────────────


def create_span(
    tracer: Any,
    name: str,
    attributes: dict | None = None,
) -> Any:
    """
    Create a span with ATOM-standard attributes.

    Standard attributes always added:
      - atom.node_id
      - atom.ts (span start time)
    """
    if attributes is None:
        attributes = {}

    span = tracer.start_span(name)
    span.set_attribute("atom.node_id", attributes.get("node_id", ""))
    span.set_attribute("atom.ts", time.time())

    for key, value in attributes.items():
        if key != "node_id" and value:
            span.set_attribute(key, value)

    return span

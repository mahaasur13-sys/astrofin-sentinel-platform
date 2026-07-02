"""
OTEL Exporter v7.0 — OTLP trace (and optionally metrics) export.

Sets up:
  - TracerProvider with OTLP/gRPC span exporter
  - Metrics export (optional, via MeterProvider + OTLP)

No cycle: this module imports OTelInstrumentation only via the
get_tracer() helper (which returns None if not yet bootstrapped).

Usage:
    from observability.core.otel_exporter import setup_otel_exporter
    tracer = setup_otel_exporter(
        endpoint="http://localhost:4317",   # OTEL collector gRPC
        service_name="atom-node-a",
        node_id="atom-node-a",
    )
"""

from __future__ import annotations

import threading
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


# Lock to make setup idempotent and thread-safe
_setup_lock = threading.Lock()
_setup_done: bool = False


def setup_otel_exporter(
    endpoint: str = "http://localhost:4317",
    service_name: str = "atom-node",
    node_id: str = "unknown",
    insecure: bool = True,
) -> Any | None:
    """
    Configure the global TracerProvider + MeterProvider with OTLP export.

    Idempotent: calling twice is safe (second call returns the existing tracer).

    Args:
        endpoint:     OTLP collector gRPC endpoint (default localhost:4317)
                      Docker/K8s:  http://otel-collector:4317
                      Local dev:   http://localhost:4317
        service_name: value for service.name resource attribute
        node_id:      value for host.name resource attribute
        insecure:     True = use gRPC insecure channel (no TLS)

    Returns:
        The current tracer (or None if OTel libs not installed / setup failed).
    """
    global _setup_done

    if not _HAS_OTEL:
        print("[otel] opentelemetry not installed — tracing disabled")
        return None

    tracer: Any | None = None

    with _setup_lock:
        if _setup_done:
            # Already set up; just return the current tracer
            try:
                return trace.get_tracer("atom-federation-os")
            except Exception:
                return None

        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: "7.0",
            ResourceAttributes.HOST_NAME: node_id,
        })

        tracer_provider = TracerProvider(resource=resource)
        meter_provider = MeterProvider(resource=resource)

        # Add OTLP span exporter (gRPC)
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace import OTLPSpanExporter

            exporter: Any = OTLPSpanExporter(
                endpoint=endpoint,
                insecure=insecure,
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        except ImportError:
            print(f"[otel] OTLPSpanExporter not available — traces will not be exported to {endpoint}")
        except Exception as exc:
            print(f"[otel] Failed to configure OTLP exporter ({endpoint}): {exc}")

        trace.set_tracer_provider(tracer_provider)
        metrics.set_meter_provider(meter_provider)

        tracer = trace.get_tracer("atom-federation-os", "7.0")
        _setup_done = True
        print(f"[otel] configured — exporting traces to {endpoint}")

    return tracer


def is_otel_setup() -> bool:
    """Return True if setup_otel_exporter() has been called successfully."""
    return _setup_done


def reset_otel() -> None:
    """Reset OTel state (for tests only)."""
    global _setup_done
    with _setup_lock:
        _setup_done = False

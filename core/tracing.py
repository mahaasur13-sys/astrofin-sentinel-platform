"""
OpenTelemetry initialisation with OTLP gRPC export to Jaeger.

Configuration is sourced from :class:`core.settings.Settings`:

* ``OTEL_EXPORTER_OTLP_ENDPOINT`` — gRPC collector endpoint (default
  ``http://localhost:4317``).
* ``OTEL_SERVICE_NAME`` — service name attribute on spans (default
  ``astrofin-sentinel``).
* ``OTEL_ENABLED`` — when ``false`` the function is a no-op (useful for
  unit tests that do not need a collector running).

aiohttp auto-instrumentation is attempted when the optional package
``opentelemetry-instrumentation-aiohttp`` is installed.
"""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from core.settings import get_settings

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str | None = None) -> trace.Tracer:
    settings = get_settings()
    if not settings.OTEL_ENABLED:
        logger.debug("tracing.disabled (OTEL_ENABLED=false)")
        return trace.get_tracer(__name__)

    name = service_name or settings.OTEL_SERVICE_NAME
    resource = Resource(attributes={SERVICE_NAME: name})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=True,
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Optional aiohttp auto-instrumentation.
    try:
        from opentelemetry.instrumentation.aiohttp import AioHttpInstrumentor

        AioHttpInstrumentor().instrument()
        logger.info("tracing.aiohttp_instrumentation_enabled")
    except ImportError:
        logger.warning("tracing.aiohttp_instrumentation_unavailable")

    return trace.get_tracer(__name__)


# Global tracer used across the platform. Initialised lazily so that
# tests that disable tracing (OTEL_ENABLED=false) do not spin up a
# background exporter thread.
tracer: trace.Tracer = trace.get_tracer(__name__)


def _ensure_tracer_initialised() -> None:
    """Replace the module-level ``tracer`` with a configured one if not already done."""
    global tracer
    if getattr(tracer, "_astrofin_configured", False):
        return
    new_tracer = setup_tracing()
    # Mark the configured tracer so we don't keep re-creating providers.
    setattr(new_tracer, "_astrofin_configured", True)
    tracer = new_tracer

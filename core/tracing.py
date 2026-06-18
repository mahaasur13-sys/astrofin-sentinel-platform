"""
Инициализация OpenTelemetry с экспортом в Jaeger (OTLP gRPC).
Добавлено автоматическое инструментирование aiohttp, если пакет установлен.
"""
from __future__ import annotations

import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str = "astrofin-sentinel") -> trace.Tracer:
    resource = Resource(attributes={SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Попытка автоматически инструментировать aiohttp (если пакет есть)
    try:
        from opentelemetry.instrumentation.aiohttp import AioHttpInstrumentor

        AioHttpInstrumentor().instrument()
        logger.info("tracing.aiohttp_instrumentation_enabled")
    except ImportError:
        logger.warning("tracing.aiohttp_instrumentation_unavailable")

    return trace.get_tracer(__name__)


# Глобальный tracer для использования в других модулях
tracer = setup_tracing()

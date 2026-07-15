"""
Observability Bootstrap v7.0.

Wires together the three export layers:
  1. Prometheus  /metrics  (HTTP server on :9464)
  2. OTLP trace export     (gRPC → OTEL collector)
  3. In-memory   prom_metrics singleton (used by ReplayObservabilitySubscriber)

Minimal one-shot startup for a cluster node or test harness.

Usage:
    from observability.bootstrap import start_observability

    tracer = start_observability(
        node_id="atom-node-a",
        metrics_port=9464,
        otel_endpoint="http://localhost:4317",
    )
    # tracer == None if OTel not available
    # /metrics server runs in background daemon thread
"""

from __future__ import annotations

import threading
from typing import Any

from observability.core.atom_metrics import prom_metrics
from observability.core.otel_exporter import setup_otel_exporter


def start_observability(
    node_id: str = "unknown",
    metrics_port: int = 9464,
    metrics_host: str = "0.0.0.0",
    otel_endpoint: str = "http://localhost:4317",
    otel_insecure: bool = True,
) -> Any | None:
    """
    Start all observability export channels.

    Idempotent: safe to call more than once.

    Args:
        node_id:       host.name attribute for OTEL resource
        metrics_port:  Prometheus scrape port (default 9464)
        metrics_host:  Prometheus bind address (default 0.0.0.0)
        otel_endpoint: OTLP collector gRPC endpoint
        otel_insecure: use insecure gRPC channel (no TLS)

    Returns:
        The configured tracer (or None if OTel not available).
    """
    # ── 1. Prometheus /metrics HTTP server ─────────────────────────────────
    from observability.server.metrics_server import start_metrics_server

    server = start_metrics_server(host=metrics_host, port=metrics_port, emitter=prom_metrics)

    t = threading.Thread(target=server.serve_forever, daemon=True, name="prom-metrics")
    t.start()

    # ── 2. OTLP exporter ───────────────────────────────────────────────────
    tracer = setup_otel_exporter(
        endpoint=otel_endpoint,
        service_name=f"atom-{node_id}",
        node_id=node_id,
        insecure=otel_insecure,
    )

    print(f"[observability] bootstrap complete — node={node_id} metrics=:~/{metrics_port} otel=~/{otel_endpoint}")

    return tracer

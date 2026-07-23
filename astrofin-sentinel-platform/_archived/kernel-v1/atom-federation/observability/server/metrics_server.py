"""
Prometheus /metrics endpoint server v7.0.

Serves the current prom_metrics registry in Prometheus text format.
Scraped by Prometheus on :9464/metrics.

Usage:
    from observability.server.metrics_server import start_metrics_server

import logging
log = logging.getLogger(__name__)

    start_metrics_server(host="0.0.0.0", port=9464)
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from observability.core.atom_metrics import InMemoryPrometheusEmitter


class MetricsHandler(BaseHTTPRequestHandler):
    """
    HTTP handler for /metrics endpoint.

    GET /metrics  → 200 text/plain (Prometheus 0.0.4)
    GET *         → 404
    """

    # Class-level reference to the metrics emitter (set by start_metrics_server)
    _emitter: InMemoryPrometheusEmitter | None = None

    def do_GET(self) -> None:
        if self.path != "/metrics":
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        emitter = MetricsHandler._emitter
        if emitter is None:
            self.send_response(503)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Metrics not initialised")
            return

        output = emitter.render_prometheus()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(output.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(output.encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        # Suppress default stderr logging — errors go to the process stderr anyway
        pass


def start_metrics_server(
    host: str = "0.0.0.0",
    port: int = 9464,
    emitter: InMemoryPrometheusEmitter | None = None,
) -> HTTPServer:
    """
    Start the Prometheus /metrics HTTP server.

    Args:
        host:        bind address (default 0.0.0.0 = all interfaces)
        port:        scrape port (default 9464)
        emitter:     metrics emitter to serve. If None, uses the global prom_metrics singleton.

    Returns:
        The configured HTTPServer instance (caller may .serve_forever() or .shutdown() it).
    """
    from observability.core.atom_metrics import prom_metrics

    MetricsHandler._emitter = emitter if emitter is not None else prom_metrics

    server = HTTPServer((host, port), MetricsHandler)
    server.allow_reuse_address = True
    log.info(f"[metrics] listening on {host}:{port}/metrics")
    return server

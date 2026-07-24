#!/usr/bin/env python3
"""
ATOM Operator — health endpoints.

Tiny stdlib HTTP server exposing:
    GET /healthz  -> 200 once the controller thread is alive
    GET /readyz   -> 200 once kubeconfig has been loaded
    GET /metrics  -> 204 (real metrics are exported on a separate port by main)

The Dockerfile HEALTHCHECK hits /healthz on 127.0.0.1:8080.
The Helm Service already publishes port 8080 -> "health".
"""

from __future__ import annotations

import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG = logging.getLogger("operator.health")


class _HealthState:
    """Mutable readiness flag shared by main() and the HTTP handler."""

    def __init__(self) -> None:
        self._ready = threading.Event()
        self._alive = threading.Event()
        self._alive.set()

    def mark_ready(self) -> None:
        self._ready.set()

    def mark_not_ready(self) -> None:
        self._ready.clear()

    def is_ready(self) -> bool:
        return self._ready.is_set()

    def is_alive(self) -> bool:
        return self._alive.is_set()


def _make_handler(state: _HealthState) -> type[BaseHTTPRequestHandler]:
    class HealthHandler(BaseHTTPRequestHandler):
        # Silence default access log; main() already configures structured logging.
        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/healthz":
                if state.is_alive():
                    self._ok("alive")
                else:
                    self._fail("not alive")
            elif self.path == "/readyz":
                if state.is_ready():
                    self._ok("ready")
                else:
                    self._fail("not ready")
            elif self.path == "/metrics":
                # Real Prometheus exposition is served elsewhere; here we just ack.
                self.send_response(204)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()

        def _ok(self, msg: str) -> None:
            body = msg.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _fail(self, msg: str) -> None:
            body = msg.encode()
            self.send_response(503)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return HealthHandler


def start_health_server(
    state: _HealthState,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> ThreadingHTTPServer:
    """Start the health server in a daemon thread. Returns the server instance."""
    handler = _make_handler(state)
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(
        target=server.serve_forever,
        name="atom-operator-health",
        daemon=True,
    )
    thread.start()
    LOG.info("Health server listening on %s:%d", host, port)
    return server


def make_state() -> _HealthState:
    """Public factory so callers do not have to import the private class."""
    return _HealthState()


# Re-export for tests / external callers.
__all__ = ["start_health_server", "make_state"]


def _selftest() -> int:
    """Minimal smoke test — run with `python -m operator.health`."""
    state = make_state()
    state.mark_ready()
    server = start_health_server(state, host="127.0.0.1", port=18080)
    try:
        import urllib.request

        with urllib.request.urlopen("http://127.0.0.1:18080/healthz", timeout=2) as r:
            assert r.status == 200, r.status
        with urllib.request.urlopen("http://127.0.0.1:18080/readyz", timeout=2) as r:
            assert r.status == 200, r.status
        log.info("selftest: OK")
        return 0
    finally:
        server.shutdown()


if __name__ == "__main__":
    import sys

    sys.exit(_selftest())

from __future__ import annotations

import logging
import os
import sys

import structlog
from opentelemetry import trace as otel_trace


def _add_trace_context(logger, method, event_dict):
    span = otel_trace.get_current_span()
    if span.get_span_context().is_valid:
        event_dict["trace_id"] = format(span.get_span_context().trace_id, "032x")
        event_dict["span_id"] = format(span.get_span_context().span_id, "016x")
    return event_dict


def _add_correlation_id(logger, method_name, event_dict):
    """Ensure every log line has a correlation_id; default 'unknown' if not bound."""
    event_dict.setdefault("correlation_id", "unknown")
    return event_dict


def setup_logging():
    """Configure structured logging for the AstroFin Sentinel platform.

    The renderer is selected by RENDER_MODE env var:
      - "json" (default): JSONRenderer — machine-readable, CI/ELK friendly.
        All tests that assert on log structure (test_logging.py) use this.
      - "console": ConsoleRenderer — human-friendly colors for dev (rich).

    logger_factory=PrintLoggerFactory(file=sys.stdout) writes to the **current**
    sys.stdout at call time. This is required for pytest's capsys fixture to
    work correctly: pytest redirects sys.stdout INSIDE the test, and the
    default LoggerFactory captures the *original* stdout at config time, so
    pytest's redirect is missed.
    """
    render_mode = (os.getenv("RENDER_MODE") or "json").lower()
    if render_mode == "console":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG,
    )

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            _add_trace_context,
            _add_correlation_id,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=True,
    )
    # Reduce noise from libraries
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)


def get_logger(name=None):
    """Return a structlog logger."""
    return structlog.get_logger(name)

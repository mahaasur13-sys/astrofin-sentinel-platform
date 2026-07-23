import logging
import sys
import uuid
from contextvars import ContextVar

import structlog
from opentelemetry import trace as otel_trace

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="unknown")


def set_correlation_id(value: str | None = None) -> str:
    """Set correlation id for current async context. Returns effective value."""
    value = value or str(uuid.uuid4())
    _correlation_id.set(value)
    return value


def new_correlation_id(prefix: str | None = None) -> str:
    """Generate a new correlation id, optionally prefixed."""
    body = str(uuid.uuid4())[:8]
    return f"{prefix}-{body}" if prefix else body


def get_correlation_id() -> str:
    return _correlation_id.get()


def _add_trace_context(logger, method, event_dict):
    span = otel_trace.get_current_span()
    if span.get_span_context().is_valid:
        event_dict["trace_id"] = format(span.get_span_context().trace_id, "032x")
        event_dict["span_id"] = format(span.get_span_context().span_id, "016x")
    return event_dict


def _add_correlation_id(logger, method, event_dict):
    event_dict["correlation_id"] = _correlation_id.get()
    return event_dict


def setup_logging():
    """Configure structured JSON logging to stdout (works with pytest capfd)."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_correlation_id,
            _add_trace_context,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=False,
    )

    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name=None):
    return structlog.get_logger(name)

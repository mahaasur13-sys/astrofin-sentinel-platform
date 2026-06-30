import logging
import sys

import structlog
from opentelemetry import trace as otel_trace


def _add_trace_context(logger, method, event_dict):
    span = otel_trace.get_current_span()
    if span.get_span_context().is_valid:
        event_dict["trace_id"] = format(span.get_span_context().trace_id, "032x")
        event_dict["span_id"] = format(span.get_span_context().span_id, "016x")
    return event_dict


def setup_logging():
    # Настраиваем стандартный логгер для вывода в stdout
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            _add_trace_context,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    # Уменьшаем шум от библиотек
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)


def get_logger(name=None):
    """Возвращает логгер structlog."""
    return structlog.get_logger(name)

"""Structured-logging bootstrap.

Same logger-name pattern as push/core/logging.py.
Stdlib only - no structlog/opentelemetry dep.

Use:
    from logging_setup import setup_logging, get_logger
    setup_logging(level="INFO")
    log = get_logger(__name__)
    log.info("event_name", key=value)
"""

from __future__ import annotations

import logging
import os
import sys
from logging import Logger
from typing import Literal

Level = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(level: Level | None = None) -> None:
    """Configure root logger with a single-line structured-friendly format.

    Idempotent: safe to call multiple times.
    """
    resolved = level or os.environ.get("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    # Avoid duplicating handlers on repeated calls (tests, reloads).
    if getattr(root, "_logging_setup_done", False):
        root.setLevel(resolved)
        return
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)sZ level=%(levelname)s logger=%(name)s msg=%(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(resolved)
    # Quiet noisy libraries.
    for noisy in ("urllib3", "asyncio", "docker", "kubernetes"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    root._logging_setup_done = True  # type: ignore[attr-defined]


def get_logger(name: str | None = None) -> Logger:
    """Return stdlib logger named after `name` (or root when None)."""
    return logging.getLogger(name or "app")


__all__ = ["setup_logging", "get_logger"]

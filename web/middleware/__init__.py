"""web.middleware — request middleware: correlation id + error envelope."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, Response, g, jsonify, request
from werkzeug.exceptions import HTTPException

from core.error_schema import (
    AppException,
    InternalError,
    format_error,
    set_correlation_id,
)
from core.logging import get_logger

_log = get_logger(__name__)

_CORRELATION_HEADER = "X-Correlation-ID"


def _status_to_code(status: int) -> str:
    if status == 400:
        return "BAD_REQUEST"
    if status == 401:
        return "UNAUTHORIZED"
    if status == 403:
        return "FORBIDDEN"
    if status == 404:
        return "NOT_FOUND"
    if status == 409:
        return "CONFLICT"
    if status == 422:
        return "UNPROCESSABLE_ENTITY"
    if status == 429:
        return "RATE_LIMITED"
    if 500 <= status:
        return "INTERNAL_ERROR"
    return "ERROR"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def install_flask(app: Flask) -> None:
    """Attach correlation-id + JSON-error handling to a Flask app."""

    @app.before_request
    def _bind_correlation_id() -> None:
        cid = request.headers.get(_CORRELATION_HEADER) or uuid.uuid4().hex
        set_correlation_id(cid)
        g.correlation_id = cid
        g.request_started = time.time()

    @app.after_request
    def _normalise_errors(response: Response) -> Response:
        cid = getattr(g, "correlation_id", None) or "unknown"
        response.headers.setdefault(_CORRELATION_HEADER, cid)

        if 400 <= response.status_code < 600:
            status = response.status_code
            ct = response.headers.get("Content-Type", "")
            if "application/json" not in ct:
                try:
                    raw = response.get_data(as_text=True) or ""
                    if raw.startswith("{"):
                        legacy = json.loads(raw)
                    else:
                        legacy = {"message": raw or "error"}
                except Exception:  # pragma: no cover — defensive  # noqa: BLE001
                    legacy = {"message": "error"}

                msg = legacy.get("error") or legacy.get("message") or "error"
                code = _status_to_code(status)
                envelope = {
                    "code": code,
                    "message": str(msg),
                    "trace_id": legacy.get("trace_id") or "unknown",
                    "correlation_id": cid,
                    "timestamp": _utcnow_iso(),
                    "status": status,
                    "details": {k: v for k, v in legacy.items() if k not in {"error", "message", "trace_id", "status"}},
                }
                response = jsonify(envelope)
            else:
                try:
                    data = response.get_json()
                except Exception:  # noqa: BLE001
                    data = None
                if isinstance(data, dict):
                    data.setdefault("correlation_id", cid)
                    data.setdefault("code", _status_to_code(status))
                    data.setdefault("status", status)
                    data.setdefault("trace_id", data.get("trace_id") or "unknown")
                    if "timestamp" not in data:
                        data["timestamp"] = _utcnow_iso()
                    response = jsonify(data)

            response.status_code = status
            response.headers.setdefault(_CORRELATION_HEADER, cid)

        _log.info(
            "http_request",
            method=request.method,
            path=request.path,
            status=response.status_code,
            correlation_id=cid,
        )
        return response

    @app.errorhandler(AppException)
    def _handle_app_exception(exc: AppException) -> Response:
        envelope = format_error(exc, correlation_id=getattr(g, "correlation_id", None))
        _log.warning(
            "app_exception",
            code=exc.code,
            status=exc.status,
            message=exc.message,
            correlation_id=envelope["correlation_id"],
        )
        response = jsonify(envelope)
        response.status_code = exc.status
        return response

    @app.errorhandler(HTTPException)
    def _handle_http_exception(exc: HTTPException) -> Response:
        """werkzeug HTTPException (404, 405, 500 internal) → JSON envelope."""
        cid = getattr(g, "correlation_id", None) or "unknown"
        envelope = {
            "code": _status_to_code(exc.code or 500),
            "message": exc.description or exc.name or "error",
            "trace_id": "unknown",
            "correlation_id": cid,
            "timestamp": _utcnow_iso(),
            "status": exc.code or 500,
            "details": {"path": request.path, "method": request.method},
        }
        _log.warning(
            "http_exception",
            code=envelope["code"],
            status=envelope["status"],
            message=envelope["message"],
            correlation_id=cid,
        )
        response = jsonify(envelope)
        response.status_code = exc.code or 500
        return response

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception) -> Response:
        envelope = format_error(exc, correlation_id=getattr(g, "correlation_id", None))
        _log.error(
            "unhandled_exception",
            exception=type(exc).__name__,
            message=str(exc),
            correlation_id=envelope["correlation_id"],
        )
        envelope["message"] = InternalError.message
        response = jsonify(envelope)
        response.status_code = 500
        return response


__all__ = ["install_flask", "install_error_handling"]

# Public alias — canonical name referenced from web/app.py / docs.
install_error_handling = install_flask

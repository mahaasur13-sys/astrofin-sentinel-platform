"""Schema-level tests for core.error_schema (no Flask, no network).

These tests validate the *envelope* contract:

  { "code", "message", "trace_id", "correlation_id", "timestamp", "status", "details" }

The HTTP-level integration is covered by ``test_error_handling_wsgi.py``
which uses the Flask test client and the wsgi ``server`` defined in
``web/wsgi.py``.
"""

from __future__ import annotations

import re

import pytest

from core.error_schema import (
    AppException,
    BadRequest,
    Conflict,
    Forbidden,
    InternalError,
    NotFound,
    Unauthorized,
    ValidationFailed,
    format_error,
    get_correlation_id,
    set_correlation_id,
)


def _envelope_keys() -> set[str]:
    return {
        "code",
        "message",
        "trace_id",
        "correlation_id",
        "timestamp",
        "status",
        "details",
    }


@pytest.fixture(autouse=True)
def _reset_correlation_id():
    """Reset the ContextVar before and after each test."""
    from core.error_schema import _correlation_id_var

    token = _correlation_id_var.set("unknown")
    try:
        yield
    finally:
        _correlation_id_var.reset(token)


class TestSchemaShape:
    def test_format_error_has_all_required_fields(self):
        e = BadRequest("bad x", details={"field": "symbol"})
        env = format_error(e)
        assert _envelope_keys().issubset(env.keys())

    def test_status_codes_match_typed_subclass(self):
        assert format_error(BadRequest("x"))["status"] == 400
        assert format_error(Unauthorized("x"))["status"] == 401
        assert format_error(Forbidden("x"))["status"] == 403
        assert format_error(NotFound("x"))["status"] == 404
        assert format_error(Conflict("x"))["status"] == 409
        assert format_error(ValidationFailed("x"))["status"] == 422
        assert format_error(InternalError("x"))["status"] == 500

    def test_code_is_stable_string(self):
        assert BadRequest("x").code == "BAD_REQUEST"
        assert Unauthorized("x").code == "UNAUTHORIZED"
        assert Forbidden("x").code == "FORBIDDEN"
        assert NotFound("x").code == "NOT_FOUND"
        assert Conflict("x").code == "CONFLICT"
        assert ValidationFailed("x").code == "VALIDATION_FAILED"
        assert InternalError("x").code == "INTERNAL_ERROR"

    def test_timestamp_is_iso_utc(self):
        env = format_error(BadRequest("x"))
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", env["timestamp"])

    def test_details_default_to_empty_dict(self):
        env = format_error(BadRequest("x"))
        assert env["details"] == {}

    def test_details_passed_through(self):
        e = BadRequest("bad", details={"field": "x", "expected": "int"})
        assert format_error(e)["details"] == {"field": "x", "expected": "int"}


class TestCorrelationId:
    def test_default_correlation_id_is_unknown(self):
        assert get_correlation_id() == "unknown"
        env = format_error(BadRequest("x"))
        assert env["correlation_id"] == "unknown"

    def test_explicit_correlation_id_propagates(self):
        set_correlation_id("abc-123")
        env = format_error(BadRequest("x"))
        assert env["correlation_id"] == "abc-123"

    def test_set_correlation_id_none_generates_uuid(self):
        cid = set_correlation_id(None)
        assert re.match(r"^[a-f0-9]{32}$", cid)
        assert get_correlation_id() == cid

    def test_set_correlation_id_produces_unique_ids(self):
        ids = {set_correlation_id(None) for _ in range(100)}
        assert len(ids) == 100


class TestErrorEnvelopesForStatusCodes:
    def test_400_bad_request(self):
        env = format_error(BadRequest("invalid input"))
        assert env["status"] == 400
        assert env["code"] == "BAD_REQUEST"

    def test_401_unauthorized(self):
        env = format_error(Unauthorized("invalid token"))
        assert env["status"] == 401
        assert env["code"] == "UNAUTHORIZED"

    def test_403_forbidden(self):
        env = format_error(Forbidden("insufficient role"))
        assert env["status"] == 403
        assert env["code"] == "FORBIDDEN"

    def test_404_not_found(self):
        env = format_error(NotFound("resource not found"))
        assert env["status"] == 404
        assert env["code"] == "NOT_FOUND"

    def test_500_internal_server_error(self):
        env = format_error(RuntimeError("boom"))
        assert env["status"] == 500
        assert env["code"] == "INTERNAL_ERROR"
        assert env["message"] != "boom"
        assert "exception" in env["details"]


class TestExceptionHierarchy:
    def test_all_subclasses_inherit_from_app_exception(self):
        for cls in (
            BadRequest,
            Unauthorized,
            Forbidden,
            NotFound,
            Conflict,
            ValidationFailed,
            InternalError,
        ):
            assert issubclass(cls, AppException)

    def test_app_exception_is_exception(self):
        assert issubclass(AppException, Exception)

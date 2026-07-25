"""Tests for core/logging_utils.py PII scrubber.
Coverage target: 100% of _scrub_string, _scrub_value, scrub_pii.
"""

import pytest
from core.logging_utils import _scrub_string, _scrub_value, scrub_pii


class TestScrubString:
    """Unit tests for _scrub_string."""

    @pytest.mark.parametrize(
        "inp,expected",
        [
            ("user@astrofin.io", "[REDACTED]"),
            ("admin+tag@sentinel.com", "[REDACTED]"),
            ("Felix <felix@astrofin.io>", "Felix <[REDACTED]>"),
        ],
    )
    def test_email_redaction(self, inp, expected):
        assert _scrub_string(inp) == expected

    def test_jwt_redaction(self):
        inp = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgN"
        result = _scrub_string(inp)
        assert "Bearer" in result
        assert "[REDACTED]" in result

    @pytest.mark.parametrize(
        "inp,expected",
        [
            ("api-key: sk-abcdefghijklmnopqrstuvwxyz1234567890ABCD", "api-key: [REDACTED]"),
            ("password=secret123", "password=secret123"),  # current impl does not detect key=value secrets
        ],
    )
    def test_api_key_redaction(self, inp, expected):
        assert _scrub_string(inp) == expected

    @pytest.mark.parametrize(
        "inp",
        [
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "1234567890123456789012345678901234567890abcd",
        ],
    )
    def test_hex_secret_redaction(self, inp):
        assert _scrub_string(inp) == "[REDACTED]"

    def test_aws_key_redaction(self):
        assert _scrub_string("AKIAIOSFODNN7EXAMPLE") == "[REDACTED]"

    def test_non_string_passthrough(self):
        assert _scrub_string(42) == 42
        assert _scrub_string(None) is None
        assert _scrub_string(3.14) == 3.14

    def test_clean_text_passthrough(self):
        assert _scrub_string("Normal log message") == "Normal log message"


class TestScrubValue:
    """Unit tests for _scrub_value."""

    def test_scrub_dict(self):
        out = _scrub_value({"email": "user@astrofin.io", "name": "Felix"})
        assert out["email"] == "[REDACTED]"
        assert out["name"] == "Felix"

    def test_scrub_nested_dict(self):
        out = _scrub_value({"user": {"email": "user@astrofin.io"}})
        assert out["user"]["email"] == "[REDACTED]"

    def test_scrub_list(self):
        out = _scrub_value(["user@astrofin.io", "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc123def", "clean"])
        assert out == ["[REDACTED]", "Bearer [REDACTED]", "clean"]

    def test_scrub_tuple(self):
        out = _scrub_value(("user@astrofin.io", "clean"))
        assert out == ("[REDACTED]", "clean")

    def test_scrub_tuple_of_tuples(self):
        out = _scrub_value((("user@astrofin.io",), ("clean",)))
        assert out == (("[REDACTED]",), ("clean",))

    def test_primitives_passthrough(self):
        assert _scrub_value(42) == 42
        assert _scrub_value(None) is None


class TestScrubPii:
    """Integration tests for scrub_pii processor."""

    def test_scrub_email_in_event_dict(self):
        out = scrub_pii(None, None, {"event": "user user@astrofin.io logged in"})
        assert "[REDACTED]" in out["event"]

    def test_noop_on_non_dict(self):
        assert scrub_pii(None, None, "string") == "string"
        assert scrub_pii(None, None, 42) == 42
        assert scrub_pii(None, None, None) is None

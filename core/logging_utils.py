"""Lightweight PII scrubber for structured logs.

Used as a structlog processor in `core/logging.py`. Scrubs obvious
secrets from log payloads so they do not end up in centralised log
storage (Loki/ELK) or in error reports (Sentry).

Scope is intentionally narrow: it targets high-confidence patterns
(emails, JWTs, bearer tokens, API keys, long hex secrets, AWS keys).
Anything that does not match is passed through untouched.

This is a defense-in-depth measure, not a substitute for not logging
secrets in the first place. Track coverage in `docs/slo.md` and
`SLO.md` (PII scrubber uptime is an internal quality gate).
"""
from __future__ import annotations

import re
from typing import Any, Mapping

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# JWT: three base64url segments separated by dots.
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b")
# Bearer / Token / Authorization header values.
_BEARER_RE = re.compile(r"(?i)(Bearer|Token|Authorization)\s+[A-Za-z0-9._\-]{8,}")
# 40+ char hex strings (typical API keys, hashes, secrets).
_HEX_SECRET_RE = re.compile(r"\b[0-9a-fA-F]{40,}\b")
# AWS access key id (AKIA / ASIA prefix, 16 chars from [A-Z0-9]).
_AWS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{12,}\b")
# Slack, GitHub, Stripe style "x"-prefixed API keys.
_PREFIXED_KEY_RE = re.compile(
    r"\b(?:"
    r"xox[bopasr]-[A-Za-z0-9-]{10,}"   # Slack
    r"|ghp_[A-Za-z0-9]{20,}"            # GitHub PAT
    r"|sk_(?:live|test)_[A-Za-z0-9]{16,}"  # Stripe live/test
    r"|sk-[A-Za-z0-9_-]{16,}"           # OpenAI / generic
    r"|AIza[A-Za-z0-9_-]{15,}"          # Google API key
    r")\b"
)

_REDACTED = "[REDACTED]"


def _scrub_string(value: str) -> str:
    """Apply all scrubbing patterns to a single string."""
    value = _EMAIL_RE.sub(_REDACTED, value)
    value = _JWT_RE.sub(_REDACTED, value)
    value = _BEARER_RE.sub(lambda m: f"{m.group(1)} {_REDACTED}", value)
    value = _AWS_KEY_RE.sub(_REDACTED, value)
    value = _PREFIXED_KEY_RE.sub(_REDACTED, value)
    value = _HEX_SECRET_RE.sub(_REDACTED, value)
    return value


def _scrub_value(value: Any) -> Any:
    """Recursively scrub strings inside dicts / lists / tuples.

    Non-string scalars (int, float, bool, None) are returned as-is.
    Bytes and other opaque types are returned as-is.
    """
    if isinstance(value, str):
        return _scrub_string(value)
    if isinstance(value, Mapping):
        return {k: _scrub_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        scrubbed = [_scrub_value(item) for item in value]
        return type(value)(scrubbed)
    return value


def scrub_pii(logger, method_name: str, event_dict: dict) -> dict:
    """Structlog processor: redact obvious PII / secrets in-place.

    Operates on the rendered event_dict so it runs after all upstream
    processors (including any key renames). Returns the modified
    dict so the next processor in the chain sees redacted values.
    """
    if not event_dict:
        return event_dict
    for key, value in list(event_dict.items()):
        event_dict[key] = _scrub_value(value)
    return event_dict

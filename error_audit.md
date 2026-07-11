# Error Handling Audit (ERR-01)

**Date:** 2026-07-09
**Scope:** `core/`, `web/`, `orchestration/`, `meta_rl/`, `knowledge/`
**Author:** ERR-01 sprint automation

## Summary

- **52 files** in core+meta_rl+web use `try/except`.
- **177 try-blocks** and **177 except-clauses** (parity → all catches re-raise or swallow).
- `core/logging.py` already configures **structlog** with `JSONRenderer` (`RENDER_MODE=json`).
  - Processors in place: `add_log_level`, `_add_trace_context` (OTel), `_add_correlation_id` (default `"unknown"`), `scrub_pii`, `TimeStamper(iso)`.
  - `get_logger(name)` returns a bound `structlog` logger.
- `core/auth_jwt.py` defines domain-specific exception hierarchy: `JWTError`, `RevokedError`, `TokenExpiredError`, `MissingKeyError`.
- `core/auth_refresh.py` defines `RefreshError`.
- `web/wsgi.py` returns ad-hoc `jsonify({"status": "ERROR", "error": "..."})` shapes — **not** following any project-wide schema.
- `web/app.py` uses Dash callbacks; no unified error envelope.
- **No `AppException` base class** for cross-module errors.
- **No `format_error(exc, request_id) -> dict`** helper.
- **No `correlation_id` middleware** that propagates request-scoped id into structlog context.
- **No HTTP error envelope** (`code`, `message`, `trace_id`, `timestamp`, `details`).

## Per-Module Findings

| Module                  | try/except | logging.error | Custom Exceptions                  | Standardised JSON Error |
|-------------------------|-----------:|--------------:|------------------------------------|-------------------------|
| `core/`                 |         47 |             9 | `JWTError`, `RevokedError`, `TokenExpiredError`, `MissingKeyError`, `RefreshError` | ✗ |
| `web/`                  |          9 |             2 | —                                  | ✗ (raw `jsonify({...,"error":...})`) |
| `orchestration/`        |         13 |             9 | —                                  | ✗ |
| `meta_rl/`              |         85 |             1 | —                                  | ✗ |
| `knowledge/`            |          3 |             0 | —                                  | ✗ |

## Gaps (priority order)

1. **No JSON error envelope** for HTTP endpoints.
2. **No correlation-id propagation** from request → logs.
3. **Inconsistent error shapes** between `web/wsgi.py`, `web/app.py`, and Dash callbacks.
4. **Domain exceptions are not subclassed from a common base** → can't be caught uniformly at the HTTP boundary.
5. **Tests don't assert on the standardised error shape** (no `test_error_responses.py`).
6. **No `docs/api_errors.md`** describing the contract.

## Target Architecture (introduced in this sprint)

```
core/error_schema.py     # AppException hierarchy + format_error() + error_response()
core/logging_config.py   # structlog config + correlation-id contextvar
core/middleware_flask.py # Flask before/after + error handler
core/middleware_fastapi.py # FastAPI middleware + exception handlers
core/auth_jwt.py         # now subclasses AppException
core/auth_refresh.py     # now subclasses AppException
web/wsgi.py              # route handlers use error_response(...)
tests/error_handling/    # contract tests for 400/401/403/404/500
docs/api_errors.md       # public contract
README.md                # + "Error Handling" section
```

Backwards-compatibility: existing `try/except` blocks are **kept**; new helpers
are *additive*. The Flask/FastAPI middleware is wired in `web/wsgi.py` and the
existing `app = dash.Dash(...)` builder; we do not change the public route set.

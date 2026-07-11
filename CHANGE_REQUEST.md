# CHANGE_REQUEST — KI-127 Quality Gate fixes

**Branch:** `feat/err-01-improve-error-handling`
**Author:** Felix (asurdev)
**Process:** ADD (Audit → Decide → Deliver)
**Iteration:** 0 — spec lock

## Goal

Bring `core/auth.py`, `web/wsgi.py`, `tests/auth/test_require_api_key_decorator.py`,
and the related `core/error_schema.py` contract into a single, consistent,
test-passing state so the Quality Gate (ruff format + 9 tests) is green.

## Scope (in)

- `core/auth.py`
- `web/wsgi.py`
- `tests/auth/test_require_api_key_decorator.py`
- `core/error_schema.py` (only the parts that shape the auth/error envelope)
- `tests/test_auth_empty_key.py`
- `tests/test_auth_flask_decorator.py`
- `tests/error_handling/test_error_handling_wsgi.py`
- `tests/conftest.py` (only if shared fixtures need updates)

## Scope (out)

- All other modules.

## Acceptance criteria

1. `ruff format --check` passes on the three named files.
2. `pytest tests/auth tests/test_auth_empty_key.py tests/test_auth_flask_decorator.py tests/error_handling` — all green.
3. Auth error envelope shape is **standardised**:
   ```json
   { "error": "Unauthorized" | "Forbidden", "timestamp": "...", "correlation_id": "..." }
   ```
4. Behavior matrix (matrix tests, not just smoke):
   | API_KEY env | API_KEY_AUTH_DISABLED | X-API-Key | Status | Body.error |
   |---|---|---|---|---|
   | empty | false (default) | any | 500 | InternalError envelope |
   | set | false | missing | 401 | `Unauthorized` |
   | set | false | wrong | 403 | `Forbidden` |
   | set | false | correct | 200 | route response |
   | any | true | any | 200 | route response |
5. `TestSchemaShape::test_timestamp_is_iso_utc` accepts **both** `...:13Z` and
   `...:13.758Z` (optional fractional seconds, max 6 digits).
6. `format_error` returns `(body: dict, status: int)` so both FastAPI and Flask
   can consume it.
7. `core.auth.API_KEY` and `core.auth.REQUIRE_AUTH` shims kept for
   backwards compatibility (read at import time), but auth decisions always
   re-read env at request time.

## Edge cases (explicit)

- API_KEY unset (no env var at all)
- API_KEY set to empty string
- API_KEY set to whitespace
- X-API-Key header missing
- X-API-Key header empty string
- X-API-Key with trailing whitespace (must NOT match — `compare_digest` handles this)
- `API_KEY_AUTH_DISABLED=true` / `1` / `yes` (case-insensitive)
- `API_KEY_AUTH_DISABLED` unset (default = auth enabled)
- Timestamp with milliseconds in error envelope (e.g. `2026-07-11T10:22:33.758Z`)

## Out-of-scope concerns (logged, not fixed here)

- The pre-existing uncommitted diff in `core/auth.py` already re-reads env
  per-request, but still uses the name `REQUIRE_AUTH`. Spec uses
  `API_KEY_AUTH_DISABLED` (inverted). We will rename in this change.
- `tests/auth/test_require_api_key_decorator.py` (uncommitted) currently
  asserts `body["code"]`. After this change it must assert `body["error"]`.

## Iteration plan

- **Iter 1:** ruff format on the three files; fix timestamp regex in
  `TestSchemaShape` to accept optional `\.\d{1,6}`.
- **Iter 2:** rename `REQUIRE_AUTH` → `API_KEY_AUTH_DISABLED` in
  `core/auth.py` (invert semantic), update every test that touches it.
- **Iter 3:** align `core/error_schema.format_error` envelope:
  `code` → `error`, keep `timestamp` + `correlation_id`.
- **Iter 4:** re-run ruff + pytest locally (in sandbox) to confirm green
  before push.

## Risks

- Renaming the env var is a behavior change for ops. Mitigation: keep
  `REQUIRE_AUTH` shim that maps `true` → `API_KEY_AUTH_DISABLED=false` and
  logs a deprecation warning.
- `format_error` signature change is a breaking API for any caller still
  expecting `{"code": ...}`. Mitigation: in this branch we are the only
  caller (search shows `web/wsgi.py`, `tests/*`, `core/auth.py`); no
  external consumers.

## Verification commands

```bash
ruff format --check core/auth.py web/wsgi.py tests/auth/test_require_api_key_decorator.py
pytest tests/auth tests/test_auth_empty_key.py tests/test_auth_flask_decorator.py tests/error_handling -v
```

# Change Request — Auth Decorator / Error Schema alignment

## Status
**Approved by user — Variant 1 (spec wins).** Drift acknowledged:
spec says `API_KEY_AUTH_DISABLED` + `{"error": ...}` payload; current
uncommitted code uses `REQUIRE_AUTH` + `{"code": ...}`. We align code
to spec, not the other way around.

## Target contract (source of truth)

- **Env var:** `API_KEY_AUTH_DISABLED` (string, truthy = `"true"|"1"|"yes"`)
  → auth disabled. Default: `false` (auth ON).
- **Error envelope** (returned by `core.error_schema.format_error` and
  used by the `require_api_key` decorator):
  ```json
  { "error": "Unauthorized" | "Forbidden" | "InternalError",
    "message": "...",
    "timestamp": "ISO-8601 UTC",
    "correlation_id": "uuid" }
  ```
- **Statuses:** `401` missing/invalid key · `403` disabled-by-policy ·
  `500` server misconfiguration (no `API_KEY` set).
- **No envelope when auth is disabled** — route handler runs as-is.

## Scope (in)

- `core/auth.py` — rename `REQUIRE_AUTH` → `API_KEY_AUTH_DISABLED` (invert
  semantics), return envelope via `format_error`, honor disabled mode.
- `core/error_schema.py` — ensure `format_error` returns
  `{"error", "message", "timestamp", "correlation_id"}` and a tuple
  `(body, status)`.
- `web/wsgi.py` — keep single `error_response` import and single
  `handle_known_errors` definition.
- `tests/auth/test_require_api_key_decorator.py` — assert new envelope
  shape, new env var, and `500` for missing `API_KEY`.
- Loosen `timestamp` regex to accept optional fractional seconds.
- Apply `ruff format` to the three files.

## Scope (out)

- Other modules and other tests. No refactor beyond the auth/error
  surface listed above.

## Iteration plan

1. **Iter 1 (now):** ruff format + timestamp regex + small envelope
   alignment. Push, watch Quality Gate + CI – Security and Quality.
2. **Iter 2 (next):** rename env var across `core/auth.py` and tests,
   flip disabled-mode semantics, verify 401/403/500 matrix.
3. **Iter 3:** close CodeRabbit threads, merge PR #176.

## Verification matrix (must pass after iter 2)

| Scenario                            | Status | Body.error       |
|-------------------------------------|--------|------------------|
| valid key                           | 200    | (handler output) |
| missing key                         | 401    | Unauthorized     |
| wrong key                           | 403    | Forbidden        |
| `API_KEY` unset                     | 500    | InternalError    |
| `API_KEY_AUTH_DISABLED=true`        | 200    | (handler output) |

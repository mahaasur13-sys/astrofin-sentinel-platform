# Error Handling

> **Status:** ✅ Implemented in `core/security_middleware.py::install_security_middleware`
> **Sprint:** Sprint 1 (issue #86)

## Contract

Every unhandled exception raised inside a Flask route is converted to a
JSON envelope. **No HTML stack trace, no Werkzeug debug page**, no leaked
secret.

```json
{
  "error": "internal server error",
  "request_id": "0193a1b2-...-uuid7"
}
```

* `error` — fixed, generic message. Never include the exception text.
* `request_id` — UUIDv7 minted in `install_request_id` and stashed in `flask.g`.
  Returned back in the `X-Request-Id` response header so operators can grep
  the logs by it.

## Logging

Each unhandled exception is logged **once** with the request_id and the
original exception (so the traceback is preserved for operators, not for
the client):

```python
flask_app.logger.exception("Unhandled error (request_id=%s): %s", rid, exc)
```

The level is `ERROR` (via `.exception`), so it shows up in any standard
Python logging config — the same place everything else is logged.

## What it does NOT do

* It does **not** swallow `HTTPException` subclasses — `werkzeug.exceptions.HTTPException`
  (404, 405, 415, etc.) is handled by the stock Flask `errorhandler(HTTPException)`
  upstream and returns a real HTTP response. Only the catch-all `Exception`
  path is overridden.
* It does **not** affect the Dash callback path. Dash callbacks run inside
  their own request context; a Dash exception is reported to the client
  over the websocket and shows up in the browser console, not via this
  handler. For Dash-specific errors, see `web/callbacks.py`.

## Testing

There is no dedicated test for the catch-all handler yet — it is exercised
indirectly by `pytest tests/test_*` when a route under test raises. To
verify manually:

```bash
curl -s -o - -w '\nHTTP %{http_code}\n' http://localhost:8050/__raise__
# {"error":"internal server error","request_id":"..."}
# HTTP 500
```

## See also

* `core/security_middleware.py` — implementation.
* `docs/SECURITY.md` — middleware stack and order.
* KI-012, KI-086.

---

## ERR-01: Standardised Error Envelope

> **Status:** ✅ Implemented in `core/error_schema.py` and `web/middleware/__init__.py`
> **Sprint:** ERR-01 (issue #173)
> **PR:** TBD — `feat/err-01-improve-error-handling`

### Schema

Every error response, including unhandled `Exception` and `HTTPException`,
is serialised to the same JSON envelope:

```json
{
  "code":           "BAD_REQUEST",
  "message":        "sid_a and sid_b required",
  "trace_id":       "0af7651916cd43dd8448eb211c80319c",
  "correlation_id": "cid-1",
  "timestamp":      "2026-07-09T07:36:44Z",
  "status":         400,
  "details":        { "field": "sid_a" }
}
```

* `code` — stable machine-readable string (e.g. `BAD_REQUEST`, `UNAUTHORIZED`).
* `message` — human-readable, safe to surface to operators.
* `trace_id` — OpenTelemetry trace id, or `unknown` if not active.
* `correlation_id` — request-scoped id, taken from the
  `X-Correlation-ID` request header or generated as a uuid4 hex.
* `timestamp` — ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).
* `status` — HTTP status code (mirrors the response status).
* `details` — structured context (validated, never contains the original
  stack trace or the raw exception text).

### Codes

| HTTP | `code`              | Class                      |
|-----:|---------------------|----------------------------|
| 400  | `BAD_REQUEST`       | `core.error_schema.BadRequest`     |
| 401  | `UNAUTHORIZED`      | `core.error_schema.Unauthorized`   |
| 403  | `FORBIDDEN`         | `core.error_schema.Forbidden`      |
| 404  | `NOT_FOUND`         | `core.error_schema.NotFound`       |
| 409  | `CONFLICT`          | `core.error_schema.Conflict`       |
| 422  | `VALIDATION_FAILED` | `core.error_schema.ValidationFailed`|
| 500  | `INTERNAL_ERROR`    | `core.error_schema.InternalError`  |

Any other exception (e.g. `RuntimeError`) is mapped to a 500 envelope
with the original `exception` class name in `details`, but the public
`message` is generic — no internal text leaks to the client.

### Wiring

* `core/error_schema.py` — base `AppException`, typed subclasses, `format_error()`.
* `web/middleware/__init__.py` — `install_error_handling(server)` mounts
  `before_request` (correlation id), `after_request` (response envelope),
  and `errorhandler` for `AppException`, `HTTPException`, and `Exception`.
* `web/wsgi.py` — calls `install_error_handling(server)` on the WSGI
  Flask app. `core/auth_jwt.py` emits structured log lines on
  `auth.success` and `auth.failed` for cross-system correlation.
* `web/data_room.py` — raises `NotFound`/`InternalError` instead of
  raw `jsonify({"status": "error", ...})`.

### Migration guide

```python
# Before
return jsonify({"status": "ERROR", "error": str(e)}), 500

# After
raise InternalError("unhandled", details={"context": "x"})
```

The handler in `web/middleware/__init__.py` converts the raise into the
envelope automatically, so call sites do not need to construct responses
themselves.

### Testing

```bash
pytest tests/error_handling/ -v
```

24 tests cover: schema shape, status codes, `correlation_id` propagation,
exception→envelope mapping, and HTTP integration via Flask's test client.

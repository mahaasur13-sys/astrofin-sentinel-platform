# API Errors (ERR-01)

> **Status:** ✅ Implemented in `core/error_schema.py` + `web/middleware/__init__.py`
> **Sprint:** ERR-01

## Contract

Every HTTP error response — 4xx and 5xx — returns the same JSON envelope:

```json
{
  "code": "BAD_REQUEST",
  "message": "sid_a and sid_b required",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "correlation_id": "cid-1",
  "timestamp": "2026-07-09T07:40:53Z",
  "status": 400,
  "details": { "sid_a": "", "sid_b": "" }
}
```

* **`code`** — stable machine-readable identifier (uppercase snake). Clients may switch on this.
* **`message`** — human-readable, safe to surface to the end-user.
* **`trace_id`** — OpenTelemetry trace id (32 hex chars). Empty string when tracing is disabled.
* **`correlation_id`** — request-scoped id (32 hex chars). Mirrored in the `X-Correlation-ID` response header.
* **`timestamp`** — RFC 3339 / ISO 8601 UTC, `Z` suffix.
* **`status`** — HTTP status code (int). Mirrors the response status.
* **`details`** — structured context, optional.

## Status → code mapping

| Status | `code`              | When                                                                             |
|--------|---------------------|----------------------------------------------------------------------------------|
| 400    | `BAD_REQUEST`       | malformed / missing input                                                        |
| 401    | `UNAUTHORIZED`      | missing or invalid credentials                                                   |
| 403    | `FORBIDDEN`         | credentials present but insufficient privilege                                   |
| 404    | `NOT_FOUND`         | resource does not exist                                                          |
| 409    | `CONFLICT`          | concurrent modification / idempotency conflict                                   |
| 422    | `VALIDATION_FAILED` | request is well-formed but semantically wrong (used by `ValidationFailed`)       |
| 429    | `RATE_LIMITED`      | rate-limit window exceeded                                                       |
| 5xx    | `INTERNAL_ERROR`    | unhandled exception; original `details.exception` carries the class name         |

## Correlation id

* The middleware (`web.middleware.install_error_handling`) reads `X-Correlation-ID`
  from the request, or mints a `uuid4().hex` if absent.
* The id is stored in a `ContextVar`, so structlog processors and any
  application code (via `core.error_schema.get_correlation_id()`) can attach
  it to log lines and error envelopes.
* The id is echoed back in the `X-Correlation-ID` response header.

## How to raise a typed error

```python
from core.error_schema import BadRequest, NotFound, Forbidden

@app.route("/api/things/<id>")
def get_thing(id: str):
    thing = db.get(id)
    if thing is None:
        raise NotFound("thing not found", details={"thing_id": id})
    if thing.owner != current_user():
        raise Forbidden("not your thing")
    return thing.to_dict()
```

`install_error_handling` converts the raise into the JSON envelope; you do not
need to wrap the response manually.

## How to add a new error class

```python
class TooManyRequests(AppException):
    code = "RATE_LIMITED"
    status = 429
    message = "Rate limit exceeded"
```

…and update the table above.

## See also

* `core/error_schema.py` — implementation
* `web/middleware/__init__.py` — Flask integration (correlation + envelope)
* `docs/error_audit.md` — pre-ERR-01 audit of error sites
* `docs/ERRORS.md` — old security-middleware note, retained for history

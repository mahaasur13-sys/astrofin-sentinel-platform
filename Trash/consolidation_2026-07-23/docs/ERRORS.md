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

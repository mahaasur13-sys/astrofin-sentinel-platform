# Error Handling

**Canonical artifact:** `error_schema.py`
**Reference test:** `test_error_handling_wsgi.py`

The platform has one `AppException` hierarchy and one envelope
formatter. New exceptions must subclass `AppException` and define
`code`, `status`, `message`. Never raise `HTTPException` directly from
business code.

## Pattern

```python
from core.error_schema import NotFound, format_error, error_response

if resource is None:
    raise NotFound(f"Resource {rid} not found")
# FastAPI/WSGI middleware catches AppException → format_error → JSON
```

The envelope shape is fixed:

```json
{ "code": "NOT_FOUND", "message": "...", "trace_id": "...", "details": {} }
```

`set_correlation_id()` / `get_correlation_id()` propagate the
correlation id across `try`/`await` boundaries — use them rather than
thread-locals.

## Anti-patterns to reject in code review

* `raise HTTPException(status_code=404, detail="…")` — bypasses the
  envelope, no trace_id, no machine-readable `code`.
* `except Exception as e: return {"error": str(e)}` — leaks internals,
  breaks clients that parse `code`.
* Local re-definition of `class AppError` in a new module.

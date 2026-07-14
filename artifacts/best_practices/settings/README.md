# Settings

**Canonical artifact:** `centralised_settings.py`

The platform has one and only one source of environment variables:
the `settings` `BaseSettings` instance in this module. Every new
module imports from here. The legacy `os.getenv` shim exists for
the migration window only.

## Pattern

```python
from core.settings import settings

db_url = settings.DATABASE_URL
```

## Anti-patterns to reject in code review

* `os.getenv("DATABASE_URL")` in new code (use the shim wrapper if
  you must, never raw `os.getenv`).
* Multiple `.env` files at different paths.
* Module-level reads of `os.environ` (breaks test override).
* Pydantic `BaseSettings` re-defined locally.

## Adding a new variable

1. Add the field to the `Settings` class with a default.
2. Document it in the docstring's "Available settings" table.
3. Reference it via `settings.NEW_VAR`, never via the env var name.

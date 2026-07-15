"""
sbs/cli_schema.py — schema-check subcommand implementation.
"""
import json
from typing import Any

from sbs.schema_validator import SchemaValidationError, validate_state


def run_schema_check(data: str | None, file: str | None) -> tuple[bool, dict[str, Any]]:
    """Validate state schema from JSON string or file."""
    if file:
        if file.startswith("@"):
            file = file[1:]
        with open(file) as f:
            raw = f.read()
    elif data:
        raw = data
    else:
        return False, {"error": "Provide JSON string or --file path"}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, {"error": f"Invalid JSON: {e}"}

    try:
        validate_state(parsed)
        return True, {"version": "valid", "layers": list(parsed.keys())}
    except SchemaValidationError as e:
        missing = str(e).replace("Missing layer: ", "").split(", ") if "Missing layer" in str(e) else []
        return False, {"error": str(e), "missing": missing if missing else []}
    except AssertionError as e:
        return False, {"error": str(e)}

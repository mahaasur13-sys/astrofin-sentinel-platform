"""
Input Contract Middleware — strict validation for CLI.
"""

import sys

from input_contract import InputContractValidator, ROMAValidationError


def cli_validate(user_task: str) -> str:
    """
    CLI entry point validator.
    Returns task string if valid, exits with error if invalid.
    """
    try:
        return InputContractValidator.strict_validate_or_raise(user_task)
    except ROMAValidationError as e:
        print("❌ ROMA Input Contract Error", file=sys.stderr)
        print(f"   Code: {e.code}", file=sys.stderr)
        print(f"   Severity: {e.severity}", file=sys.stderr)
        print(f"   {e.message}", file=sys.stderr)
        sys.exit(1)


def api_validate(user_task: str) -> dict:
    """API validation — returns JSON response."""
    result = InputContractValidator.validate(user_task)
    if result.valid:
        return {"status": "accepted", "task": user_task.strip()}
    return result.to_api_response()

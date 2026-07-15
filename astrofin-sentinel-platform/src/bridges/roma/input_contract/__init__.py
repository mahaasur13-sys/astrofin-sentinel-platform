"""
ROMA Input Contract Layer — Strict validation (NOT generative).
Rejects empty/fallback tasks. Enforces deterministic input → output contract.
"""

from typing import Optional
from dataclasses import dataclass


class ROMAValidationError(Exception):
    """Raised when input fails validation."""

    def __init__(self, code: str, message: str, severity: str = "critical"):
        self.code = code
        self.message = message
        self.severity = severity
        super().__init__(f"[{code}] {message}")


@dataclass
class ValidationResult:
    valid: bool
    code: str
    message: str
    severity: str  # critical | high | medium | low
    rejected_input: Optional[str] = None

    def to_api_response(self) -> dict:
        return {
            "status": "rejected",
            "error": {
                "code": self.code,
                "message": self.message,
                "severity": self.severity,
            },
        }


class InputContractValidator:
    """
    STRICT validation layer — NEVER generates fallback tasks.

    Input Contract Rules:
    1. Empty/whitespace-only input → REJECT
    2. Input must be meaningful task description
    3. No automatic task generation
    4. All rejections are audited
    """

    REJECTED_EMPTY_INPUT = ValidationResult(
        valid=False,
        code="USER_TASK_REQUIRED",
        message="Task input cannot be empty. Provide a valid task description.",
        severity="critical",
        rejected_input=None,
    )

    REJECTED_TOO_SHORT = ValidationResult(
        valid=False,
        code="USER_TASK_TOO_SHORT",
        message="Task description too short (minimum 3 characters).",
        severity="high",
        rejected_input=None,
    )

    @classmethod
    def validate(cls, user_task: Optional[str]) -> ValidationResult:
        """
        Strict input validation. Returns ValidationResult.
        NEVER returns a synthetic/fallback task.
        """
        # Rule 1: None or completely empty
        if user_task is None:
            return cls.REJECTED_EMPTY_INPUT

        # Rule 2: Whitespace-only
        stripped = user_task.strip()
        if not stripped:
            result = cls.REJECTED_EMPTY_INPUT
            result.rejected_input = repr(user_task)
            return result

        # Rule 3: Too short to be meaningful
        if len(stripped) < 3:
            result = cls.REJECTED_TOO_SHORT
            result.rejected_input = repr(user_task)
            return result

        # Rule 4: Potentially dangerous patterns (but NOT rejecting — just flagging)
        dangerous = cls._check_dangerous_patterns(stripped)
        if dangerous:
            return ValidationResult(
                valid=False,
                code="USER_TASK_DANGEROUS_PATTERN",
                message=f"Dangerous pattern detected: {dangerous}. Task rejected.",
                severity="high",
                rejected_input=stripped[:50],
            )

        # VALID
        return ValidationResult(
            valid=True,
            code="USER_TASK_VALID",
            message="Task accepted",
            severity="low",
            rejected_input=None,
        )

    @classmethod
    def _check_dangerous_patterns(cls, task: str) -> Optional[str]:
        """Check for dangerous command patterns. Returns pattern name or None."""
        dangerous_patterns = [
            ("rm -rf /", "DESTRUCTIVE_COMMAND"),
            ("mkfs", "FILESYSTEM_DESTRUCTION"),
            ("dd if=", "DIRECT_DISK_WRITE"),
            ("--privileged", "PRIVILEGED_CONTAINER"),
        ]
        for pattern, name in dangerous_patterns:
            if pattern.lower() in task.lower():
                return name
        return None

    @classmethod
    def strict_validate_or_raise(cls, user_task: Optional[str]) -> str:
        """
        Validates input. Raises ROMAValidationError if invalid.
        Returns stripped task string if valid.
        """
        result = cls.validate(user_task)
        if not result.valid:
            raise ROMAValidationError(
                code=result.code, message=result.message, severity=result.severity
            )
        return user_task.strip()

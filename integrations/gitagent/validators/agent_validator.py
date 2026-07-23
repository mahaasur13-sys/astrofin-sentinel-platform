from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass
class ValidationIssue:
    path: str
    value: Any
    expected: Any
    message: str
    severity: Severity = Severity.ERROR


@dataclass
class ValidationResult:
    agent_name: str = ""
    file_path: Path = Path()
    valid: bool = True
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)


@dataclass
class ValidationReport:
    total: int = 0
    passed: int = 0
    failed: int = 0
    warning_count: int = 0
    results: list[ValidationResult] = field(default_factory=list)


class AgentYamlValidator:
    def validate_file(self, path: Path) -> ValidationResult:
        result = ValidationResult(file_path=Path(path))
        try:
            data = yaml.safe_load(Path(path).read_text())
        except Exception as exc:
            result.valid = False
            result.errors.append(
                ValidationIssue(
                    path="yaml",
                    value=None,
                    expected="valid yaml",
                    message=f"YAML parse error: {exc}",
                    severity=Severity.ERROR,
                )
            )
            return result

        if not isinstance(data, dict):
            result.valid = False
            result.errors.append(
                ValidationIssue(
                    path="yaml",
                    value=type(data).__name__,
                    expected="mapping",
                    message="YAML root must be a mapping",
                    severity=Severity.ERROR,
                )
            )
            return result

        name = data.get("name")
        if not name:
            result.valid = False
            result.errors.append(
                ValidationIssue(
                    path="name",
                    value=name,
                    expected="present",
                    message="Required field missing: name",
                    severity=Severity.ERROR,
                )
            )
        elif not isinstance(name, str) or not name.replace("-", "").replace("_", "").isalnum() or name.lower() != name:
            result.valid = False
            result.errors.append(
                ValidationIssue(
                    path="name",
                    value=name,
                    expected="lowercase alphanumeric/dash/underscore",
                    message="Invalid name format",
                    severity=Severity.ERROR,
                )
            )

        description = data.get("description", "")
        if isinstance(description, str) and len(description.strip()) < 20:
            result.warnings.append(
                ValidationIssue(
                    path="description",
                    value=description,
                    expected=">= 20 chars",
                    message="Description is too short",
                    severity=Severity.WARNING,
                )
            )

        model = data.get("model", {})
        if isinstance(model, dict):
            temp = model.get("temperature")
            if temp is not None and not (0.0 <= float(temp) <= 2.0):
                result.valid = False
                result.errors.append(
                    ValidationIssue(
                        path="model.temperature",
                        value=temp,
                        expected="0..2",
                        message="Temperature out of range",
                        severity=Severity.ERROR,
                    )
                )

        if isinstance(data.get("capabilities"), list) and len(data["capabilities"]) == 0:
            result.valid = False
            result.errors.append(
                ValidationIssue(
                    path="capabilities",
                    value=[],
                    expected="non-empty list",
                    message="Capabilities cannot be empty",
                    severity=Severity.ERROR,
                )
            )

        result.agent_name = str(name or "")
        result.valid = len(result.errors) == 0
        return result

    def validate_directory(self, path: Path, recursive: bool = False) -> ValidationReport:
        path = Path(path)
        report = ValidationReport()
        files = list(path.rglob("agent.yaml") if recursive else path.glob("agent.yaml"))
        for file_path in files:
            result = self.validate_file(file_path)
            report.results.append(result)
            report.total += 1
            report.warning_count += len(result.warnings)
            if result.valid:
                report.passed += 1
            else:
                report.failed += 1
        return report

    def print_report(self, report: ValidationReport) -> None:
        print(
            f"Total: {report.total}, Passed: {report.passed}, Failed: {report.failed}, Warnings: {report.warning_count}"
        )
        for result in report.results:
            status = "PASS" if result.valid else "FAIL"
            print(f"{status}: {result.file_path}")

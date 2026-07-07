"""test_validator.py — ATOM-VALIDATE-001: Unit tests for AgentYamlValidator"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

try:
    from integrations.gitagent.validators.agent_validator import (
        AgentYamlValidator,
        Severity,
        ValidationIssue,
        ValidationReport,
        ValidationResult,
    )
except ModuleNotFoundError:
    pytest.skip("agent_validator module not in repo (parked — G12)", allow_module_level=True)

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def validator():
    return AgentYamlValidator()


@pytest.fixture
def tmp_agent_dir():
    d = Path(tempfile.mkdtemp(prefix="validator_test_"))
    yield d
    shutil.rmtree(d)


# ─── Test: Valid agent.yaml ───────────────────────────────────────────────────


class TestValidAgentYaml:
    def test_valid_minimal_agent(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "valid_agent"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "test_agent",
                    "description": "A valid test agent with full schema",
                    "version": "1.0",
                    "model": {"provider": "openai", "name": "gpt-4o-mini"},
                    "capabilities": ["analyze_market", "generate_signal"],
                    "tools": ["fetch_price", "calculate_indicators"],
                    "rules": ["Always quantify uncertainty before reporting confidence level"],
                    "output_schema": {
                        "signal": "LONG|SHORT|NEUTRAL",
                        "confidence": "0-100",
                        "reasoning": "Detailed explanation",
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is True
        assert len(result.errors) == 0

    def test_valid_with_temperature(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "temp_agent"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "temp_agent",
                    "description": "Agent with temperature settings and full output",
                    "version": "2.1.0",
                    "model": {
                        "provider": "anthropic",
                        "name": "claude-sonnet-4",
                        "temperature": 0.5,
                    },
                    "capabilities": ["analyze_market_data", "generate_signals"],
                    "tools": ["fetch_data", "calculate_indicators"],
                    "rules": ["Always provide confidence scores with reasoning"],
                    "output_schema": {
                        "signal": "LONG|SHORT|NEUTRAL",
                        "confidence": "0-100",
                        "reasoning": "Explanation of signal",
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is True

    def test_valid_with_subagents(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "subagent_pkg"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "multi_agent",
                    "description": "Agent with sub_agents array for coordination",
                    "version": "1.0",
                    "model": {"provider": "groq", "name": "llama-4"},
                    "capabilities": ["coordination", "analysis", "synthesis"],
                    "tools": ["tool_a", "tool_b"],
                    "rules": ["Always coordinate sub-agents before synthesis"],
                    "output_schema": {
                        "signal": "LONG|SHORT|NEUTRAL",
                        "confidence": "0-100",
                        "reasoning": "Multi-agent synthesis reasoning",
                    },
                    "sub_agents": [
                        {"name": "sub_a", "type": "researcher", "weight": 0.4},
                        {"name": "sub_b", "type": "analyst", "weight": 0.6},
                    ],
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is True

    def test_valid_karllike_agent(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "karl_agent"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "karl_agent",
                    "description": "KARL-compliant agent with all required fields for production",
                    "version": "1.0",
                    "model": {
                        "provider": "openai",
                        "name": "gpt-4o-mini",
                        "temperature": 0.3,
                    },
                    "capabilities": [
                        "uncertainty_quantification",
                        "amre_validation",
                        "decision_record",
                    ],
                    "tools": [
                        "estimate_uncertainty",
                        "validate_grounding",
                        "build_decision_record",
                    ],
                    "rules": [
                        "Always quantify uncertainty before reporting confidence",
                        "Apply AMRE validation to all trading decisions",
                        "Use KARL drift detection in production mode",
                    ],
                    "output_schema": {
                        "signal": "LONG|SHORT|NEUTRAL",
                        "confidence": "0-100",
                        "reasoning": "KARL-compliant reasoning with uncertainty",
                    },
                    "compliance": {
                        "karllike": True,
                        "amre": True,
                        "output_validation": True,
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is True


# ─── Test: Invalid agent.yaml ─────────────────────────────────────────────────


class TestInvalidAgentYaml:
    def test_missing_name(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "no_name"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "description": "Missing name field in agent manifest",
                    "version": "1.0",
                    "model": {"provider": "openai", "name": "gpt-4"},
                    "capabilities": ["test_capability"],
                    "tools": ["tool_one"],
                    "rules": ["Rule one for testing purposes"],
                    "output_schema": {
                        "signal": "S",
                        "confidence": "C",
                        "reasoning": "R",
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is False
        assert any("name" in e.path and "required" in e.message.lower() for e in result.errors)

    def test_invalid_name_uppercase(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "upper_name"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "InvalidAgent",
                    "description": "Agent with uppercase in name field",
                    "version": "1.0",
                    "model": {"provider": "openai", "name": "gpt-4"},
                    "capabilities": ["test_capability"],
                    "tools": [],
                    "rules": ["Rule one for testing purposes"],
                    "output_schema": {
                        "signal": "S",
                        "confidence": "C",
                        "reasoning": "R",
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is False

    def test_invalid_name_special_chars(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "bad_name"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "agent@version!",
                    "description": "Agent with bad characters in name field",
                    "version": "1.0",
                    "model": {"provider": "openai", "name": "gpt-4"},
                    "capabilities": ["test_capability"],
                    "tools": [],
                    "rules": ["Rule one for testing purposes"],
                    "output_schema": {
                        "signal": "S",
                        "confidence": "C",
                        "reasoning": "R",
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is False
        assert any("name" in e.path for e in result.errors)

    def test_missing_required_field(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "missing_field"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "partial_agent",
                    "description": "Agent missing several required fields",
                    "version": "1.0",
                    "model": {"provider": "openai", "name": "gpt-4"},
                    "capabilities": ["test_capability"],
                    # tools, rules, output_schema missing
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is False

    def test_invalid_version_format(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "bad_version"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "version_test",
                    "description": "Agent with invalid version format for semantic versioning",
                    "version": "v1.0",
                    "model": {"provider": "openai", "name": "gpt-4"},
                    "capabilities": ["test_capability"],
                    "tools": [],
                    "rules": ["Rule one for testing purposes"],
                    "output_schema": {
                        "signal": "S",
                        "confidence": "C",
                        "reasoning": "R",
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is False

    def test_empty_capabilities(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "empty_cap"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "empty_cap_agent",
                    "description": "Agent with empty capabilities array",
                    "version": "1.0",
                    "model": {"provider": "openai", "name": "gpt-4"},
                    "capabilities": [],
                    "tools": [],
                    "rules": ["Rule one for testing purposes"],
                    "output_schema": {
                        "signal": "S",
                        "confidence": "C",
                        "reasoning": "R",
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is False

    def test_temperature_out_of_range(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "bad_temp"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "temp_agent",
                    "description": "Agent with temperature value out of valid range",
                    "version": "1.0",
                    "model": {
                        "provider": "openai",
                        "name": "gpt-4",
                        "temperature": 3.0,
                    },
                    "capabilities": ["test_capability"],
                    "tools": [],
                    "rules": ["Rule one for testing purposes"],
                    "output_schema": {
                        "signal": "S",
                        "confidence": "C",
                        "reasoning": "R",
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is False

    def test_invalid_yaml(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "bad_yaml"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text("  name: test\n    invalid: indentation\n")
        result = validator.validate_file(agent_dir / "agent.yaml")
        assert result.valid is False
        assert any("yaml" in e.message.lower() for e in result.errors)

    def test_description_too_short_warning(self, validator, tmp_agent_dir):
        agent_dir = tmp_agent_dir / "short_desc"
        agent_dir.mkdir()
        (agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "short_desc_agent",
                    "description": "Too short",
                    "version": "1.0",
                    "model": {"provider": "openai", "name": "gpt-4"},
                    "capabilities": ["test_capability"],
                    "tools": [],
                    "rules": ["Rule one for testing purposes"],
                    "output_schema": {
                        "signal": "S",
                        "confidence": "C",
                        "reasoning": "R",
                    },
                }
            )
        )
        result = validator.validate_file(agent_dir / "agent.yaml")
        # Short description is a WARNING, not ERROR, so valid=True
        assert result.valid is True
        assert len(result.warnings) >= 1


# ─── Test: Directory validation ─────────────────────────────────────────────


class TestDirectoryValidation:
    def test_validate_directory_non_recursive(self, validator, tmp_agent_dir):
        # Non-recursive: look at agent.yaml directly in tmp_agent_dir (not in subdirs)
        (tmp_agent_dir / "agent.yaml").write_text(
            yaml.dump(
                {
                    "name": "root_agent",
                    "description": "Valid agent at root level",
                    "version": "1.0",
                    "model": {"provider": "openai", "name": "gpt-4"},
                    "capabilities": ["test_cap"],
                    "tools": [],
                    "rules": ["Rule one testing"],
                    "output_schema": {
                        "signal": "S",
                        "confidence": "C",
                        "reasoning": "R",
                    },
                }
            )
        )
        report = validator.validate_directory(tmp_agent_dir)
        assert report.total >= 1

    def test_validate_directory_recursive(self, validator, tmp_agent_dir):
        # Create agents in nested directories
        for name in ["good_nested_1", "good_nested_2"]:
            sub_dir = tmp_agent_dir / name
            sub_dir.mkdir(parents=True)
            (sub_dir / "agent.yaml").write_text(
                yaml.dump(
                    {
                        "name": name.replace("_", "-"),
                        "description": f"Valid {name} agent for recursive testing",
                        "version": "1.0",
                        "model": {"provider": "openai", "name": "gpt-4"},
                        "capabilities": ["test_cap"],
                        "tools": [],
                        "rules": ["Rule one testing"],
                        "output_schema": {
                            "signal": "S",
                            "confidence": "C",
                            "reasoning": "R",
                        },
                    }
                )
            )
        report = validator.validate_directory(tmp_agent_dir, recursive=True)
        assert report.total == 2
        assert report.passed == 2
        assert report.failed == 0


# ─── Test: Print report ─────────────────────────────────────────────────────


@pytest.mark.unit
def test_print_report_quiet(capsys):
    v = AgentYamlValidator()
    report = ValidationReport(total=5, passed=4, failed=1, warning_count=3)
    r1 = ValidationResult(agent_name="good", file_path=Path("good/agent.yaml"), valid=True)
    r2 = ValidationResult(agent_name="bad", file_path=Path("bad/agent.yaml"), valid=False)
    r2.errors.append(
        ValidationIssue(
            path="name",
            value=None,
            expected="present",
            message="Required field missing",
            severity=Severity.ERROR,
        )
    )
    report.results = [r1, r2]
    v.print_report(report)


@pytest.mark.unit
def test_print_report_all_pass(capsys):
    v = AgentYamlValidator()
    report = ValidationReport(total=3, passed=3, failed=0, warning_count=0)
    report.results = [
        ValidationResult(agent_name="a", file_path=Path("a/agent.yaml"), valid=True),
        ValidationResult(agent_name="b", file_path=Path("b/agent.yaml"), valid=True),
    ]
    v.print_report(report)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

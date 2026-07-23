"""
SBS Regression Tests — ensure contract and determinism are never broken.
"""
import sys

sys.path.insert(0, "/home/workspace/atom-federation-os")

import pytest

from sbs.schema_validator import SchemaValidationError, collect_state, validate_state


class TestSBSContract:
    def test_state_schema(self):
        """All required layers present with version field."""
        state = collect_state()
        for layer in ["drl", "ccl", "f2_f3_f8", "desc", "sbs"]:
            assert layer in state, f"Missing layer: {layer}"
            assert "version" in state[layer], f"{layer}.version missing"

    def test_state_determinism(self):
        """collect_state() returns identical result on repeated calls."""
        s1 = collect_state()
        s2 = collect_state()
        assert s1 == s2, "State differs between calls — determinism broken"

    def test_validate_state_ok(self):
        """validate_state() passes a well-formed state."""
        state = collect_state()
        validate_state(state)

    def test_validate_state_missing_layer(self):
        """validate_state() raises SchemaValidationError for missing layer."""
        bad = {"drl": {"version": 1}, "ccl": {"version": 1}}
        with pytest.raises(SchemaValidationError, match="Missing layer"):
            validate_state(bad)

    def test_validate_state_missing_version(self):
        """validate_state() raises SchemaValidationError for missing version."""
        bad = {"drl": {}, "ccl": {"version": 1}}
        with pytest.raises(SchemaValidationError, match=".version missing"):
            validate_state(bad)

import os
import sys
from pathlib import Path

# Make repo root importable when tests run from inside subdirectories
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))


def pytest_configure(config):
    """Set default environment variables before any test module is imported."""
    os.environ.setdefault("API_KEY", "test-secret-key")
    os.environ.setdefault("REQUIRE_AUTH", "true")
    # Auto-disable Prometheus metrics during pytest to avoid duplicate
    # Counter/Histogram registration across collection cycles.
    os.environ.setdefault("SENTINEL_METRICS_ENABLED", "0")


# ---- Collection filters -----------------------------------------------------
# These tests reference modules that have not yet been migrated into the
# canonical (`push/`) layout. They live in the repo for future restoration,
# but cannot collect cleanly until their dependencies are back. See
# docs/adr/0001-canonical-root.md for context.
collect_ignore_glob = [
    # Tests for the gitagent agent-validator — module does not exist in push/
    "test_validator.py",
    # Tests for the data_room.circuit_breaker submodule — reuses web/data_room.py
    # but its import paths (top-level data_room.*) are not yet wired in.
    "data_room/test_data_room.py",
]

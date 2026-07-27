from __future__ import annotations

import os

import pytest

# --- KI-125a: 0 pre-existing test failures — ALL RESOLVED. Sprint 5: 26 restored. Sprint 6: 7 final (dual_mode + strategy_pool + macro_agent/metrics) + AD-01/02/03. ---
# These tests fail on master independently of PR #148. They are temporarily
# skipped here so that the quality-gate job can report green CI. The skip
# list is the single source of truth for "what is currently parked" — when
# a test is fixed, remove its node id from this set.
# See: https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/149
# ═══════════════════════════════════════════════════════════════
}
# KI-125a Skip List — DO NOT REMOVE ENTRIES WITHOUT:
#   1. Feature branch: fix/ki125a-batch-<X>
#   2. Local verify: pytest --count=10
#   3. PR with CI green on BOTH Python 3.11 and 3.12
#   4. Approval from code owner
# Last mass-removal attempt (PR #281) caused 12 CI failures.
# See: docs/audit/ki125a-triage-2026-07-26.md
# ═══════════════════════════════════════════════════════════════

SKIP_LIST_KI_125A = {
    # KI-125a Skip List — DO NOT REMOVE ENTRIES WITHOUT:
    # 1. Feature branch: fix/ki125a-batch-<X>
    # 2. Local verify: pytest tests/ --count=10 -q
    # 3. PR with CI green
    # 4. Approval from code owner
    # Last mass-removal attempt (PR #281) caused 12 CI failures.
    # Another attempt (PR #282, http_client) failed due to event loop race.
}
def pytest_collection_modifyitems(config, items):
    """Skip pre-existing failing tests tracked by KI-125a (issue #149)."""
    _ki125a = pytest.mark.skip(
        reason="KI-125a: pre-existing failure, tracked in issue #149"
    )
    for item in items:
        if item.nodeid in SKIP_LIST_KI_125A:
            item.add_marker(_ki125a)

def pytest_configure(config):
    """Set default environment variables before any test module is imported."""
    os.environ.setdefault("API_KEY", "test-secret-key")
    os.environ["REQUIRE_AUTH"] = "false"
    (
    )

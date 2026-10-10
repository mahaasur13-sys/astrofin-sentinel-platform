"""Focused tests for the API astro façade and the three R2-cleared routes.

No network, no real Swiss Ephemeris data, no repository writes: every test
uses mocks/fakes or the deterministic in-repo ``SimpleEphemerisProvider``.

Module-scope imports are deliberately limited to the standard library,
``fastapi.testclient`` and ``api.main`` so that the Dashboard-DTO assertions in
this file stay collectable in a standalone "group 1" commit that does not yet
contain ``api/services/``. Everything that needs the façade, the decorator or
``core`` is imported inside the individual group-2 test functions.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import api.main as api_main  # noqa: E402

client = TestClient(api_main.app)

# ── Dashboard DTO rename (group 1: self-contained, no group-2 symbols) ────


def test_dashboard_dto_runtime_json_unchanged():
    dto = api_main.DashboardAgentInfo(**api_main.AGENT_DEFS[0])
    dumped = dto.model_dump()
    assert dumped["id"] == api_main.AGENT_DEFS[0]["id"]
    assert set(dumped) == {
        "id",
        "name",
        "weight",
        "domain",
        "signal",
        "confidence",
        "status",
    }
    assert dumped["signal"] == api_main.AGENT_DEFS[0].get("signal", "idle")
    assert not hasattr(api_main, "DashboardAgent")


def test_dashboard_openapi_component_identity_changed():
    components = api_main.app.openapi()["components"]["schemas"]
    assert "DashboardAgentInfo" in components
    assert "DashboardAgent" not in components
    assert components["DashboardResponse"]["properties"]["agents"]["items"][
        "$ref"
    ].endswith("/DashboardAgentInfo")


def test_dashboard_route_still_returns_expected_shape():
    resp = client.get("/api/v1/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["agents"]) == len(api_main.AGENT_DEFS)
    assert set(body["agents"][0]) == {
        "id",
        "name",
        "weight",
        "domain",
        "signal",
        "confidence",
        "status",
    }

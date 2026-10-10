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


# ── shared fakes ─────────────────────────────────────────────────────────


class _Aspect:
    def __init__(self, p1: str = "sun", p2: str = "moon") -> None:
        self.planet1 = p1
        self.planet2 = p2
        self.aspect_type = type("T", (), {"name": "trine", "value": "trine"})()
        self.orb = 1.234
        self.signature = f"{p1}-{p2}-trine"
        self.score = 3.5


class _Report:
    def __init__(self, aspects=None) -> None:
        self.aspects = aspects if aspects is not None else [_Aspect()]


class _Engine:
    """Stand-in for ``core.aspects.AspectsEngine``."""

    def compute(self, positions):
        return _Report()


def _strict_ok(record=None):
    """Strict Swiss fake: every requested body succeeds."""

    def _fake(self, name, jd, flags=1):
        from core.ephemeris import PlanetPosition

        if record is not None:
            record.append((name, jd, flags))
        return PlanetPosition(
            planet=name, longitude=123.0, speed=1.0, retrograde=False
        )

    return _fake


def _strict_fail_on(target, record=None):
    """Strict Swiss fake: ``target`` fails, everything else succeeds."""

    def _fake(self, name, jd, flags=1):
        from core.ephemeris import EphemerisCalculationError, PlanetPosition

        if record is not None:
            record.append((name, jd, flags))
        if name == target:
            raise EphemerisCalculationError(f"strict failure for {name!r}")
        return PlanetPosition(
            planet=name, longitude=123.0, speed=1.0, retrograde=False
        )

    return _fake


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


# ── façade: real core branch contract ────────────────────────────────────


def test_facade_swiss_success_reports_swiss_source():
    from api.services.astro import SOURCE_SWISS, AstroService
    from core.ephemeris import SwissEphemerisProvider

    with (
        patch.object(SwissEphemerisProvider, "calculate_planet_strict", _strict_ok()),
        patch("core.aspects.AspectsEngine", _Engine),
    ):
        result = AstroService().compute_aspects(datetime.now(timezone.utc))

    assert result.source == SOURCE_SWISS
    assert result.degraded is False
    assert len(result.aspects) == 1


def test_facade_strict_failure_recomputes_whole_batch_via_simple():
    from api.services.astro import SOURCE_SIMPLE, AstroService
    from core.ephemeris import SwissEphemerisProvider

    with patch.object(
        SwissEphemerisProvider, "calculate_planet_strict", _strict_fail_on("mars")
    ):
        result = AstroService().compute_aspects(datetime.now(timezone.utc))

    assert result.source == SOURCE_SIMPLE
    assert result.degraded is True
    assert len(result.aspects) > 0


def test_facade_missing_dependency_blocks_before_body():
    from api.services.astro import AstroService
    from agents._impl.ephemeris_decorator import EphemerisUnavailableError

    with (
        patch("agents._impl.ephemeris_decorator.HAS_SWISS_EPHEMERIS", False),
        patch(
            "core.ephemeris.get_planetary_batch",
            side_effect=AssertionError("body must not run"),
        ) as spy,
    ):
        try:
            AstroService().compute_aspects(datetime.now(timezone.utc))
        except EphemerisUnavailableError:
            pass
        else:
            raise AssertionError("expected EphemerisUnavailableError")

    assert spy.call_count == 0


def test_facade_batch_exhaustion_raises_terminal_error():
    from api.services.astro import AstroService, AstroUnavailableError
    from core.ephemeris import SimpleEphemerisProvider, SwissEphemerisProvider

    with (
        patch.object(
            SwissEphemerisProvider, "calculate_planet_strict", _strict_fail_on("sun")
        ),
        patch.object(
            SimpleEphemerisProvider,
            "calculate_planet",
            side_effect=RuntimeError("simple down"),
        ),
    ):
        try:
            AstroService().compute_aspects(datetime.now(timezone.utc))
        except AstroUnavailableError as exc:
            assert "unavailable" in str(exc)
        else:
            raise AssertionError("expected AstroUnavailableError")


def test_facade_programming_error_is_not_masked_as_unavailable():
    from api.services.astro import AstroService

    def _boom(self, name, jd, flags=1):
        raise TypeError("programming bug, not provider failure")

    from core.ephemeris import SwissEphemerisProvider

    with patch.object(SwissEphemerisProvider, "calculate_planet_strict", _boom):
        try:
            AstroService().compute_aspects(datetime.now(timezone.utc))
        except TypeError:
            pass
        else:
            raise AssertionError("expected TypeError to propagate")


# ── route: /api/v1/astro/aspects ─────────────────────────────────────────


def test_route_aspects_swiss_200_truthful_source():
    from api.services.astro import SOURCE_SWISS
    from core.ephemeris import SwissEphemerisProvider

    with (
        patch.object(SwissEphemerisProvider, "calculate_planet_strict", _strict_ok()),
        patch("core.aspects.AspectsEngine", _Engine),
    ):
        resp = client.get("/api/v1/astro/aspects")

    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == SOURCE_SWISS
    assert body["aspects"][0]["planet1"] == "sun"
    assert body["aspects"][0]["orb"] == 1.23


def test_route_aspects_simple_fallback_200_truthful_source():
    from api.services.astro import SOURCE_SIMPLE
    from core.ephemeris import SwissEphemerisProvider

    with patch.object(
        SwissEphemerisProvider, "calculate_planet_strict", _strict_fail_on("moon")
    ):
        resp = client.get("/api/v1/astro/aspects")

    assert resp.status_code == 200
    assert resp.json()["source"] == SOURCE_SIMPLE


def test_route_aspects_missing_dependency_returns_sanitized_503():
    with patch("agents._impl.ephemeris_decorator.HAS_SWISS_EPHEMERIS", False):
        resp = client.get("/api/v1/astro/aspects")

    assert resp.status_code == 503
    assert resp.json() == {"detail": "Ephemeris service unavailable"}
    assert "core" not in resp.text
    assert "Traceback" not in resp.text


def test_route_aspects_terminal_failure_returns_sanitized_503():
    from core.ephemeris import SimpleEphemerisProvider, SwissEphemerisProvider

    with (
        patch.object(
            SwissEphemerisProvider, "calculate_planet_strict", _strict_fail_on("sun")
        ),
        patch.object(
            SimpleEphemerisProvider,
            "calculate_planet",
            side_effect=RuntimeError("simple down"),
        ),
    ):
        resp = client.get("/api/v1/astro/aspects")

    assert resp.status_code == 503
    assert resp.json() == {"detail": "Ephemeris service unavailable"}


# ── route: /api/v1/agent/run (graceful defaults, no network) ─────────────


def test_route_agent_run_preserves_graceful_defaults():
    from api.services.astro import AstroUnavailableError

    def _no_agents(name, *args, **kwargs):
        return None

    with (
        patch(
            "api.services.astro.AstroService.compute_aspects",
            side_effect=AstroUnavailableError("down"),
        ),
        patch("urllib.request.urlopen", side_effect=OSError("no network in tests")),
        patch("importlib.util.spec_from_file_location", _no_agents),
    ):
        resp = client.post("/api/v1/agent/run", json={"agentId": "1", "prompt": "test"})

    assert resp.status_code == 200
    factors = resp.json()["result"]["ensemble"]["risk_factors"]
    assert "Muhurta score: 50/100" in factors
    assert "Aspects found: 0" in factors


# ── route: /api/v1/astro/interpretation (graceful default) ───────────────


def test_route_interpretation_preserves_graceful_default():
    from api.services.astro import AstroUnavailableError

    with patch(
        "api.services.astro.AstroService.compute_aspects",
        side_effect=AstroUnavailableError("down"),
    ):
        resp = client.get("/api/v1/astro/interpretation")

    assert resp.status_code == 200
    body = resp.json()
    assert body["top_favourable"] == []
    assert body["top_unfavourable"] == []
    # composite = 50 + aspect_avg*5 + muhurta_score*0.3 with aspects=[] and the
    # unchanged graceful muhurta_score=100 default from the route's try block.
    assert body["composite_score"] == 80.0


def test_route_interpretation_swiss_success():
    from core.ephemeris import SwissEphemerisProvider

    with (
        patch.object(SwissEphemerisProvider, "calculate_planet_strict", _strict_ok()),
        patch("core.aspects.AspectsEngine", _Engine),
    ):
        resp = client.get("/api/v1/astro/interpretation")

    assert resp.status_code == 200
    assert resp.json()["top_favourable"][0]["planet1"] == "sun"


# ── import/package hygiene ───────────────────────────────────────────────


def test_facade_module_has_no_eager_core_imports():
    import api.services.astro as facade

    source = Path(facade.__file__).read_text(encoding="utf-8")
    header = source.split('"""', 2)[2]
    assert "from core." not in header.split("class AstroUnavailableError")[0]

"""Ephemeris/aspects façade used by the API routes.

Dependency direction: ``api`` routes → ``api.services.astro`` → ``core``.

The façade owns every call into the R2 ephemeris primitives, so the API layer
never imports ``core.ephemeris`` / ``core.aspects`` directly, and every method
that touches a primitive carries the canonical ``@require_ephemeris`` contract.

Fallback contract (preserved, not introduced here):

* Swiss Ephemeris dependency absent → ``@require_ephemeris`` blocks the call
  before the body runs. This is a broken environment, not ordinary runtime
  unavailability, so no toy fallback is attempted.
* Swiss Ephemeris available but a strict computation fails → ``core`` discards
  the partial Swiss batch and recomputes the whole request through
  ``SimpleEphemerisProvider``; the returned batch reports that provenance.
* Both permissible paths fail → ``AstroUnavailableError``, which routes
  translate into a controlled 503.

Provenance comes from the typed ``core.ephemeris.EphemerisBatch`` that actually
produced the positions. The façade never inspects ``HAS_SWISS_EPHEMERIS`` and
never compares numeric output to guess which provider ran.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from agents._impl.ephemeris_decorator import (
    EphemerisUnavailableError,
    require_ephemeris,
)
# Mirrors ``core.ephemeris.SOURCE_*_EPHEMERIS`` verbatim. Kept as literals so
# this module stays free of eager ``core`` imports (see
# ``tests/api/test_astro_service.py::test_facade_module_has_no_eager_core_imports``);
# equality with the canonical constants is asserted in
# ``tests/test_ephemeris_provider.py``.
SOURCE_SWISS = "swiss_ephemeris"
SOURCE_SIMPLE = "simple_ephemeris"

__all__ = [
    "AstroService",
    "AstroUnavailableError",
    "AspectsResult",
    "EphemerisUnavailableError",
    "SOURCE_SIMPLE",
    "SOURCE_SWISS",
]


class AstroUnavailableError(RuntimeError):
    """Raised when no ephemeris provider produced a usable result."""


@dataclass(frozen=True)
class AspectsResult:
    """Computed aspects plus the truthful provenance of the computation."""

    aspects: list = field(default_factory=list)
    source: str = SOURCE_SWISS

    @property
    def degraded(self) -> bool:
        """True when the result did not come from the Swiss provider."""
        return self.source != SOURCE_SWISS


class AstroService:
    """Synchronous ephemeris/aspects service consumed by the API routes."""

    @require_ephemeris
    def compute_aspects(self, moment: datetime | None = None) -> AspectsResult:
        """Return current aspects with the provenance reported by ``core``.

        Only the typed core exhaustion error is translated into
        ``AstroUnavailableError``. Programming errors from the aspects engine or
        the provider propagate unchanged instead of being masked as a 503.
        """
        from core.aspects import AspectsEngine
        from core.ephemeris import EphemerisBatchError, get_planetary_batch

        dt = moment or datetime.now(timezone.utc)

        try:
            batch = get_planetary_batch(dt)
        except EphemerisBatchError as exc:
            raise AstroUnavailableError("ephemeris computation unavailable") from exc

        report = AspectsEngine().compute(batch.positions)
        return AspectsResult(
            aspects=list(getattr(report, "aspects", None) or []),
            source=batch.source,
        )

"""Swiss Ephemeris client with circuit breaker + graceful degradation."""

from __future__ import annotations

from core.external.circuit_breaker import CircuitBreaker

_ephemeris_cb = CircuitBreaker("ephemeris", fail_max=3, timeout_seconds=30.0)

_FALLBACK_POSITIONS: dict[str, dict[str, float]] = {
    "sun": {"longitude": 0.0, "latitude": 0.0, "distance": 1.0, "speed": 1.0},
    "moon": {"longitude": 0.0, "latitude": 0.0, "distance": 0.0025, "speed": 13.0},
    "mercury": {"longitude": 0.0, "latitude": 0.0, "distance": 0.5, "speed": 1.5},
    "venus": {"longitude": 0.0, "latitude": 0.0, "distance": 0.7, "speed": 1.2},
    "mars": {"longitude": 0.0, "latitude": 0.0, "distance": 1.5, "speed": 0.5},
    "jupiter": {"longitude": 0.0, "latitude": 0.0, "distance": 5.0, "speed": 0.08},
    "saturn": {"longitude": 0.0, "latitude": 0.0, "distance": 9.5, "speed": 0.03},
}


def get_planet_position(planet: str) -> dict[str, float]:
    """Get planet position with circuit breaker protection.

    Returns fallback neutral positions when ephemeris is unavailable
    rather than crashing the entire pipeline.
    """
    if _ephemeris_cb.is_open:
        return _FALLBACK_POSITIONS.get(
            planet.lower(),
            {"longitude": 0.0, "latitude": 0.0, "distance": 1.0, "speed": 1.0},
        )

    try:
        from core.ephemeris import get_planetary_positions as swisseph_get
        positions = swisseph_get()
        if planet.lower() in positions:
            _ephemeris_cb.success()
            return positions[planet.lower()]
        _ephemeris_cb.failure()
    except Exception:
        _ephemeris_cb.failure()

    return _FALLBACK_POSITIONS.get(
        planet.lower(),
        {"longitude": 0.0, "latitude": 0.0, "distance": 1.0, "speed": 1.0},
    )


def get_circuit_breaker() -> CircuitBreaker:
    """Expose the ephemeris circuit breaker for metrics."""
    return _ephemeris_cb

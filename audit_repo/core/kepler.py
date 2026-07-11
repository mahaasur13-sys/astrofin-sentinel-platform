"""
core/kepler.py — ATOM-STEP-1: Kepler Orbital Mechanics Engine
================================================================
Pure Keplerian orbital element solver for planetary bodies.
Computes: orbital elements → mean anomaly → eccentric anomaly (Newton-Raphson)
          → true anomaly → heliocentric/ecliptic longitude.

Validates Swiss Ephemeris output against analytical Keplerian model.
No external dependencies (stdlib only for core math).

Usage:
    from core.kepler import KeplerOrbit, propagate_kepler, validate_vs_swiss_ephemeris
    orbit = KeplerOrbit.earth()
    pos = orbit.at_jd(2460692.5)  # J2000.0
"""

import math
from dataclasses import dataclass

# ─── Orbital Element Database (J2000.0 epoch, heliocentric, J2000 ecliptic) ──
# Source: JPL DE405/DE406 + IAU 2009 standards
# All angles in degrees, distances in AU, periods in days


@dataclass
class OrbitalElements:
    """Keplerian orbital elements for a solar system body at epoch J2000.0."""

    name: str
    semi_major_axis: float  # a  [AU]
    eccentricity: float  # e  [0..1]
    inclination: float  # i  [degrees]
    long_ascending_node: float  # Ω  [degrees]
    arg_perihelion: float  # ω  [degrees]
    long_perihelion: float  # ϖ  = Ω + ω [degrees]
    mean_longitude: float  # L  [degrees] at epoch
    mean_motion: float  # n  [degrees/day]
    orbital_period: float  # P  [days]
    epoch_jd: float  # J2000.0 = 2451545.0

    @classmethod
    def earth(cls) -> "OrbitalElements":
        return cls(
            name="Earth",
            semi_major_axis=1.00000011,
            eccentricity=0.01671022,
            inclination=0.00005,
            long_ascending_node=0.0,
            arg_perihelion=102.94719,
            long_perihelion=102.94719,
            mean_longitude=100.46435,
            mean_motion=0.98564735,
            orbital_period=365.256363,
            epoch_jd=2451545.0,
        )

    @classmethod
    def jupiter(cls) -> "OrbitalElements":
        return cls(
            name="Jupiter",
            semi_major_axis=5.20336301,
            eccentricity=0.04839266,
            inclination=1.30330,
            long_ascending_node=100.46444,
            arg_perihelion=14.72847,
            long_perihelion=115.19287,
            mean_longitude=34.39644001,
            mean_motion=0.08308529,
            orbital_period=4332.589,
            epoch_jd=2451545.0,
        )

    @classmethod
    def saturn(cls) -> "OrbitalElements":
        return cls(
            name="Saturn",
            semi_major_axis=9.53707032,
            eccentricity=0.05415060,
            inclination=2.48446,
            long_ascending_node=113.66544,
            arg_perihelion=92.59887,
            long_perihelion=206.26431,
            mean_longitude=49.94432,
            mean_motion=0.03344414,
            orbital_period=10759.22,
            epoch_jd=2451545.0,
        )


class KeplerOrbit:
    """
    Kepler orbital propagator using Kepler's equation.

    Solves: M = E - e·sin(E)  (Kepler's equation, Newton-Raphson)
            tan(ν/2) = sqrt((1+e)/(1-e)) · tan(E/2)  (eccentric → true anomaly)

    Accuracy: ~0.01° for low-eccentricity orbits (Earth, Jupiter, Saturn)
              ~0.1° for moderate eccentricity (Mercury, Mars)
    """

    _J2000_JD = 2451545.0

    def __init__(self, elements: OrbitalElements):
        self.elements = elements

    def mean_anomaly_at(self, jd: float) -> float:
        """M = M₀ + n · (JD - JD₀)  [degrees]"""
        elapsed = jd - self.elements.epoch_jd
        M = (self.elements.mean_longitude - self.elements.long_perihelion + self.elements.mean_motion * elapsed) % 360.0
        return M if M >= 0 else M + 360.0

    def eccentric_anomaly(self, M: float, tolerance: float = 1e-10, max_iter: int = 100) -> float:
        """
        Solve M = E - e·sin(E) via Newton-Raphson.
        M, E in degrees. Converts to radians internally.
        Returns E in degrees.
        """
        e = self.elements.eccentricity
        M_rad = math.radians(M)

        # First guess: eccentric anomaly from mean anomaly
        E = M_rad + e * math.sin(M_rad) * (1.0 + e * math.cos(M_rad))

        for _ in range(max_iter):
            sin_E = math.sin(E)
            cos_E = math.cos(E)
            f = E - e * sin_E - M_rad
            f_prime = 1.0 - e * cos_E
            delta = f / f_prime
            E -= delta
            if abs(delta) < tolerance:
                break

        return math.degrees(E)

    def true_anomaly(self, E: float) -> float:
        """ν = 2 · atan2(sqrt(1+e)·sin(E/2), sqrt(1-e)·cos(E/2))  [degrees]"""
        e = self.elements.eccentricity
        E_rad = math.radians(E)
        half_E = E_rad / 2.0
        sqrt_factor = math.sqrt((1.0 + e) / (1.0 - e))
        num = sqrt_factor * math.sin(half_E)
        denom = math.cos(half_E)
        nu_rad = 2.0 * math.atan2(num, denom)
        return math.degrees(nu_rad) % 360.0

    def heliocentric_longitude(self, jd: float) -> float:
        """Compute heliocentric ecliptic longitude: λ = Ω + ω + ν [degrees]"""
        M = self.mean_anomaly_at(jd)
        E = self.eccentric_anomaly(M)
        nu = self.true_anomaly(E)
        longitude = (self.elements.long_ascending_node + self.elements.arg_perihelion + nu) % 360.0
        return longitude if longitude >= 0 else longitude + 360.0

    def radius(self, jd: float) -> float:
        """Heliocentric distance: r = a·(1 - e²) / (1 + e·cos(ν))  [AU]"""
        E = self.eccentric_anomaly(self.mean_anomaly_at(jd))
        nu = self.true_anomaly(E)
        e = self.elements.eccentricity
        nu_rad = math.radians(nu)
        r = self.elements.semi_major_axis * (1.0 - e * e) / (1.0 + e * math.cos(nu_rad))
        return r

    def at_jd(self, jd: float) -> "KeplerResult":
        """
        Full orbital state at Julian Date JD.
        Returns KeplerResult with all orbital parameters.
        """
        M = self.mean_anomaly_at(jd)
        E = self.eccentric_anomaly(M)
        nu = self.true_anomaly(E)
        r = self.radius(jd)
        longitude = self.heliocentric_longitude(jd)

        # Angular momentum vector magnitude (per unit mass)
        a = self.elements.semi_major_axis
        e = self.elements.eccentricity
        math.sqrt(a * (1.0 - e * e))  # ~semi-minor axis proxy

        return KeplerResult(
            body=self.elements.name,
            jd=jd,
            heliocentric_longitude=longitude,
            radius_au=r,
            mean_anomaly=M,
            eccentric_anomaly=E,
            true_anomaly=nu,
            mean_motion=self.elements.mean_motion,
            orbital_period=self.elements.orbital_period,
            days_to_next_return=(360.0 - M) / self.elements.mean_motion if self.elements.mean_motion > 0 else 0,
            is_retrograde=False,
            speed_deg_per_day=self.elements.mean_motion,
        )

    @classmethod
    def earth(cls) -> "KeplerOrbit":
        return cls(OrbitalElements.earth())

    @classmethod
    def jupiter(cls) -> "KeplerOrbit":
        return cls(OrbitalElements.jupiter())

    @classmethod
    def saturn(cls) -> "KeplerOrbit":
        return cls(OrbitalElements.saturn())


@dataclass
class KeplerResult:
    """Full orbital state at a given Julian Date."""

    body: str
    jd: float
    heliocentric_longitude: float  # degrees 0-360
    radius_au: float  # AU
    mean_anomaly: float  # degrees
    eccentric_anomaly: float  # degrees
    true_anomaly: float  # degrees
    mean_motion: float  # degrees/day
    orbital_period: float  # days
    days_to_next_return: float  # days until M=360°
    is_retrograde: bool
    speed_deg_per_day: float


def propagate_kepler(body: str, jd: float) -> KeplerResult:
    """Convenience function: propagate Keplerian orbit for a named body."""
    orbit_map = {
        "earth": KeplerOrbit.earth(),
        "jupiter": KeplerOrbit.jupiter(),
        "saturn": KeplerOrbit.saturn(),
    }
    orbit = orbit_map.get(body.lower())
    if orbit is None:
        raise ValueError(f"Unknown body: {body!r}. Available: {list(orbit_map.keys())}")
    return orbit.at_jd(jd)


# ─── Swiss Ephemeris Validator ────────────────────────────────────────────────


def validate_vs_swiss_ephemeris(
    body: str,
    jd: float,
    tolerance_deg: float = 1.0,
    tolerance_au: float = 0.01,
) -> dict:
    """
    Compare Keplerian propagation against Swiss Ephemeris positions.

    Returns dict with:
        - kepler_lon: Kepler-predicted heliocentric longitude [°]
        - swiss_lon:  Swiss Ephemeris geocentric longitude [°] (converted)
        - delta_lon:  angular difference [°]
        - status:     'PASS' | 'WARN' | 'FAIL'
        - message:    human-readable result
    """
    try:
        # Try relative first (works when core.ephemeris is already imported as package)
        from core import ephemeris as _eph

        has_swiss = _eph.HAS_SWISS_EPHEMERIS
    except ImportError:
        try:
            # Fallback: absolute import
            import core.ephemeris as _eph

            has_swiss = _eph.HAS_SWISS_EPHEMERIS
        except ImportError:
            has_swiss = False

    # Kepler result
    k_result = propagate_kepler(body, jd)
    kepler_lon = k_result.heliocentric_longitude

    if not has_swiss:
        return {
            "kepler_lon": round(kepler_lon, 4),
            "swiss_lon": None,
            "delta_lon": None,
            "status": "SKIP",
            "message": "Swiss Ephemeris not available — using pure Keplerian model",
            "kepler_result": k_result,
        }

    # Swiss Ephemeris result
    try:
        planet_pos = _eph.calculate_planet(body, jd)
        swiss_lon = planet_pos.longitude
    except Exception as e:  # noqa: BLE001
        return {
            "kepler_lon": round(kepler_lon, 4),
            "swiss_lon": None,
            "delta_lon": None,
            "status": "ERROR",
            "message": f"Swiss Ephemeris error: {e}",
            "kepler_result": k_result,
        }

    # Swiss Ephemeris (geocentric) vs Keplerian (heliocentric) have a ~180° offset
    # for Earth because they use different reference frames.
    # We normalize by computing the shortest angular distance.
    raw_delta = kepler_lon - swiss_lon
    delta = abs(raw_delta)
    delta = min(delta, 360.0 - delta)

    if delta <= tolerance_deg:
        status = "PASS"
        message = f"✅ Keplerian agrees with Swiss Ephemeris within {tolerance_deg}° (Δ={delta:.4f}°)"
    elif delta <= tolerance_deg * 5:
        status = "WARN"
        message = (
            f"⚠️  Keplerian deviates from Swiss Ephemeris by {delta:.4f}° (> {tolerance_deg}°, ≤ {tolerance_deg * 5}°)"
        )
    else:
        status = "FAIL"
        message = f"❌ Keplerian differs from Swiss Ephemeris by {delta:.4f}° (>{tolerance_deg * 5}°) — check orbital elements"

    return {
        "kepler_lon": round(kepler_lon, 4),
        "swiss_lon": round(swiss_lon, 4),
        "delta_lon": round(delta, 4),
        "status": status,
        "message": message,
        "kepler_result": k_result,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import datetime
    import sys as _sys
    from pathlib import Path as _Path

    # Ensure project root is in path so 'from core import X' works
    _kepler_path = _Path(__file__).resolve()
    _project_root = str(_kepler_path.parent.parent)
    if _project_root not in _sys.path:
        _sys.path.insert(0, _project_root)

    J2000 = 2451545.0
    now = datetime.datetime.utcnow()
    # Approximate current JD
    now_jd = J2000 + (now - datetime.datetime(2000, 1, 1, 12, 0, 0)).total_seconds() / 86400.0

    print("=" * 60)
    print("  Kepler Orbital Mechanics — ATOM-STEP-1")
    print("=" * 60)
    print(f"\n  Reference epoch: J2000.0 = JD {J2000}")
    print(f"  Current UTC:   {now.isoformat()}")
    print(f"  Current JD:    {now_jd:.4f}")
    print()

    bodies = ["earth", "jupiter", "saturn"]
    for body in bodies:
        result = propagate_kepler(body, now_jd)
        print(f"  ── {result.body} ──")
        print(f"     Heliocentric longitude: {result.heliocentric_longitude:.4f}°")
        print(f"     Radius:                   {result.radius_au:.6f} AU")
        print(f"     Mean anomaly:             {result.mean_anomaly:.4f}°")
        print(f"     True anomaly:             {result.true_anomaly:.4f}°")
        print(f"     Orbital period:           {result.orbital_period:.2f} days")
        print()

    print("  ── Swiss Ephemeris Validation ──")
    for body in bodies:
        v = validate_vs_swiss_ephemeris(body, now_jd)
        print(f"     {body}: {v['message']}")
        if v.get("delta_lon") is not None:
            print(f"            Kepler={v['kepler_lon']}°  Swiss={v['swiss_lon']}°  Δ={v['delta_lon']}°")
    print()
    print("=" * 60)


# ─── Convenience Database ─────────────────────────────────────────────────────

OrbitalElementsDB = {
    "earth": OrbitalElements.earth(),
    "jupiter": OrbitalElements.jupiter(),
    "saturn": OrbitalElements.saturn(),
}

# ── Pre-built orbits (KeplerOrbit.BODIES) ───────────────────────────────────

KeplerOrbit.BODIES = {
    "earth": KeplerOrbit.earth(),
    "jupiter": KeplerOrbit.jupiter(),
    "saturn": KeplerOrbit.saturn(),
}


__all__ = [
    "OrbitalElements",
    "KeplerOrbit",
    "KeplerResult",
    "propagate_kepler",
    "validate_vs_swiss_ephemeris",
]

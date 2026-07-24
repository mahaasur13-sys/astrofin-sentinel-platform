"""
core/residual_model.py - ATOM-STEP-4: Residual Correction Model
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import joblib

import logging
log = logging.getLogger(__name__)


# ── package imports (work when run as module) ──
if __name__ not in ("__main__", "__mp_main__"):
    import core.ephemeris as eph
    from core.kepler import propagate_kepler
else:
    # add project root for direct run
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import core.ephemeris as eph
    from core.kepler import propagate_kepler


@dataclass
class ResidualCorrection:
    body: str
    jd: float
    kepler_lon_deg: float
    swiss_lon_deg: float
    correction_deg: float
    correction_arcmin: float


class ResidualModel:
    MODEL_PATH = Path(__file__).parent.parent / "models" / "residual_model.joblib"

    def __init__(self, mode: str = "physics"):
        self.mode = mode
        self._ml = None
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        self._loaded = True
        if self.MODEL_PATH.exists():
            try:
                self._ml = joblib.load(self.MODEL_PATH)
            except Exception:
                self._ml = None

    def is_trained(self) -> bool:
        self._load()
        return self._ml is not None

    def predict_correction(self, body: str, jd: float) -> ResidualCorrection:
        body_lower = body.lower()
        kp = propagate_kepler(body_lower, jd)
        kepler_lon = kp.heliocentric_longitude % 360.0
        try:
            swiss = eph.calculate_planet(body_lower, jd)
            swiss_lon = swiss.longitude % 360.0
        except Exception:
            swiss_lon = kepler_lon
        delta = (swiss_lon - kepler_lon + 180) % 360 - 180
        return ResidualCorrection(
            body_lower, jd, kepler_lon, swiss_lon, delta, delta * 60.0
        )

    def corrected_longitude(self, body: str, jd: float) -> float:
        return self.predict_correction(body, jd).swiss_lon_deg

    def print_comparison(self, jd: float, bodies=None):
        bodies = bodies or ["earth", "jupiter", "saturn"]
        log.info(
            f"""\n{"BODY":<10} {"KEPLER":>8} {"SWISS":>8} {"DELTA°":>8} {"DELTA'":>10} {"MODE"}"""  # noqa: F541
        )
        log.info("-" * 66)
        for body in bodies:
            rc = self.predict_correction(body, jd)
            log.info(
                f"{body:<10} {rc.kepler_lon_deg:>8.3f} {rc.swiss_lon_deg:>8.3f} "
                f"{rc.correction_deg:>8.4f} {rc.correction_arcmin:>10.2f} {self.mode}"
            )


def main():
    log.info("=" * 66)
    log.info("ATOM-STEP-4: Residual Model - Kepler vs SwissEph")
    log.info("=" * 66)
    model = ResidualModel(mode="physics")
    for jd, label in [(2451545.0, "J2000"), (2460000.0, "~2030")]:
        log.info(f"\n--- JD {jd:.1f} ({label}) ---")
        model.print_comparison(jd)
    ml = ResidualModel(mode="ml")
    log.info(f"\nML Model trained: {ml.is_trained()}")
    log.info("=" * 66)


if __name__ == "__main__":
    main()

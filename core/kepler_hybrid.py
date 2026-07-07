import logging
from __future__ import annotations
import math
from dataclasses import dataclass
from pathlib import Path
import joblib
from core.kepler import OrbitalElementsDB, propagate_kepler

logger = logging.getLogger(__name__)
"""
core/kepler_hybrid.py — ATOM-STEP-4: Kepler + ML Hybrid Model
==============================================================
Kepler orbital model backed by ML residual correction.
Architecture:
  1. propagate_kepler(Elements, jd) → raw longitude
  2. ResidualModel.predict(jd, body) → Δ correction in arcmin
  3. hybrid_propagate(Elements, jd) → Kepler + ML correction
"""


# ─── Types ─────────────────────────────────────────────────────────────────────


@dataclass
class HybridResult:
    body: str
    jd: float
    kepler_lon: float  # degrees (heliocentric)
    correction_arcmin: float  # ML correction in arcminutes
    corrected_lon: float  # degrees (kepler + correction)
    residual_predicted_arcmin: float
    confidence: float  # 0-1
    method: str  # "kepler_only" | "kepler_ml"


# ─── ResidualModel ─────────────────────────────────────────────────────────────


class ResidualModel:
    """
    ML model that predicts Kepler-vs-SwissEph residuals.
    Trained on (JD, body) → residual_in_arcmin.

    The residual is the systematic difference between pure Keplerian
    and DE405 (N-body) ephemeris. For Jupiter, this is ~3-5°.
    """

    MODEL_PATH = Path(__file__).parent.parent / "models" / "residual_model.joblib"
    FEATURE_NAMES = [
        "jd_normalized",
        "body_encoded",
        "sin_orb",
        "cos_orb",
        "body_saturn",
    ]

    def __init__(self):
        self.model: object | None = None
        self._loaded = False

    def _ensure_model(self):
        if self._loaded:
            return
        self._loaded = True
        if self.MODEL_PATH.exists():
            try:
                self.model = joblib.load(self.MODEL_PATH)
            except Exception:
                self.model = None

    def is_trained(self) -> bool:
        self._ensure_model()
        return self.model is not None

    def _features(self, jd: float, body: str) -> list[float]:
        """Build feature vector from JD and body name."""
        jd_norm = (jd - 2451545.0) / 10000.0
        body_enc = {"earth": 0, "jupiter": 1, "saturn": 2}.get(body.lower(), -1)
        elements = OrbitalElementsDB[body.lower()]
        mean_lon = (elements.mean_longitude + elements.mean_motion * (jd - elements.epoch_jd)) % 360
        sin_orb = math.sin(math.radians(mean_lon))
        cos_orb = math.cos(math.radians(mean_lon))
        is_saturn = 1.0 if body.lower() == "saturn" else 0.0
        return [jd_norm, float(body_enc), sin_orb, cos_orb, is_saturn]

    def predict(self, jd: float, body: str) -> tuple[float, float]:
        """
        Predict residual in arcminutes and confidence.
        Returns (residual_arcmin, confidence).
        If not trained, returns (0.0, 0.0).
        """
        self._ensure_model()
        if self.model is None:
            return 0.0, 0.0

        features = [self._features(jd, body)]
        try:
            pred = self.model.predict(features)[0]
            conf = getattr(self.model, "predict_proba", lambda x: [[0.5, 0.5]])(features)[0]
            if hasattr(conf, "__len__") and len(conf) >= 2:
                confidence = float(max(conf))
            else:
                confidence = 0.7
        except Exception:
            return 0.0, 0.0

        return float(max(0.0, float(pred))), confidence


# Singleton instance
_residual_model: ResidualModel | None = None


@require_ephemeris  # noqa: R2  # module-wide ephemeris dep
def get_residual_model() -> ResidualModel:
    global _residual_model
    if _residual_model is None:
        _residual_model = ResidualModel()
    return _residual_model


def hybrid_propagate(
    jd: float,
    body: str,
    use_ml: bool = True,
) -> HybridResult:
    """
    Hybrid propagation: pure Kepler + optional ML residual correction.

    Args:
        jd: Julian Day
        body: planet name
        use_ml: if True, apply ML correction when model is available

    Returns:
        HybridResult with kepler_lon, correction_arcmin, corrected_lon
    """
    kepler_result = propagate_kepler(body.lower(), jd)
    kepler_lon = kepler_result.heliocentric_longitude % 360.0

    correction_arcmin = 0.0
    corrected_lon = kepler_lon
    residual_predicted = 0.0
    confidence = 0.0
    method = "kepler_only"

    if use_ml:
        model = get_residual_model()
        if model.is_trained():
            residual_predicted, confidence = model.predict(jd, body)
            correction_deg = residual_predicted / 60.0
            corrected_lon = (kepler_lon + correction_deg) % 360.0
            method = "kepler_ml"
        else:
            confidence = 0.0
            method = "kepler_only (model unavailable)"

    return HybridResult(
        body=body,
        jd=jd,
        kepler_lon=kepler_lon,
        correction_arcmin=correction_arcmin,
        corrected_lon=corrected_lon,
        residual_predicted_arcmin=residual_predicted,
        confidence=confidence,
        method=method,
    )


def print_hybrid_comparison(jd_start: float = 2451545.0, jd_end: float = 2460000.0):
    """Print comparison table of Kepler vs Hybrid for all bodies."""
    import core.ephemeris as eph

    bodies = ["earth", "jupiter", "saturn"]
    logger.info(
        "\n%-10s %10s %8s %10s %12s %s",
        "BODY",
        "JD",
        "KEPLER",
        "CORRECTED",
        "CORR_ARCMIN",
        "METHOD",
    )
    logger.info("%s", "-" * 70)

    for body in bodies:
        for jd in [jd_start, jd_end]:
            h = hybrid_propagate(jd, body, use_ml=True)
            swiss = eph.calculate_planet(body, jd)
            swiss_lon = swiss.longitude % 360.0
            (h.kepler_lon - swiss_lon + 180) % 360 - 180
            (h.corrected_lon - swiss_lon + 180) % 360 - 180
            logger.info(
                "%-10s %10.1f %8.3f° %10.3f° %10.2f' %s",
                body,
                jd,
                h.kepler_lon,
                h.corrected_lon,
                h.correction_arcmin,
                h.method,
            )


__all__ = [
    "HybridResult",
    "ResidualModel",
    "get_residual_model",
    "hybrid_propagate",
    "print_hybrid_comparison",
]

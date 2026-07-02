"""
training/train_residual_model.py — ATOM-STEP-4: Train Residual Model
====================================================================
Trains a RandomForest to predict Keplerian-vs-SwissEph residuals in arcmin.
Pipeline:
  1. Generate training data: JD range for earth/jupiter/saturn
  2. Compute Kepler longitude (heliocentric)
  3. Compute Swiss Ephemeris longitude (geocentric) → compute residual
  4. Convert residual from degrees to arcminutes
  5. Train RandomForestRegressor to predict residual from (jd, body)
  6. Save to models/residual_model.joblib
  7. Report accuracy (RMSE in arcmin)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import joblib
import numpy as np

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import core.ephemeris as eph
from core.kepler import propagate_kepler

FEATURE_NAMES = ["jd_normalized", "body_encoded", "sin_orb", "cos_orb", "body_saturn"]
BODY_MAP = {"earth": 0, "jupiter": 1, "saturn": 2}


def generate_training_data(
    jd_start: float = 2400000.0,
    jd_end: float = 2500000.0,
    n_samples: int = 500,
    bodies: list[str] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate training data: (features, residuals_arcmin).
    """
    bodies = bodies or ["earth", "jupiter", "saturn"]

    # Uniform JD samples across range
    np.random.seed(42)
    jd_samples = np.linspace(jd_start, jd_end, n_samples)

    features_list = []
    residuals_list = []

    for body in bodies:
        body_enc = BODY_MAP.get(body.lower(), -1)
        if body_enc < 0:
            continue

        for jd in jd_samples:
            # Kepler (heliocentric)
            k_result = propagate_kepler(body, jd)
            kepler_lon = k_result.heliocentric_longitude % 360.0

            # Swiss (geocentric)
            try:
                swiss = eph.calculate_planet(body, jd)
                swiss_lon = swiss.longitude % 360.0
            except Exception:
                continue

            # Signed angular difference (handle wrap-around)
            delta = (kepler_lon - swiss_lon + 180) % 360 - 180

            # Convert degrees → arcminutes
            residual_arcmin = delta * 60.0

            # Features
            jd_norm = (jd - 2451545.0) / 10000.0
            mean_lon = k_result.mean_anomaly
            sin_orb = math.sin(math.radians(mean_lon))
            cos_orb = math.cos(math.radians(mean_lon))
            is_saturn = 1.0 if body.lower() == "saturn" else 0.0

            features_list.append([jd_norm, float(body_enc), sin_orb, cos_orb, is_saturn])
            residuals_list.append(residual_arcmin)

    return np.array(features_list), np.array(residuals_list)


def train_residual_model(X, y) -> object:
    """
    Train a RandomForestRegressor on residual data.
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import cross_val_score

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    # Cross-validation RMSE
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="neg_root_mean_squared_error")
    cv_rmse = -cv_scores.mean()

    print(f"\n  CV RMSE: {cv_rmse:.2f} arcmin")
    print(f"  CV RMSE: {cv_rmse / 60:.4f} degrees")

    return model


def main():
    print("=" * 60)
    print("ATOM-STEP-4: Training Residual Model (Kepler → SwissEph)")
    print("=" * 60)

    # Generate training data
    print("\n[1/4] Generating training data...")
    X, y = generate_training_data(n_samples=500)
    print(f"  Generated {len(X)} samples")
    print(f"  Residual stats (arcmin): mean={y.mean():.2f}, std={y.std():.2f}, min={y.min():.2f}, max={y.max():.2f}")

    # Train model
    print("\n[2/4] Training RandomForestRegressor...")
    model = train_residual_model(X, y)

    # Feature importance
    if hasattr(model, "feature_importances_"):
        print("\n[3/4] Feature importances:")
        for name, imp in zip(FEATURE_NAMES, model.feature_importances_, strict=False):
            print(f"  {name:<20}: {imp:.4f}")

    # Save model
    model_dir = Path(__file__).parent.parent / "models"
    model_dir.mkdir(exist_ok=True)
    model_path = model_dir / "residual_model.joblib"
    joblib.dump(model, model_path)
    print(f"\n[4/4] Model saved: {model_path}")

    # Test on held-out points
    print("\n--- Test: Jupiter at J2000 ---")
    from core.kepler_hybrid import hybrid_propagate

    h = hybrid_propagate(2451545.0, "jupiter", use_ml=True)
    swiss = eph.calculate_planet("jupiter", 2451545.0)
    delta_raw = (h.kepler_lon - swiss.longitude + 180) % 360 - 180
    delta_corr = (h.corrected_lon - swiss.longitude + 180) % 360 - 180
    print(f"  Kepler residual:  {delta_raw * 60:.2f} arcmin ({delta_raw:.4f}°)")
    print(f"  ML predicted:     {h.residual_predicted_arcmin:.2f} arcmin")
    print(f"  Corrected residual: {delta_corr * 60:.2f} arcmin ({delta_corr:.4f}°)")
    print(f"  Confidence:       {h.confidence:.2f}")

    print("\n--- Test: Saturn at J2000 ---")
    h = hybrid_propagate(2451545.0, "saturn", use_ml=True)
    swiss = eph.calculate_planet("saturn", 2451545.0)
    delta_raw = (h.kepler_lon - swiss.longitude + 180) % 360 - 180
    delta_corr = (h.corrected_lon - swiss.longitude + 180) % 360 - 180
    print(f"  Kepler residual:  {delta_raw * 60:.2f} arcmin ({delta_raw:.4f}°)")
    print(f"  ML predicted:     {h.residual_predicted_arcmin:.2f} arcmin")
    print(f"  Corrected residual: {delta_corr * 60:.2f} arcmin ({delta_corr:.4f}°)")
    print(f"  Confidence:       {h.confidence:.2f}")

    # Final message
    final_rmse = abs(y.std())  # naive baseline
    print(f"\n{'=' * 60}")
    print("✅ Training complete!")
    print(f"   Baseline (naive mean): {final_rmse:.2f} arcmin RMSE")
    print(f"   Model file: {model_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

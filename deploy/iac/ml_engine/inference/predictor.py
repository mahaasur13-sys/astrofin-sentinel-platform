#!/usr/bin/env python3
"""
Predictor — online inference wrapper for all ML models.
Handles feature construction, model loading, and risk computation.
<10ms latency target.
"""

import logging
import pickle
from pathlib import Path

from feature_pipeline import FeatureBuilder

logger = logging.getLogger(__name__)


class Predictor:
    def __init__(
        self,
        failure_model_path: Path | None = None,
        load_model_path: Path | None = None,
        failure_threshold: float = 0.5,
        risk_coefficients: dict[str, float] | None = None,
    ):
        self.failure_threshold = failure_threshold
        self.risk_coefficients = risk_coefficients or {
            "failure_weight": 0.6,
            "load_weight": 0.3,
            "queue_weight": 0.1,
        }

        self._failure_model = None
        self._load_model = None
        self._feature_builder = FeatureBuilder()

        if failure_model_path and failure_model_path.exists():
            with open(failure_model_path, "rb") as f:
                self._failure_model = pickle.load(f)

        if load_model_path and load_model_path.exists():
            with open(load_model_path, "rb") as f:
                self._load_model = pickle.load(f)

    def predict(
        self,
        node_id: str,
        features: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """
        Online inference for a single node.

        Args:
            node_id: target node
            features: optional pre-computed features (fetched from TSDB if None)

        Returns:
            {
                "failure_probability": float,
                "load_forecast_queue": float,
                "load_forecast_gpu": float,
                "risk_score": float,         # 0-1, high = dangerous
                "recommendation": str,       # "schedule", "defer", "reject"
                "model_version": str,
            }
        """
        if features is None:
            features = self._fetch_features(node_id)

        if not features:
            return self._default_prediction(node_id)

        import pandas as pd

        X = pd.DataFrame([features])

        failure_prob = 0.0
        if self._failure_model is not None:
            try:
                failure_prob = float(self._failure_model.predict_proba(X)[0])
            except Exception as e:
                logger.warning(f"Failure prediction failed: {e}")

        load_forecast = {"queue": 0.0, "gpu": 0.0}
        if self._load_model is not None:
            try:
                load_pred = self._load_model.predict(X)
                load_forecast["queue"] = float(load_pred.get("queue_depth", [0.0])[0])
                load_forecast["gpu"] = float(load_pred.get("gpu_util", [0.0])[0])
            except Exception as e:
                logger.warning(f"Load prediction failed: {e}")

        risk_score = self._compute_risk(failure_prob, load_forecast)
        recommendation = self._recommend(risk_score, load_forecast)

        return {
            "failure_probability": round(failure_prob, 4),
            "load_forecast_queue": round(load_forecast["queue"], 4),
            "load_forecast_gpu": round(load_forecast["gpu"], 4),
            "risk_score": round(risk_score, 4),
            "recommendation": recommendation,
            "model_version": "v1",
        }

    def predict_batch(self, node_ids: list[str]) -> dict[str, dict[str, float]]:
        """Batch inference for multiple nodes."""
        return {node_id: self.predict(node_id) for node_id in node_ids}

    def _fetch_features(self, node_id: str) -> dict[str, float]:
        """Fetch latest features for node from TimescaleDB."""
        try:
            vectors = self._feature_builder.build_batch(
                node_ids=[node_id],
                window_type="5m",
            )
            if vectors.empty:
                return {}
            row = vectors.sort_values("time", ascending=False).iloc[0]
            return {
                c: float(row[c])
                for c in row.index
                if c not in ("time", "node_id") and isinstance(row[c], (int, float))
            }
        except Exception as e:
            logger.warning(f"Feature fetch failed for {node_id}: {e}")
            return {}

    def _compute_risk(
        self, failure_prob: float, load_forecast: dict[str, float]
    ) -> float:
        """Compute composite risk score from predictions."""
        w = self.risk_coefficients
        load_penalty = min(
            1.0, (load_forecast["gpu"] + load_forecast["queue"] / 10.0) / 2.0
        )
        risk = (
            w["failure_weight"] * failure_prob
            + w["load_weight"] * load_penalty
            + w["queue_weight"] * min(1.0, load_forecast["queue"] / 10.0)
        )
        return min(1.0, max(0.0, risk))

    def _recommend(self, risk_score: float, load_forecast: dict[str, float]) -> str:
        """Decision recommendation based on risk."""
        if risk_score < 0.3:
            return "schedule"
        if risk_score < 0.6:
            return "defer"
        return "reject"

    def _default_prediction(self, node_id: str) -> dict[str, float]:
        return {
            "failure_probability": 0.0,
            "load_forecast_queue": 0.0,
            "load_forecast_gpu": 0.0,
            "risk_score": 0.0,
            "recommendation": "schedule",
            "model_version": "fallback",
        }

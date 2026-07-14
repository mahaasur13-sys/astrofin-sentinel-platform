#!/usr/bin/env python3
"""
Failure Prediction Model — XGBoost classifier.
P(failure | node_features, horizon).
"""
import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FailureXGBoost:
    def __init__(
        self,
        max_depth: int = 6,
        n_estimators: int = 200,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        scale_pos_weight: float = 5.0,
        random_state: int = 42,
    ):
        self.max_depth = max_depth
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.scale_pos_weight = scale_pos_weight
        self.random_state = random_state
        self._model: Any | None = None
        self._feature_names: list | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "FailureXGBoost":
        """Train XGBoost failure classifier."""
        try:
            import xgboost as xgb
        except ImportError:
            logger.error("xgboost not installed — run: pip install xgboost")
            raise

        self._feature_names = list(X.columns)

        self._model = xgb.XGBClassifier(
            max_depth=self.max_depth,
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            scale_pos_weight=self.scale_pos_weight,
            random_state=self.random_state,
            use_label_encoder=False,
            eval_metric="aucpr",
            verbosity=0,
        )

        self._model.fit(X, y)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return P(failure) per sample."""
        if self._model is None:
            raise RuntimeError("Model not trained — call fit() first")
        return self._model.predict_proba(X)[:, 1]

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Binary prediction at given threshold."""
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)

    def feature_importance(self) -> dict[str, float]:
        """Return feature importance scores."""
        if self._model is None:
            raise RuntimeError("Model not trained")
        importance = self._model.feature_importances_
        return dict(zip(self._feature_names, importance))

    def get_params(self) -> dict[str, Any]:
        return {
            "max_depth": self.max_depth,
            "n_estimators": self.n_estimators,
            "learning_rate": self.learning_rate,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "scale_pos_weight": self.scale_pos_weight,
        }

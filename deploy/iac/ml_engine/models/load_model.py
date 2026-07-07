#!/usr/bin/env python3
"""
Load Prediction Model — XGBoost regressor.
Predicts: queue_depth(t+10m), gpu_util(t+15m), memory_util(t+15m).
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class LoadXGBoost:
    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 6,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self._models: dict[str, Any] = {}
        self._feature_names: list | None = None

    def fit(
        self, X: pd.DataFrame, y_queue: pd.Series, y_gpu: pd.Series, y_mem: pd.Series | None = None
    ) -> "LoadXGBoost":
        """Train separate regressors for queue_depth, gpu_util, memory_util."""
        try:
            import xgboost as xgb
        except ImportError:
            logger.error("xgboost not installed")
            raise

        self._feature_names = list(X.columns)

        self._models["queue_depth"] = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            verbosity=0,
        )
        self._models["queue_depth"].fit(X, y_queue)

        self._models["gpu_util"] = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            verbosity=0,
        )
        self._models["gpu_util"].fit(X, y_gpu)

        if y_mem is not None and not y_mem.isna().all():
            self._models["memory_util"] = xgb.XGBRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                subsample=self.subsample,
                colsample_bytree=self.colsample_bytree,
                random_state=self.random_state,
                verbosity=0,
            )
            self._models["memory_util"].fit(X, y_mem)

        return self

    def predict(self, X: pd.DataFrame) -> dict[str, np.ndarray]:
        """Return predictions for all targets."""
        if not self._models:
            raise RuntimeError("No models trained — call fit() first")
        return {name: model.predict(X) for name, model in self._models.items()}

    def predict_queue(self, X: pd.DataFrame) -> np.ndarray:
        return self._models["queue_depth"].predict(X)

    def predict_gpu(self, X: pd.DataFrame) -> np.ndarray:
        return self._models["gpu_util"].predict(X)

    def predict_memory(self, X: pd.DataFrame) -> np.ndarray:
        return self._models["memory_util"].predict(X)

    def feature_importance(self) -> dict[str, dict[str, float]]:
        return {name: dict(zip(self._feature_names, m.feature_importances_)) for name, m in self._models.items()}

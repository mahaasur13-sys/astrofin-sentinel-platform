#!/usr/bin/env python3
"""
Trainer — batch training loop for all ML models.
Produces failure + load models, logs to registry.
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from ml_engine.dataset import DatasetBuilder, time_aware_split
from ml_engine.models import FailureXGBoost, LoadXGBoost
from ml_engine.registry import ModelRegistry

logger = logging.getLogger(__name__)


class Trainer:
    def __init__(
        self,
        registry_path: Path | None = None,
        dataset_days: int = 30,
        horizon_minutes: int = 30,
    ):
        self.dataset_builder = DatasetBuilder()
        self.registry = ModelRegistry(registry_path)
        self.dataset_days = dataset_days
        self.horizon_minutes = horizon_minutes

    def train(
        self,
        output_dir: Path | None = None,
        retrain: bool = False,
        min_positive_ratio: float = 0.05,
    ) -> dict[str, str]:
        """
        Full training pipeline: build → split → train → evaluate → register.

        Returns:
            Dict of model_name → version_id
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=self.dataset_days)

        logger.info(f"Building dataset: {self.dataset_days} days of history")
        df = self.dataset_builder.build(
            start_time=start_time,
            end_time=end_time,
            horizon_minutes=self.horizon_minutes,
        )

        if df.empty:
            logger.error("No training data — aborting")
            return {}

        # Feature columns (exclude metadata + label columns)
        exclude_cols = {"time", "node_id", "time_bucket", "label_bucket",
                       "label_failure", "label_queue_depth", "label_gpu_util"}
        feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in (np.float64, np.int64)]
        X = df[feature_cols].fillna(0)
        y_failure = df["label_failure"].fillna(0).astype(int)
        y_queue = df["label_queue_depth"].fillna(0)
        y_gpu = df["label_gpu_util"].fillna(0)

        # Time-aware split
        train_df, val_df, test_df = time_aware_split(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
        X_train, _X_val, X_test = X.loc[train_df.index], X.loc[val_df.index], X.loc[test_df.index]
        yf_train, _yf_val, yf_test = y_failure.loc[train_df.index], y_failure.loc[val_df.index], y_failure.loc[test_df.index]
        yq_train, _yq_val, yq_test = y_queue.loc[train_df.index], y_queue.loc[val_df.index], y_queue.loc[test_df.index]
        yg_train, _yg_val, yg_test = y_gpu.loc[train_df.index], y_gpu.loc[val_df.index], y_gpu.loc[test_df.index]

        registered = {}

        # Train Failure Model
        logger.info("Training failure model (XGBoost)...")
        failure_model = FailureXGBoost()
        failure_model.fit(X_train, yf_train)

        from ml_engine.training.evaluate import evaluate_classifier, evaluate_regressor
        failure_metrics = evaluate_classifier(failure_model, X_test, yf_test)
        logger.info(f"Failure model — AUC: {failure_metrics['test_auc']:.4f}")

        if output_dir:
            import pickle
            model_path = output_dir / "failure_model.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(failure_model, f)
            version_id = self.registry.register(
                model_name="failure_xgb",
                model_file=model_path,
                params=failure_model.get_params(),
                metrics=failure_metrics,
                feature_names=feature_cols,
                train_rows=len(X_train),
                dataset_version=f"v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            )
            registered["failure_xgb"] = version_id

        # Train Load Model
        logger.info("Training load model (XGBoost)...")
        load_model = LoadXGBoost()
        load_model.fit(X_train, yq_train, yg_train)

        load_metrics = evaluate_regressor(load_model, X_test, yq_test, y_gpu_test=yg_test)
        logger.info(f"Load model — Queue MAE: {load_metrics['queue_mae']:.4f}, GPU MAE: {load_metrics['gpu_mae']:.4f}")

        if output_dir:
            import pickle
            model_path = output_dir / "load_model.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(load_model, f)
            version_id = self.registry.register(
                model_name="load_xgb",
                model_file=model_path,
                params=load_model.__dict__,
                metrics=load_metrics,
                feature_names=feature_cols,
                train_rows=len(X_train),
                dataset_version=f"v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            )
            registered["load_xgb"] = version_id

        return registered

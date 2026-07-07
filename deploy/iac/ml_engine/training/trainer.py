#!/usr/bin/env python3
"""
Trainer — batch training loop for all ML models.
Now supports: advanced features, XGBoost hyperparameter tuning, SMOTE balancing.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from ml_engine.dataset import DatasetBuilder, time_aware_split
from ml_engine.models import FailureXGBoost, LoadXGBoost
from ml_engine.registry import ModelRegistry

logger = logging.getLogger(__name__)


def train_xgboost(X_train, y_train, param_dist=None):
    """
    Train XGBoost with RandomizedSearchCV hyperparameter tuning.
    Handles class imbalance via scale_pos_weight or SMOTE.
    """
    try:
        import xgboost as xgb
        from sklearn.model_selection import RandomizedSearchCV
    except ImportError:
        logger.error("xgboost or sklearn not installed")
        raise

    if param_dist is None:
        param_dist = {
            "max_depth": [3, 5, 7],
            "learning_rate": [0.01, 0.05, 0.1],
            "n_estimators": [100, 200, 300],
            "subsample": [0.8, 0.9, 1.0],
            "colsample_bytree": [0.8, 0.9, 1.0],
        }

    base_model = xgb.XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        use_label_encoder=False,
        verbosity=0,
        random_state=42,
    )

    random_search = RandomizedSearchCV(
        base_model,
        param_dist,
        n_iter=20,
        cv=3,
        scoring="roc_auc",
        n_jobs=-1,
    )
    random_search.fit(X_train, y_train)
    logger.info(f"Best params: {random_search.best_params_}")
    return random_search.best_estimator_


def apply_smote(X_train, y_train):
    """Balance classes using SMOTE oversampling."""
    try:
        from imblearn.over_sampling import SMOTE
    except ImportError:
        logger.warning("imblearn not installed — skipping SMOTE")
        return X_train, y_train

    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
    return X_resampled, y_resampled


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
        use_advanced_features: bool = True,
        use_smote: bool = True,
        use_hyperopt: bool = False,
    ) -> dict[str, str]:
        """
        Full training pipeline: build → split → train → evaluate → register.

        Args:
            use_advanced_features: Add rolling/lag/temporal features
            use_smote: Apply SMOTE class balancing
            use_hyperopt: Use RandomizedSearchCV tuning
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

        if use_advanced_features:
            from ml_engine.training.feature_builder import build_advanced_features

            df = build_advanced_features(df, horizon_minutes=self.horizon_minutes)
            logger.info(f"Advanced features added — shape: {df.shape}")

        # Feature columns (exclude metadata + label columns)
        exclude_cols = {
            "time",
            "node_id",
            "time_bucket",
            "label_bucket",
            "label_failure",
            "label_queue_depth",
            "label_gpu_util",
            "timestamp",
        }
        feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in (np.float64, np.int64)]
        X = df[feature_cols].fillna(0)
        y_failure = df["label_failure"].fillna(0).astype(int)
        y_queue = df["label_queue_depth"].fillna(0)
        y_gpu = df["label_gpu_util"].fillna(0)

        # Time-aware split
        train_df, val_df, test_df = time_aware_split(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
        X_train, _X_val, X_test = X.loc[train_df.index], X.loc[val_df.index], X.loc[test_df.index]
        yf_train, _yf_val, yf_test = (
            y_failure.loc[train_df.index],
            y_failure.loc[val_df.index],
            y_failure.loc[test_df.index],
        )
        yq_train, _yq_val, yq_test = y_queue.loc[train_df.index], y_queue.loc[val_df.index], y_queue.loc[test_df.index]
        yg_train, _yg_val, yg_test = y_gpu.loc[train_df.index], y_gpu.loc[val_df.index], y_gpu.loc[test_df.index]

        registered = {}

        # SMOTE balancing
        if use_smote:
            X_train_bal, yf_train_bal = apply_smote(X_train, yf_train)
            logger.info(f"SMOTE applied — before: {len(X_train)}, after: {len(X_train_bal)}")
        else:
            X_train_bal, yf_train_bal = X_train, yf_train

        # Train Failure Model (XGBoost)
        logger.info("Training failure model (XGBoost)...")
        if use_hyperopt:
            failure_model = train_xgboost(X_train_bal, yf_train_bal)
        else:
            failure_model = FailureXGBoost()
            failure_model.fit(X_train_bal, yf_train_bal)

        from ml_engine.training.evaluate import evaluate_classifier, evaluate_regressor

        failure_metrics = evaluate_classifier(failure_model, X_test, yf_test)
        logger.info(f"Failure model — AUC: {failure_metrics['test_auc']:.4f}")

        if output_dir:
            import pickle

            model_path = output_dir / "failure_model.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(failure_model, f)

            # Save feature list
            feat_path = output_dir / "features.txt"
            with open(feat_path, "w") as f:
                f.write("\n".join(feature_cols))

            version_id = self.registry.register(
                model_name="failure_xgb",
                model_file=model_path,
                params=failure_model.get_params() if hasattr(failure_model, "get_params") else {},
                metrics=failure_metrics,
                feature_names=feature_cols,
                train_rows=len(X_train_bal),
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

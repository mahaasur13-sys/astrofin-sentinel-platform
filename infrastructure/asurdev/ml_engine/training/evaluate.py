#!/usr/bin/env python3
"""
Evaluator — metrics for classification and regression models.
Includes drift detection.
"""

import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    precision_recall_fscore_support,
    roc_auc_score,
)


def evaluate_classifier(model, X_test, y_test, threshold: float = 0.5) -> dict[str, float]:
    y_proba = model.predict_proba(X_test)
    y_pred = (y_proba >= threshold).astype(int)

    auc = roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0.0
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="binary", zero_division=0)

    return {
        "test_auc": float(auc),
        "test_precision": float(precision),
        "test_recall": float(recall),
        "test_f1": float(f1),
        "test_positive_rate": float(y_test.mean()),
    }


def evaluate_regressor(model, X_test, y_queue_test, y_gpu_test=None) -> dict[str, float]:
    yq_pred = model.predict_queue(X_test)

    metrics = {
        "queue_mae": float(mean_absolute_error(y_queue_test, yq_pred)),
        "queue_rmse": float(np.sqrt(mean_squared_error(y_queue_test, yq_pred))),
    }

    if y_gpu_test is not None:
        metrics["gpu_mae"] = float(mean_absolute_error(y_gpu_test, model.predict_gpu(X_test)))
        metrics["gpu_rmse"] = float(np.sqrt(mean_squared_error(y_gpu_test, model.predict_gpu(X_test))))

    return metrics


def detect_drift(
    train_metrics: dict[str, float],
    current_metrics: dict[str, float],
    drift_threshold: float = 0.1,
) -> bool:
    """
    Detect if model performance has drifted significantly.
    Returns True if drift detected.
    """
    for key in ["test_auc", "test_f1"]:
        if key in train_metrics and key in current_metrics:
            if abs(train_metrics[key] - current_metrics[key]) > drift_threshold:
                return True
    return False

"""
Integration test — ML Pipeline (Train → Predict → Metrics)

Tests the full stack:
    1. Synthetic dataset generation (mimics DatasetBuilder output)
    2. Train failure + load models via Trainer
    3. Register models via ModelRegistry
    4. Load models for inference
    5. POST /predict → verify risk_score in [0, 1]
    6. GET /health  → verify liveness
    7. GET /metrics → verify Prometheus format

Requires: pytest, fastapi, uvicorn, scikit-learn, xgboost, joblib, pandas, numpy
Run with: pytest tests/integration/test_ml_pipeline.py -v
"""
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── path setup ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ── test configuration ───────────────────────────────────────────────────────
SYNTHETIC_N_SAMPLES = 500
SYNTHETIC_N_FEATURES = 18
SYNTHETIC_FAILURE_RATE = 0.15  # ~15% positive class


# ─────────────────────────────────────────────────────────────────────────────
# 1. SYNTHETIC DATA GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def _generate_synthetic_dataset(
    n_samples: int = SYNTHETIC_N_SAMPLES,
    n_features: int = SYNTHETIC_N_FEATURES,
    failure_rate: float = SYNTHETIC_FAILURE_RATE,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Mimics DatasetBuilder.build() output.
    Returns a DataFrame with:
      - 18 feature columns  (cpu, mem, gpu, disk, net, slurm, proc)
      - label_failure / label_queue_depth / label_gpu_util columns
      - time + node_id metadata columns
    """
    rng = np.random.default_rng(seed)

    t_start = pd.Timestamp("2026-04-01", tz="UTC")
    time_series = pd.date_range(t_start, periods=n_samples, freq="10min")

    node_ids = rng.choice(["rtx3060-node-01", "rtx4090-node-02", "a100-node-03"], size=n_samples)

    # ── feature columns ────────────────────────────────────────────────────────
    base_features = {
        "cpu_load_1":           rng.uniform(0.05, 0.95, n_samples),
        "cpu_load_5":           rng.uniform(0.05, 0.90, n_samples),
        "mem_used_pct":         rng.uniform(10.0, 95.0, n_samples),
        "swap_used_pct":        rng.uniform(0.0, 20.0, n_samples),
        "gpu_util":             rng.uniform(0.0, 100.0, n_samples),
        "gpu_mem_used_pct":     rng.uniform(20.0, 95.0, n_samples),
        "gpu_temp":             rng.uniform(40.0, 85.0, n_samples),
        "gpu_power_draw":       rng.uniform(50.0, 350.0, n_samples),
        "disk_read_bytes_sec":  rng.uniform(0.0, 5_000_000.0, n_samples),
        "disk_write_bytes_sec": rng.uniform(0.0, 3_000_000.0, n_samples),
        "disk_usage_pct":       rng.uniform(20.0, 90.0, n_samples),
        "net_recv_bytes_sec":   rng.uniform(100_000.0, 10_000_000.0, n_samples),
        "net_send_bytes_sec":   rng.uniform(100_000.0, 5_000_000.0, n_samples),
        "slurm_queue_depth":    rng.integers(0, 50, n_samples),
        "slurm_running_jobs":   rng.integers(0, 20, n_samples),
        "num_processes":         rng.integers(50, 800, n_samples),
        "open_files":           rng.integers(500, 4000, n_samples),
        "cpu_load_15":          rng.uniform(0.05, 0.85, n_samples),
    }

    df = pd.DataFrame(base_features)

    # ── labels ───────────────────────────────────────────────────────────────
    # label_failure: correlate with high cpu/mem/gpu indicators
    stress_score = (
        df["cpu_load_1"] * 0.3
        + df["mem_used_pct"] / 100 * 0.3
        + df["gpu_util"] / 100 * 0.2
        + df["gpu_temp"] / 100 * 0.2
    )
    probs = np.clip(stress_score + rng.uniform(-0.05, 0.05, n_samples), 0, 1)
    df["label_failure"] = (probs > (1 - failure_rate)).astype(int)

    df["label_queue_depth"] = df["slurm_queue_depth"] * rng.uniform(0.8, 1.2, n_samples)
    df["label_gpu_util"] = df["gpu_util"] + rng.uniform(-5, 5, n_samples)

    # ── metadata ─────────────────────────────────────────────────────────────
    df.insert(0, "time", time_series)
    df.insert(1, "node_id", node_ids)
    df["time_bucket"] = df["time"].dt.floor("5min").astype(str)
    df["label_bucket"] = df["time_bucket"]

    return df


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def tmp_model_dir():
    """Temporary directory for model artifacts (per test module)."""
    tmp = tempfile.mkdtemp(prefix="ml_integration_")
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="module")
def synthetic_dataset():
    """Generate a synthetic dataset once per test module."""
    return _generate_synthetic_dataset()


@pytest.fixture(scope="module")
def trained_models(synthetic_dataset, tmp_model_dir):
    """
    End-to-end training: split → train failure + load models → register.
    Returns dict of model_name → model artifact path.
    """
    from ml_engine.training.trainer import Trainer
    from ml_engine.dataset.splitter import time_aware_split
    from ml_engine.models import FailureXGBoost, LoadXGBoost

    df = synthetic_dataset

    # Feature columns (exclude metadata + label columns)
    exclude_cols = {
        "time", "node_id", "time_bucket", "label_bucket",
        "label_failure", "label_queue_depth", "label_gpu_util",
    }
    feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in (np.float64, np.int64)]

    X = df[feature_cols].fillna(0)
    y_failure = df["label_failure"].fillna(0).astype(int)
    y_queue   = df["label_queue_depth"].fillna(0)
    y_gpu     = df["label_gpu_util"].fillna(0)

    train_df, val_df, test_df = time_aware_split(df)
    X_train = X.loc[train_df.index]
    X_val   = X.loc[val_df.index]
    X_test  = X.loc[test_df.index]
    yf_train, yf_val, yf_test = y_failure.loc[train_df.index], y_failure.loc[val_df.index], y_failure.loc[test_df.index]
    yq_train, yq_val, yq_test = y_queue.loc[train_df.index], y_queue.loc[val_df.index], y_queue.loc[test_df.index]
    yg_train, yg_val, yg_test = y_gpu.loc[train_df.index], y_gpu.loc[val_df.index], y_gpu.loc[test_df.index]

    # ── train failure model ───────────────────────────────────────────────────
    failure_model = FailureXGBoost()
    failure_model.fit(X_train, yf_train)
    failure_path = tmp_model_dir / "failure_xgb_v2.pkl"
    import pickle
    with open(failure_path, "wb") as f:
        pickle.dump(failure_model._model, f)   # api.py uses pickle.load()

    # ── train load model ──────────────────────────────────────────────────────
    load_model = LoadXGBoost()
    load_model.fit(
        X_train,
        y_queue=yq_train,
        y_gpu=yg_train,
        y_mem=None,
    )
    load_path = tmp_model_dir / "load_model_v1.pkl"
    with open(load_path, "wb") as f:
        pickle.dump(load_model._models["queue_depth"], f)

    # ── save feature list ─────────────────────────────────────────────────────
    features_path = tmp_model_dir / "features.txt"
    features_path.write_text("\n".join(feature_cols))

    return {
        "failure": failure_path,
        "load":    load_path,
        "features": features_path,
        "feature_cols": feature_cols,
    }


@pytest.fixture(scope="module")
def api_server(trained_models, tmp_model_dir):
    """
    Start uvicorn server with trained models in a separate process.
    Yields the base URL. Process is killed after tests complete.
    """
    import multiprocessing
    import time
    import socket

    # Write feature list where api.py expects it
    features_src = trained_models["features"]
    model_src    = trained_models["failure"]

    # Copy into expected paths inside ml_engine/models/
    models_dir = REPO_ROOT / "ml_engine" / "models"
    models_dir.mkdir(exist_ok=True)
    shutil.copy(model_src, models_dir / "failure_xgb_v2.pkl")
    shutil.copy(features_src, models_dir / "features.txt")

    # Dynamically configure ml_engine/inference/api.py env vars
    os.environ["ML_MODEL_PATH"]     = str(models_dir / "failure_xgb_v2.pkl")
    os.environ["ML_FEATURES_PATH"] = str(models_dir / "features.txt")

    def run_server():
        import uvicorn
        # Import the app factory (lazy init — model loads on startup)
        from ml_engine.inference.api import app
        uvicorn.run(app, host="127.0.0.1", port=8765, log_level="error")

    ctx = multiprocessing.get_context("spawn")
    proc = ctx.Process(target=run_server, daemon=True)
    proc.start()

    # Wait for server to be ready (max 20s)
    for _ in range(40):
        with socket.create_connection(("127.0.0.1", 8765), timeout=0.5):
            break
        time.sleep(0.5)
    else:
        proc.terminate()
        pytest.fail("ML API server failed to start within 20 seconds")

    yield "http://127.0.0.1:8765"

    proc.terminate()
    proc.join(timeout=5)


# ─────────────────────────────────────────────────────────────────────────────
# 2. API ENDPOINT TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestMLPipelineAPI:
    """End-to-end tests against the live FastAPI inference server."""

    def test_predict_returns_valid_risk_score(self, api_server):
        """POST /predict → risk_score must be float in [0.0, 1.0]."""
        import requests

        payload = {
            "node_id": "rtx3060-node-01",
            "cpu_load_1": 0.45,
            "cpu_load_5": 0.38,
            "mem_used_pct": 72.5,
            "swap_used_pct": 0.0,
            "gpu_util": 85.0,
            "gpu_mem_used_pct": 91.2,
            "gpu_temp": 67.0,
            "gpu_power_draw": 180.5,
            "disk_read_bytes_sec": 1_024_000.0,
            "disk_write_bytes_sec": 512_000.0,
            "disk_usage_pct": 55.0,
            "net_recv_bytes_sec": 1_048_576.0,
            "net_send_bytes_sec": 524_288.0,
            "slurm_queue_depth": 12,
            "slurm_running_jobs": 4,
            "num_processes": 312,
            "open_files": 1847,
        }

        resp = requests.post(f"{api_server}/predict", json=payload, timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        data = resp.json()
        assert "risk_score" in data, f"Missing 'risk_score' in response: {data}"
        rs = float(data["risk_score"])
        assert 0.0 <= rs <= 1.0, f"risk_score {rs} outside [0,1]"

    def test_predict_requires_mandatory_fields(self, api_server):
        """Missing field → 422 validation error."""
        import requests

        payload = {
            "node_id": "rtx4090-node-02",
            # cpu_load_1 missing
        }
        resp = requests.post(f"{api_server}/predict", json=payload, timeout=10)
        assert resp.status_code == 422, f"Expected 422 for missing field, got {resp.status_code}"

    def test_health_endpoint_liveness(self, api_server):
        """GET /health → 'status' must be 'healthy'."""
        import requests

        resp = requests.get(f"{api_server}/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "healthy", f"Unexpected health status: {data}"

    def test_metrics_endpoint_prometheus_format(self, api_server):
        """GET /metrics → must contain '# HELP' and '# TYPE' markers."""
        import requests

        resp = requests.get(f"{api_server}/metrics", timeout=10)
        assert resp.status_code == 200
        text = resp.text
        # Prometheus exposition format
        assert "# HELP" in text or "ml_inference" in text, \
            f"Response does not look like Prometheus format: {text[:300]}"

    def test_root_endpoint_info(self, api_server):
        """GET / → must return JSON with at least a 'version' field."""
        import requests

        resp = requests.get(f"{api_server}/", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict), f"Root endpoint should return a dict, got {type(data)}"


# ─────────────────────────────────────────────────────────────────────────────
# 3. MODEL QUALITY TESTS
# ─────────────────────────────────────────────────────────────────────────────
class TestModelQuality:
    """Validate that trained models meet minimum quality thresholds."""

    def test_failure_model_auc_on_holdout(self, synthetic_dataset, trained_models):
        """Trained failure model must achieve AUC >= 0.60 on hold-out set."""
        from sklearn.metrics import roc_auc_score
        import pickle

        df = synthetic_dataset
        exclude_cols = {
            "time", "node_id", "time_bucket", "label_bucket",
            "label_failure", "label_queue_depth", "label_gpu_util",
        }
        feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in (np.float64, np.int64)]
        X = df[feature_cols].fillna(0)
        y = df["label_failure"].fillna(0).astype(int)

        from ml_engine.dataset.splitter import time_aware_split
        _, _, test_df = time_aware_split(df)
        X_test = X.loc[test_df.index]
        y_test = y.loc[test_df.index]

        with open(trained_models["failure"], "rb") as f:
            xgb_model = pickle.load(f)
        y_pred_proba = xgb_model.predict_proba(X_test)[:, 1]

        auc = roc_auc_score(y_test, y_pred_proba)
        logging.getLogger().info(f"Failure model AUC on holdout: {auc:.4f}")
        assert auc >= 0.60, f"AUC {auc:.4f} below minimum threshold 0.60"

    def test_load_model_rmse_on_holdout(self, synthetic_dataset, trained_models):
        """Trained load model must achieve RMSE <= 10.0 on hold-out set."""
        from sklearn.metrics import mean_squared_error
        import pickle

        df = synthetic_dataset
        exclude_cols = {
            "time", "node_id", "time_bucket", "label_bucket",
            "label_failure", "label_queue_depth", "label_gpu_util",
        }
        feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in (np.float64, np.int64)]
        X = df[feature_cols].fillna(0)
        y = df["label_queue_depth"].fillna(0)

        from ml_engine.dataset.splitter import time_aware_split
        _, _, test_df = time_aware_split(df)
        X_test = X.loc[test_df.index]
        y_test = y.loc[test_df.index]

        with open(trained_models["load"], "rb") as f:
            xgb_regressor = pickle.load(f)
        y_pred = xgb_regressor.predict(X_test)

        rmse = mean_squared_error(y_test, y_pred, squared=False)
        logging.getLogger().info(f"Load model RMSE on holdout: {rmse:.4f}")
        assert rmse <= 10.0, f"RMSE {rmse:.4f} above maximum threshold 10.0"

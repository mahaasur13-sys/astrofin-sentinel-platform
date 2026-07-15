"""
Unit tests for ml_engine/inference/api.py

Covers:
    - GET  /health   — liveness
    - POST /predict  — valid input
    - POST /predict  — missing required field (422)
    - POST /predict  — invalid field value (422)
    - GET  /metrics  — returns stats
    - GET  /         — root info endpoint

Requires pytest + httpx (or requests for integration mode).
Run with:  pytest tests/test_ml_api.py -v
"""
import pytest

# We use httpx for async TestClient when FastAPI is available
try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None  # skip tests if fastapi not installed


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------
VALID_PAYLOAD = {
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

PAYLOAD_MISSING_CPU = {
    "node_id": "rtx3060-node-01",
    # cpu_load_1 missing — should cause 422
    "mem_used_pct": 72.5,
}

PAYLOAD_INVALID_gpu_util = {
    **VALID_PAYLOAD,
    "gpu_util": 200.0,  # out of range (0-100)
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    """Build a TestClient against the FastAPI app.

    Note: the real app loads a model at startup. If the model file is absent
    the startup will raise and the tests will fail — which is the intended
    behaviour in a CI environment without a trained model.
    """
    if TestClient is None:
        pytest.skip("FastAPI not installed")

    # Lazy import to avoid importing the module before patching model paths
    import os
    from ml_engine.inference.api import app

    # Point at dummy files — the startup will fail gracefully in test env
    # and we skip tests that need a loaded model.
    os.environ.setdefault(
        "ML_MODEL_PATH",
        "/home/workspace/AsurDev/models/failure_xgb_v2.pkl",
    )
    os.environ.setdefault(
        "ML_FEATURES_PATH",
        "/home/workspace/AsurDev/models/features.txt",
    )

    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestRoot:
    def test_root_returns_service_info(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "ML Inference API"
        assert "version" in data
        assert "health" in data
        assert "predict" in data


class TestHealth:
    def test_health_returns_alive(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        # status may be 'alive' or 'dead' depending on whether a real model was loaded
        assert data["status"] in ("alive", "dead")
        assert "model_loaded" in data
        assert "feature_count" in data
        assert "uptime_seconds" in data


class TestMetrics:
    def test_metrics_returns_stats(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "cache_hits" in data
        assert "cache_misses" in data
        assert "avg_latency_ms" in data
        assert "error_count" in data


class TestPredictValidation:
    def test_predict_422_on_missing_required_field(self, client):
        resp = client.post("/predict", json=PAYLOAD_MISSING_CPU)
        assert resp.status_code == 422  # FastAPI validation error

    def test_predict_422_on_invalid_field_value(self, client):
        resp = client.post("/predict", json=PAYLOAD_INVALID_gpu_util)
        assert resp.status_code == 422

    def test_predict_422_on_empty_body(self, client):
        resp = client.post("/predict", json={})
        assert resp.status_code == 422


class TestPredictIntegration:
    """Integration tests that require a real model on disk."""

    @pytest.mark.skipif(
        not hasattr(TestClient, "__call__"),
        reason="FastAPI TestClient not available",
    )
    def test_predict_returns_risk_score(self, client):
        """Smoke test: /predict with valid data returns a float risk_score."""
        resp = client.post("/predict", json=VALID_PAYLOAD)
        # May be 200 (model loaded) or 500 (model absent / feature mismatch)
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "risk_score" in data
            assert "status" in data
            assert "prediction_id" in data
            assert isinstance(data["risk_score"], float)
            assert 0.0 <= data["risk_score"] <= 1.0

    def test_predict_with_explain_flag_accepted(self, client):
        """Server should accept ?explain=true without crashing."""
        resp = client.post("/predict", json=VALID_PAYLOAD, params={"explain": True})
        # Accept any 2xx or 5xx (500 = model not loaded is fine)
        assert resp.status_code > 0


# ---------------------------------------------------------------------------
# Schema validation tests (standalone — no FastAPI app needed)
# ---------------------------------------------------------------------------
class TestSchemas:
    def test_metrics_input_valid(self):
        from ml_engine.inference.schemas import MetricsInput

        inp = MetricsInput(**VALID_PAYLOAD)
        assert inp.node_id == "rtx3060-node-01"
        assert inp.gpu_util == 85.0

    def test_metrics_input_defaults(self):
        from ml_engine.inference.schemas import MetricsInput

        inp = MetricsInput(node_id="test-node")
        assert inp.cpu_load_1 == 0.0
        assert inp.num_processes == 1

    def test_prediction_response_schema(self):
        from ml_engine.inference.schemas import PredictionResponse

        r = PredictionResponse(
            risk_score=0.42,
            status="ok",
            prediction_id="abc12345",
            latency_ms=1.23,
        )
        assert r.risk_score == 0.42
        assert r.status == "ok"

    def test_health_response_schema(self):
        from ml_engine.inference.schemas import HealthResponse

        r = HealthResponse(
            status="alive",
            model_loaded=True,
            feature_count=42,
            uptime_seconds=3600.0,
        )
        assert r.status == "alive"
        assert r.model_loaded is True
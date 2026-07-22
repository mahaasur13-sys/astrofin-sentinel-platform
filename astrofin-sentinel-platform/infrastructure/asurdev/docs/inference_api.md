# ML Inference API — Real-time Failure Risk Scoring

## Overview

Production FastAPI service that loads an XGBoost model trained with advanced features (rolling/lag/temporal) and exposes:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Returns `risk_score` ∈ [0, 1] |
| `/explain/{id}` | GET | SHAP explanations for a past prediction |
| `/health` | GET | Liveness probe |
| `/metrics` | GET | Application metrics (JSON) |
| `/prometheus` | GET | Prometheus scrape endpoint |
| `/` | GET | Service info + links |

---

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
# or
pip install -e .
```

### 2. Set model paths

```bash
export ML_MODEL_PATH=models/failure_xgb_v2.pkl
export ML_FEATURES_PATH=models/features.txt
```

### 3. Run locally

```bash
# Development (auto-reload)
make ml-api-run

# Production (gunicorn, 4 workers)
make ml-api-run-prod
```

### 4. Test

```bash
make ml-api-test
```

---

## API usage

### POST /predict

**Request:**
```json
{
  "node_id": "rtx3060-node-01",
  "cpu_load_1": 0.45,
  "cpu_load_5": 0.38,
  "mem_used_pct": 72.5,
  "swap_used_pct": 0.0,
  "gpu_util": 85.0,
  "gpu_mem_used_pct": 91.2,
  "gpu_temp": 67.0,
  "gpu_power_draw": 180.5,
  "disk_read_bytes_sec": 1024000.0,
  "disk_write_bytes_sec": 512000.0,
  "disk_usage_pct": 55.0,
  "net_recv_bytes_sec": 1048576.0,
  "net_send_bytes_sec": 524288.0,
  "slurm_queue_depth": 12,
  "slurm_running_jobs": 4,
  "num_processes": 312,
  "open_files": 1847
}
```

**Response:**
```json
{
  "risk_score": 0.73,
  "status": "ok",
  "prediction_id": "a1b2c3d4",
  "explain_url": "/explain/a1b2c3d4",
  "latency_ms": 4.2
}
```

**With SHAP explanations:** `POST /predict?explain=true`

### GET /explain/{prediction_id}

```json
{
  "prediction_id": "a1b2c3d4",
  "risk_score": 0.73,
  "shap_values": {
    "gpu_util_lag1": 0.21,
    "cpu_load_rolling_std_5": 0.15,
    "mem_used_pct": -0.08
  },
  "feature_importance": { "gpu_util_lag1": 0.21, "cpu_load_rolling_std_5": 0.15 },
  "top_positive_features": ["gpu_util_lag1", "cpu_load_rolling_std_5"],
  "top_negative_features": ["mem_used_pct"]
}
```

### GET /health

```json
{
  "status": "alive",
  "model_loaded": true,
  "feature_count": 42,
  "model_version": "models/failure_xgb_v2.pkl",
  "uptime_seconds": 86400.0
}
```

---

## Configuration

| Environment variable | Default | Description |
|---------------------|---------|-------------|
| `ML_MODEL_PATH` | `models/failure_xgb_v2.pkl` | Path to pickled XGBoost model |
| `ML_FEATURES_PATH` | `models/features.txt` | Path to newline-separated feature list |
| `ML_API_BASE` | `http://localhost:8081` | Base URL for `ml_client` (scheduler) |
| `ML_API_TIMEOUT` | `0.5` | Timeout (seconds) for scheduler → API calls |
| `ML_CB_FAILURES` | `5` | Circuit breaker threshold |
| `ML_CB_RECOVERY_S` | `30` | Circuit breaker recovery cooldown |

---

## Docker

```bash
make ml-api-docker-build   # Build image
make ml-api-docker-run     # Run container (detached, port 8081)
make ml-api-docker-stop    # Stop and remove container
```

Container includes healthcheck (`/health`) and runs as non-root user (`acos`).

---

## Systemd

```bash
sudo cp ml_engine/inference/ml-inference.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ml-inference
sudo journalctl -u ml-inference -f   # follow logs
```

---

## Integration with scheduler_v3

The `scheduler_v3/scorer.py` uses `ml_client.get_risk_score()`:

```python
from ml_engine.inference.ml_client import get_risk_score

score = get_risk_score({
    "node_id": "rtx3060-node-01",
    "cpu_load_1": 0.45,
    "gpu_util": 85.0,
    "mem_used_pct": 72.5,
    ...
})
# Returns float in [0.0, 1.0], or 0.0 on any error (fail-safe)
```

Key behaviour:
- **Circuit breaker** — after 5 failures within 30 s returns `0.0`
- **Timeout 0.5 s** — scheduler never waits more than 500 ms for a decision
- **Fail-safe** — any API error → `0.0` (job is accepted, not blocked)

---

## End-to-end flow

```
scheduler_v3
    │
    ▼
ml_client.get_risk_score(metrics)
    │ HTTP POST /predict
    ▼
ml_engine.inference.api (FastAPI / uvicorn)
    │
    ├── build_advanced_features(raw_metrics)   ← from training/feature_builder.py
    ├── predict_proba()                        ← XGBoost model
    └── return { "risk_score": 0.73 }
    │
    ▼
scheduler decides: block if risk_score > threshold
```

---

## Makefile targets

| Target | Description |
|--------|-------------|
| `ml-api-install` | Install dependencies |
| `ml-api-run` | Run with uvicorn (dev, auto-reload) |
| `ml-api-run-prod` | Run with gunicorn (4 workers) |
| `ml-api-stop` | Kill uvicorn/gunicorn process |
| `ml-api-test` | Run pytest |
| `ml-api-docker-build` | Build Docker image |
| `ml-api-docker-run` | Run container (detached) |
| `ml-api-docker-stop` | Stop and remove container |
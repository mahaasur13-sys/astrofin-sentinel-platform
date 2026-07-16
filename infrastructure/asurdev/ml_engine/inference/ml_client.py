"""
ML Inference Client — thin wrapper around the /predict API.

Used by any component that needs a risk_score without importing the full API app.
Includes circuit-breaker behaviour: on API error → falls back to 0.0.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

logger = logging.getLogger("ml_client")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_API_BASE = os.environ.get("ML_API_BASE", "http://localhost:8081")
_API_TIMEOUT = float(os.environ.get("ML_API_TIMEOUT", "0.5"))  # seconds
_CB_FAILURE_THRESHOLD = int(os.environ.get("ML_CB_FAILURES", "5"))
_CB_RECOVERY_TIMEOUT = int(os.environ.get("ML_CB_RECOVERY_S", "30"))


# ---------------------------------------------------------------------------
# Circuit breaker state
# ---------------------------------------------------------------------------
_cb_failures = 0
_cb_last_failure: float = 0.0
_cb_open_since: float = 0.0


def _is_circuit_open() -> bool:
    global _cb_failures, _cb_open_since
    if _cb_failures < _CB_FAILURE_THRESHOLD:
        return False
    # Try to recover after cooldown
    if time.time() - _cb_open_since > _CB_RECOVERY_TIMEOUT:
        logger.info("ML API circuit breaker: recovery attempt")
        _cb_failures = 0
        return False
    return True


def get_risk_score(metrics: dict[str, Any], timeout: float | None = None) -> float:
    """
    Call POST /predict on the ML Inference API and return risk_score.

    Args:
        metrics:  dict with raw system metrics (node_id, cpu_load_1, gpu_util, …)
        timeout:  request timeout override (default 0.5 s)

    Returns:
        risk_score: float in [0.0, 1.0], or 0.0 on any error (fail-safe).

    Behaviour:
        - Circuit breaker: after _CB_FAILURE_THRESHOLD failures the API is skipped
          for _CB_RECOVERY_TIMEOUT seconds (fail-safe).
        - On network/timeout error: logs warning and returns 0.0.
    """
    global _cb_failures, _cb_last_failure, _cb_open_since

    if _is_circuit_open():
        logger.warning("ML API circuit open — returning 0.0")
        return 0.0

    url = f"{_API_BASE}/predict"
    tm = timeout if timeout is not None else _API_TIMEOUT

    try:
        resp = requests.post(url, json=metrics, timeout=tm)
        if resp.status_code == 200:
            data = resp.json()
            score = float(data["risk_score"])
            # Reset circuit on success
            if _cb_failures > 0:
                logger.info("ML API circuit breaker: recovered after %d failures", _cb_failures)
                _cb_failures = 0
            return score
        else:
            _record_failure()
            logger.warning("ML API /predict returned %d — treating as 0.0", resp.status_code)
            return 0.0

    except requests.Timeout:
        _record_failure()
        logger.warning("ML API /predict timed out after %.1fs — returning 0.0", tm)
        return 0.0

    except requests.ConnectionError:
        _record_failure()
        logger.warning("ML API unreachable at %s — returning 0.0", url)
        return 0.0

    except Exception as exc:
        _record_failure()
        logger.error("Unexpected ML API error: %s — returning 0.0", exc)
        return 0.0


def _record_failure() -> None:
    global _cb_failures, _cb_last_failure, _cb_open_since
    _cb_failures += 1
    _cb_last_failure = time.time()
    if _cb_failures == _CB_FAILURE_THRESHOLD:
        _cb_open_since = _cb_last_failure
        logger.error("ML API circuit breaker OPEN — will retry in %ds", _CB_RECOVERY_TIMEOUT)


def health_check() -> bool:
    """Return True if the ML API is reachable."""
    try:
        resp = requests.get(f"{_API_BASE}/health", timeout=1.0)
        return resp.status_code == 200 and resp.json().get("status") == "alive"
    except Exception:
        return False

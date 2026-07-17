"""RegimeDetector — HMM-based market regime annotation for backtests.

Fits ONE GaussianHMM on the full training history, then uses Viterbi
to label every bar with bull/sideways/bear.  Log-likelihood on a
trailing window detects anomalies (Safety Gate).

Design rationale:
  Sliding-window refit per bar fails on daily data because 120 bars
  do not contain enough regime transitions.  The full-history fit
  naturally captures the three market phases documented in the
  calibration log.
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)

try:
    from hmmlearn import hmm

    HAS_HMM = True
except ImportError:
    HAS_HMM = False
    hmm = None  # type: ignore[assignment]

# ── constants ──────────────────────────────────────────────────────────
_N_STATES = 3  # bull / sideways / bear
_DEFAULT_LOOKBACK = 120  # trailing bars for anomaly detection


class RegimeDetector:
    """Fit a 3-state GaussianHMM and annotate OHLCV bars."""

    def __init__(self, lookback: int = _DEFAULT_LOOKBACK, anomaly_threshold: float = -15.0) -> None:
        self._model: hmm.GaussianHMM | None = None
        self._regime_labels: List[str] = []  # per-bar
        self._log_lik: List[float] = []  # per-bar (trailing window score)
        self._anomaly_threshold: float = anomaly_threshold
        self._lookback = lookback
        self._feature_cache: np.ndarray | None = None

    # ── public API ─────────────────────────────────────────────────────

    def fit(self, ohlcv: List[dict]) -> None:
        """Fit HMM on *all* historical data and annotate every bar."""
        if not HAS_HMM:
            logger.warning("hmmlearn not available; fallback to heuristics")
            self._fallback(ohlcv)
            return

        features = self._build_features(ohlcv)
        self._feature_cache = features

        with np.errstate(invalid="ignore", divide="ignore"):
            try:
                model = hmm.GaussianHMM(
                    n_components=_N_STATES,
                    covariance_type="spherical",
                    n_iter=500,
                    tol=1e-4,
                    random_state=42,
                )
                model.fit(features)
                raw_states = model.predict(features)
            except Exception:
                logger.exception("HMM fit failed; fallback to heuristics")
                self._fallback(ohlcv)
                return

        self._model = model

        # Label states by mean return → highest = bull, lowest = bear
        closes = np.array([b["close"] for b in ohlcv])
        rets = np.diff(np.log(closes))
        state_returns = {}
        for s in range(_N_STATES):
            mask = raw_states[1:] == s
            state_returns[s] = float(np.mean(rets[mask])) if np.any(mask) else 0.0
        sorted_states = sorted(state_returns, key=state_returns.get)  # type: ignore[arg-type]
        label_map = {
            sorted_states[0]: "bear",
            sorted_states[1]: "sideways",
            sorted_states[2]: "bull",
        }
        self._regime_labels = [label_map[s] for s in raw_states]

        # Trailing log-likelihood per bar
        self._log_lik = [0.0] * self._lookback

        # Compute state→label mapping once after fit
        self._state_map_cache = self._compute_state_map()
        for i in range(self._lookback, len(ohlcv)):
            win = features[i - self._lookback : i + 1]
            try:
                ll = model.score(win)
            except Exception:
                ll = -999.0
            self._log_lik.append(float(ll))

        logger.info(
            "RegimeDetector fitted: bull=%d, sideways=%d, bear=%d bars",
            self._regime_labels.count("bull"),
            self._regime_labels.count("sideways"),
            self._regime_labels.count("bear"),
        )

    def annotate(self, idx: int) -> tuple[str, List[float], bool]:
        """Return (regime_label, probabilities, is_anomaly) for bar *idx*."""
        if idx < 0 or idx >= len(self._regime_labels):
            return ("sideways", [0.33, 0.34, 0.33], False)

        regime = self._regime_labels[idx]
        ll = self._log_lik[idx] if idx < len(self._log_lik) else 0.0
        is_anomaly = ll < self._anomaly_threshold if ll != 0.0 else False

        probs = {"bull": 0.33, "sideways": 0.34, "bear": 0.33}
        if self._model is not None and self._feature_cache is not None and idx >= 0:
            feat = self._feature_cache[idx].reshape(1, -1)
            raw_probs = self._model.predict_proba(feat)[0]
            sorted_states = self._state_map_cache if self._state_map_cache else ["bull", "sideways", "bear"]
            for s, p in enumerate(raw_probs):
                if s < len(sorted_states):
                    probs[sorted_states[s]] = float(p)

        probs_list = [probs["bull"], probs["sideways"], probs["bear"]]
        return (regime, probs_list, is_anomaly)

    # ── internal helpers ────────────────────────────────────────────────

    @staticmethod
    def _build_features(ohlcv: List[dict]) -> np.ndarray:
        closes = np.array([b["close"] for b in ohlcv])
        volumes = np.array([b.get("volume", 0) for b in ohlcv], dtype=float)
        rets = np.diff(np.log(closes))
        rets = np.concatenate([[0.0], rets])

        # 20-day rolling annualized vol
        vol_ann = np.zeros_like(closes)
        for i in range(len(closes)):
            win = rets[max(0, i - 19) : i + 1]
            vol_ann[i] = np.std(win) * np.sqrt(365) if len(win) > 1 else 0.0

        vol_rel = volumes / (np.mean(volumes) + 1e-8)

        return np.column_stack([rets, vol_ann, vol_rel])

    def _compute_state_map(self) -> List[str]:
        """Precompute state→label mapping once after fit using mean returns per state."""
        if not self._regime_labels or self._model is None or self._feature_cache is None:
            return ["bull", "sideways", "bear"]
        try:
            states = self._model.predict(self._feature_cache)
            # Compute mean return per HMM state
            rets = np.diff(np.log(np.array([1.0] + [b["close"] for b in [{"close": c} for c in [100.0] * len(self._regime_labels)]])))
            state_ret = {}
            for s in range(_N_STATES):
                mask = states == s
                if mask.sum() > 0:
                    state_ret[s] = float(np.mean(self._feature_cache[mask, 0]))
                else:
                    state_ret[s] = 0.0
            # Sort states by mean return: highest → bull, middle → sideways, lowest → bear
            sorted_states = sorted(range(_N_STATES), key=lambda s: state_ret.get(s, 0.0), reverse=True)
            label_order: list = ["sideways"] * _N_STATES
            if _N_STATES >= 3:
                label_order[sorted_states[0]] = "bull"
                label_order[sorted_states[1]] = "sideways"
                label_order[sorted_states[2]] = "bear"
            elif _N_STATES == 2:
                label_order[sorted_states[0]] = "bull"
                label_order[sorted_states[1]] = "bear"
            else:
                label_order[sorted_states[0]] = "bull"
            return label_order
        except Exception:
            return ["bull", "sideways", "bear"]

    def _fallback(self, ohlcv: List[dict]) -> None:
        """Heuristic regime detection when hmmlearn is unavailable."""
        closes = np.array([b["close"] for b in ohlcv])
        rets = np.diff(np.log(closes))
        self._regime_labels = ["sideways" for _ in ohlcv]
        self._log_lik = [0.0 for _ in ohlcv]
        for i in range(1, len(ohlcv)):
            win = rets[max(0, i - 20) : i]
            mean_r = np.mean(win) if len(win) > 0 else 0.0
            std_r = np.std(win) if len(win) > 1 else 0.01
            if mean_r > 0.001 and std_r < 0.03:
                self._regime_labels[i] = "bull"
            elif mean_r < -0.001 and std_r > 0.025:
                self._regime_labels[i] = "bear"
            self._log_lik.append(-999.0 if abs(win[-1]) > 3 * std_r else 0.0)

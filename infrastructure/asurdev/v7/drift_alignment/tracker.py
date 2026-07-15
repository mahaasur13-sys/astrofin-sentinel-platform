#!/usr/bin/env python3
"""
Triple Drift Alignment System — detects and reacts to feature/model/system drift.
Signals: feature drift, model drift, system drift.
Drift_Alignment = corr(f1, f2, f3)

Reaction:
  low alignment → retrain v5
  medium → adjust weights
  high → stable mode
"""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import pearsonr


@dataclass
class DriftSignals:
    """Three orthogonal drift signals."""
    feature_drift_score: float   # 0-1, Kolmogorov-Smirnov on features
    model_error_rate: float      # 0-1, prediction error vs actual
    system_drift_score: float    # 0-1, simulated vs actual divergence
    measured_at: datetime


@dataclass
class AlignmentResult:
    alignment_score: float        # 0-1, correlation across 3 signals
    regime: str                   # "stable" | "adjust_weights" | "retrain" | "critical"
    recommendation: str
    severity: float              # 0-1
    signals: DriftSignals


class DriftAlignment:
    """
    Monitors triple drift: feature ≠ model ≠ system drift.
    When signals disagree, system enters degraded mode.
    """

    def __init__(
        self,
        retrain_threshold: float = 0.3,
        adjust_threshold: float = 0.6,
        stable_threshold: float = 0.85,
        window_hours: int = 24,
        tsdb_client=None,
    ):
        self.retrain_threshold = retrain_threshold
        self.adjust_threshold = adjust_threshold
        self.stable_threshold = stable_threshold
        self.window_hours = window_hours
        self.tsdb = tsdb_client

        self._feature_history: list[float] = []
        self._model_error_history: list[float] = []
        self._system_drift_history: list[float] = []
        self._timestamps: list[datetime] = []

    def record_signals(self, signals: DriftSignals) -> None:
        """Record a measurement of all three drift signals."""
        self._feature_history.append(signals.feature_drift_score)
        self._model_error_history.append(signals.model_error_rate)
        self._system_drift_history.append(signals.system_drift_score)
        self._timestamps.append(signals.measured_at)

        # Trim to window
        cutoff = datetime.utcnow() - timedelta(hours=self.window_hours)
        mask = [t >= cutoff for t in self._timestamps]
        self._feature_history = [f for f, m in zip(self._feature_history, mask) if m]
        self._model_error_history = [m for m, mk in zip(self._model_error_history, mask) if mk]
        self._system_drift_history = [s for s, m in zip(self._system_drift_history, mask) if m]
        self._timestamps = [t for t, m in zip(self._timestamps, mask) if m]

    def measure_feature_drift(
        self,
        reference_window: list[dict],
        current_window: list[dict],
    ) -> float:
        """
        Compute feature drift via KS test on distribution shift.
        Returns 0-1, higher = more drift.
        """
        if len(reference_window) < 10 or len(current_window) < 10:
            return 0.0

        drifts = []
        feature_keys = set()
        for sample in reference_window + current_window:
            feature_keys.update(sample.keys())

        for key in feature_keys:
            if key in ("timestamp", "node_id", "job_id"):
                continue
            ref_vals = np.array([s[key] for s in reference_window if key in s])
            cur_vals = np.array([s[key] for s in current_window if key in s])
            if len(ref_vals) < 5 or len(cur_vals) < 5:
                continue
            # Two-sample KS test (simplified)
            ref_sorted = np.sort(ref_vals)
            cur_sorted = np.sort(cur_vals)
            n1, n2 = len(ref_sorted), len(cur_sorted)
            # Max diff between ECDFs
            all_vals = np.concatenate([ref_sorted, cur_sorted])
            ks_stat = 0.0
            for v in all_vals:
                e1 = np.searchsorted(ref_sorted, v, side="right") / n1
                e2 = np.searchsorted(cur_sorted, v, side="right") / n2
                ks_stat = max(ks_stat, abs(e1 - e2))
            drifts.append(ks_stat)

        return float(np.mean(drifts)) if drifts else 0.0

    def measure_model_drift(
        self,
        recent_predictions: list[float],
        recent_actuals: list[float],
    ) -> float:
        """
        Compute model error rate (MAPE).
        Returns 0-1, higher = more drift.
        """
        if len(recent_predictions) < 10:
            return 0.0
        errors = np.abs(np.array(recent_predictions) - np.array(recent_actuals))
        mape = np.mean(errors)
        return float(np.clip(mape, 0.0, 1.0))

    def measure_system_drift(
        self,
        simulated_states: list[dict],
        actual_states: list[dict],
    ) -> float:
        """
        Compute divergence: simulated vs actual cluster behavior.
        Returns 0-1, higher = more divergence.
        """
        if len(simulated_states) < 5 or len(actual_states) < 5:
            return 0.0

        divergences = []
        for sim, act in zip(simulated_states[-50:], actual_states[-50:]):
            # Compare throughput, queue_depth, failure_prob
            for key in ("throughput", "queue_depth", "cluster_failure_prob"):
                if key in sim and key in act:
                    rel_diff = abs(sim[key] - act[key]) / (max(abs(act[key]), 1e-9))
                    divergences.append(min(rel_diff, 1.0))

        return float(np.mean(divergences)) if divergences else 0.0

    def compute_alignment(self) -> AlignmentResult:
        """
        Compute correlation across three drift signals.
        Drift_Alignment = mean(corr(f1,f2), corr(f2,f3), corr(f1,f3))
        """
        n = min(len(self._feature_history), len(self._model_error_history), len(self._system_drift_history))
        if n < 10:
            return AlignmentResult(
                alignment_score=1.0,
                regime="stable",
                recommendation="insufficient data",
                severity=0.0,
                signals=DriftSignals(0.0, 0.0, 0.0, datetime.utcnow()),
            )

        f = np.array(self._feature_history[-n:])
        m = np.array(self._model_error_history[-n:])
        s = np.array(self._system_drift_history[-n:])

        correlations = []
        for a, b in [(f, m), (m, s), (f, s)]:
            if np.std(a) > 1e-9 and np.std(b) > 1e-9:
                corr, _ = pearsonr(a, b)
                if not np.isnan(corr):
                    correlations.append(abs(corr))
                else:
                    correlations.append(0.0)
            else:
                correlations.append(0.0)

        alignment = float(np.mean(correlations)) if correlations else 0.0

        # Classify regime
        mean_feature = float(np.mean(f))
        mean_model = float(np.mean(m))
        mean_system = float(np.mean(s))

        if alignment < self.retrain_threshold:
            regime = "retrain"
            recommendation = "critical drift misalignment — retrain v5 model immediately"
            severity = max(mean_feature, mean_model, mean_system)
        elif alignment < self.adjust_threshold:
            regime = "adjust_weights"
            recommendation = "moderate drift — adjust objective weights"
            severity = np.mean([mean_feature, mean_model, mean_system]) * 0.5
        elif alignment < self.stable_threshold:
            regime = "stable"
            recommendation = "drift within acceptable range"
            severity = 0.1
        else:
            regime = "stable"
            recommendation = "system well-calibrated"
            severity = 0.0

        signals = DriftSignals(
            feature_drift_score=mean_feature,
            model_error_rate=mean_model,
            system_drift_score=mean_system,
            measured_at=datetime.utcnow(),
        )

        return AlignmentResult(
            alignment_score=alignment,
            regime=regime,
            recommendation=recommendation,
            severity=severity,
            signals=signals,
        )

    def get_recommendation(self) -> AlignmentResult:
        """Shorthand for compute_alignment()."""
        return self.compute_alignment()
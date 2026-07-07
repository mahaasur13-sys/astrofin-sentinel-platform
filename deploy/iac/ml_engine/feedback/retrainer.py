#!/usr/bin/env python3
"""
Retrainer — scheduled + drift-triggered model retraining.
Triggers: every N jobs completed, or when drift detected.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Retrainer:
    def __init__(
        self,
        trainer,
        registry,
        job_count_threshold: int = 500,
        drift_threshold: float = 0.1,
    ):
        self.trainer = trainer
        self.registry = registry
        self.job_count_threshold = job_count_threshold
        self.drift_threshold = drift_threshold
        self._jobs_since_retrain = 0
        self._last_metrics = {}

    def should_retrain(self, current_metrics: dict | None = None) -> bool:
        """Check if retraining conditions are met."""
        if self._jobs_since_retrain >= self.job_count_threshold:
            return True

        if current_metrics and self._last_metrics:
            for key in ["test_auc", "test_f1"]:
                if key in current_metrics and key in self._last_metrics:
                    if abs(current_metrics[key] - self._last_metrics[key]) > self.drift_threshold:
                        logger.info(
                            f"Drift detected on {key}: {self._last_metrics[key]:.4f} → {current_metrics[key]:.4f}"
                        )
                        return True

        return False

    def retrain(self, output_dir: Path | None = None) -> dict:
        """Execute retraining and update last metrics."""
        logger.info("Retraining triggered...")
        self._jobs_since_retrain = 0

        versions = self.trainer.train(output_dir=output_dir)
        self._last_metrics = self._load_latest_metrics()

        logger.info(f"Retraining complete: {versions}")
        return versions

    def notify_job_completed(self) -> None:
        """Call after each job completes — tracks toward retrain threshold."""
        self._jobs_since_retrain += 1
        if self._jobs_since_retrain % 100 == 0:
            logger.info(f"{self._jobs_since_retrain} jobs since last retrain")

    def _load_latest_metrics(self) -> dict:
        latest = self.registry.get_latest("failure_xgb")
        return latest["metrics"] if latest else {}

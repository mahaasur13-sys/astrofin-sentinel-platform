#!/usr/bin/env python3
"""
Dataset Exporter — builds supervised ML datasets with train/val/test splits.
Features(t) → Label(t + horizon_minutes).
Time-based split (80/10/10) — no future leakage.
"""
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import asdict
from .schemas import LabeledExample, MLBatch, LabelType
from .builder import FeatureBuilder
from .window_engine import WindowEngine

# =============================================================================
# LABELS
# =============================================================================

def _label_from_outcome(outcome: str) -> int:
    """Map job/outcome string to label integer."""
    mapping = {
        "success":    LabelType.HEALTHY.value,
        "healthy":    LabelType.HEALTHY.value,
        "completed":  LabelType.HEALTHY.value,
        "running":    LabelType.HEALTHY.value,
        "degraded":   LabelType.DEGRADED.value,
        "slow":       LabelType.DEGRADED.value,
        "retried":    LabelType.DEGRADED.value,
        "failed":     LabelType.FAILED.value,
        "error":      LabelType.FAILED.value,
        "crashed":    LabelType.FAILED.value,
        "timeout":    LabelType.FAILED.value,
        "oom":        LabelType.FAILED.value,
    }
    return mapping.get(outcome.lower(), LabelType.HEALTHY.value)

# =============================================================================
# DATASET EXPORTER
# =============================================================================

class DatasetExporter:
    """
    Builds ML datasets from state_store + window_engine.

    Flow:
        1. Load job_events from state_store
        2. For each job outcome at time T, look ahead horizon_minutes
        3. Label = FAILED if any failure in [T, T+horizon]
        4. Features = feature_builder.build(node, T)
        5. Split 80/10/10 (time-based)
    """

    def __init__(
        self,
        state_store=None,        # optional: StateStore instance
        window_engine: Optional[WindowEngine] = None,
        horizon_minutes: int = 30,
    ):
        self.state_store = state_store
        self.window_engine = window_engine or WindowEngine()
        self.horizon_minutes = horizon_minutes
        self.feature_builder = FeatureBuilder(self.window_engine)

    def _load_events(self) -> List[Dict]:
        """Load job events from state_store. Falls back to synthetic data."""
        if self.state_store is not None:
            return self.state_store.get_all_events()
        # Synthetic fallback: generate demo events for testing
        return self._generate_synthetic_events()

    def _generate_synthetic_events(self) -> List[Dict]:
        """Generate synthetic job events for testing/demos."""
        import random
        from datetime import timedelta
        now = datetime.now()
        events = []
        for i in range(200):
            t = now - timedelta(minutes=200 - i)
            node = "rtx-node" if i % 3 != 0 else "rk3576-node"
            outcome = random.choices(
                ["success", "failed", "degraded"],
                weights=[0.7, 0.15, 0.15]
            )[0]
            events.append({
                "job_id": f"job_{i:04d}",
                "node_id": node,
                "timestamp": t.isoformat(),
                "state": outcome,
                "gpu_util_avg": random.uniform(10, 95),
                "cpu_util_avg": random.uniform(5, 80),
                "mem_util_avg": random.uniform(20, 70),
            })
        return events

    def _get_label(self, node_id: str, current_time: datetime, future_events: List[Dict]) -> int:
        """Determine label: did node fail within horizon_minutes?"""
        horizon = timedelta(minutes=self.horizon_minutes)
        cutoff = current_time + horizon
        for evt in future_events:
            ts = evt.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            if ts < current_time:
                continue
            if ts > cutoff:
                continue
            if evt.get("node_id") != node_id:
                continue
            state = evt.get("state", "").lower()
            if state in ("failed", "crashed", "error", "timeout", "oom"):
                return LabelType.FAILED.value
            if state in ("degraded", "slow"):
                return LabelType.DEGRADED.value
        return LabelType.HEALTHY.value

    def build_dataset(self) -> MLBatch:
        """
        Build MLBatch with train/val/test splits (time-based 80/10/10).
        Returns MLBatch containing LabeledExample lists.
        """
        events = self._load_events()
        if not events:
            return MLBatch(train=[], val=[], test=[])

        # Sort by timestamp
        events = sorted(events, key=lambda e: e.get("timestamp", ""))
        n = len(events)
        train_end = int(n * 0.8)
        val_end   = int(n * 0.9)

        splits = {
            "train": events[:train_end],
            "val":   events[train_end:val_end],
            "test":  events[val_end:],
        }

        batch_data: Dict[str, List[LabeledExample]] = {"train": [], "val": [], "test": []}

        for split_name, split_events in splits.items():
            future_events = events  # full list for label look-ahead
            for i, evt in enumerate(split_events):
                ts_str = evt.get("timestamp", "")
                if isinstance(ts_str, str):
                    ts = datetime.fromisoformat(ts_str)
                else:
                    ts = ts_str

                node_id = evt.get("node_id", "unknown")
                job_id  = evt.get("job_id")

                # Build features at time T
                for metric, key in [
                    ("gpu_util", "gpu_util_avg"),
                    ("cpu_util", "cpu_util_avg"),
                    ("mem_util", "mem_util_avg"),
                ]:
                    if key in evt:
                        self.window_engine.push(node_id, metric, evt[key], ts)

                fv = self.feature_builder.build(node_id, ts)

                # Determine label
                label = self._get_label(node_id, ts, future_events)

                example = LabeledExample(
                    node_id=node_id,
                    timestamp=ts,
                    horizon_minutes=self.horizon_minutes,
                    features=fv.features,
                    label=label,
                    job_id=job_id,
                )
                batch_data[split_name].append(example)

        return MLBatch(
            train=batch_data["train"],
            val=batch_data["val"],
            test=batch_data["test"],
            metadata={
                "horizon_minutes": self.horizon_minutes,
                "generated_at": datetime.now().isoformat(),
                "registry_version": "1.0.0",
            },
        )

    def export_csv(self, output_dir: str, split: str = "train") -> str:
        """Export a split to CSV file. Returns path."""
        batch = self.build_dataset()
        path = Path(output_dir) / f"{split}.csv"
        batch.to_csv(str(path), split=split)
        return str(path)

    def export_json(self, output_dir: str) -> str:
        """Export full dataset to JSON. Returns path."""
        batch = self.build_dataset()
        path = Path(output_dir) / "dataset.json"
        data = {
            "metadata": batch.metadata,
            "train_size": batch.train_size,
            "val_size":   batch.val_size,
            "test_size":  batch.test_size,
            "train": [ex.to_ml_dict() for ex in batch.train],
            "val":   [ex.to_ml_dict() for ex in batch.val],
            "test":  [ex.to_ml_dict() for ex in batch.test],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return str(path)

    def export_parquet(self, output_dir: str) -> str:
        """Export full dataset to Parquet (if pyarrow available). Returns path."""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError("pyarrow required for Parquet export: pip install pyarrow")
        batch = self.build_dataset()
        path = Path(output_dir) / "dataset.parquet"
        all_examples = batch.train + batch.val + batch.test
        rows = [ex.to_ml_dict() for ex in all_examples]
        table = pa.Table.from_pylist(rows)
        pq.write_table(table, str(path))
        return str(path)

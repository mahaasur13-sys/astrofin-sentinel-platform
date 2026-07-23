#!/usr/bin/env python3
"""
Model Registry — versioned model storage + lineage tracking.
Each trained model is versioned, logged, and hash-identified.
"""

import hashlib
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path(
    os.environ.get(
        "MODEL_REGISTRY_PATH",
        "/home/workspace/home-cluster-iac/ml_engine/registry/models",
    )
)


class ModelRegistry:
    def __init__(self, registry_path: Path | None = None):
        self.registry_path = registry_path or REGISTRY_PATH
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self._index_path = self.registry_path / "index.json"
        self._load_index()

    def _load_index(self) -> None:
        if self._index_path.exists():
            with open(self._index_path) as f:
                self._index: dict[str, Any] = json.load(f)
        else:
            self._index = {}

    def _save_index(self) -> None:
        with open(self._index_path, "w") as f:
            json.dump(self._index, f, indent=2, default=str)

    def _compute_hash(self, params: dict, metrics: dict) -> str:
        """Stable hash of model config + metrics for identity."""
        h = hashlib.sha256()
        h.update(json.dumps(params, sort_keys=True).encode())
        h.update(
            json.dumps(
                {k: float(v) for k, v in metrics.items()}, sort_keys=True
            ).encode()
        )
        return h.hexdigest()[:12]

    def register(
        self,
        model_name: str,
        model_file: Path,
        params: dict[str, Any],
        metrics: dict[str, float],
        feature_names: list[str],
        train_rows: int,
        dataset_version: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Register a trained model version.

        Returns:
            version_id: e.g. "failure_xgb_v00142_abcd3f"
        """
        version_hash = self._compute_hash(params, metrics)
        version_id = f"{model_name}_v{len([v for v in self._index if v.startswith(model_name)]) + 1:05d}_{version_hash}"

        model_dir = self.registry_path / version_id
        model_dir.mkdir(parents=True, exist_ok=True)

        dest_file = model_dir / "model.pkl"
        shutil.copy2(model_file, dest_file)

        entry = {
            "version_id": version_id,
            "model_name": model_name,
            "registered_at": datetime.utcnow().isoformat(),
            "params": params,
            "metrics": metrics,
            "feature_names": feature_names,
            "train_rows": train_rows,
            "dataset_version": dataset_version,
            "model_file": str(dest_file),
            "metadata": metadata or {},
        }

        self._index[version_id] = entry
        self._save_index()

        logger.info(f"Registered {version_id} — AUC={metrics.get('test_auc', '?')}")
        return version_id

    def get(self, version_id: str) -> dict[str, Any] | None:
        return self._index.get(version_id)

    def get_latest(self, model_name: str) -> dict[str, Any] | None:
        versions = sorted(
            [v for v in self._index.values() if v["model_name"] == model_name],
            key=lambda v: v["registered_at"],
            reverse=True,
        )
        return versions[0] if versions else None

    def list_versions(self, model_name: str | None = None) -> list[dict[str, Any]]:
        if model_name:
            return sorted(
                [v for v in self._index.values() if v["model_name"] == model_name],
                key=lambda v: v["registered_at"],
                reverse=True,
            )
        return sorted(
            self._index.values(), key=lambda v: v["registered_at"], reverse=True
        )

    def load_model(self, version_id: str):
        """Load model artifact from registry."""
        entry = self.get(version_id)
        if not entry:
            raise ValueError(f"Model {version_id} not found in registry")

        import pickle

        with open(entry["model_file"], "rb") as f:
            return pickle.load(f)

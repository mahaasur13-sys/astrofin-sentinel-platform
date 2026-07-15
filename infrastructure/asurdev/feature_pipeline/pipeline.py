#!/usr/bin/env python3
"""
Feature Pipeline CLI — orchestrates the full ML feature pipeline.

Usage:
    python pipeline.py --continuous --interval 60
    python pipeline.py --nodes rtx-node --window 5m
    python pipeline.py --export-csv --output /data/ml
    python pipeline.py --validate-registry
    python pipeline.py --embedding --nodes rtx-node,rk3576-node
"""
import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .window_engine import WindowEngine
from .feature_registry import FEATURE_REGISTRY, get_feature_names, validate_registry
from .builder import FeatureBuilder
from .exporter import DatasetExporter
from .embedding import NodeEmbeddingBuilder
from .schemas import NodeProfile, NodeRole

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pipeline")

# =============================================================================
# ARGUMENT PARSER
# =============================================================================

def parse_args():
    p = argparse.ArgumentParser(description="Home Cluster Feature Pipeline CLI")
    p.add_argument("--validate-registry", action="store_true", help="Validate feature registry")
    p.add_argument("--continuous", action="store_true", help="Run continuous pipeline")
    p.add_argument("--interval", type=int, default=60, help="Sampling interval in seconds")
    p.add_argument("--nodes", type=str, default="rtx-node,rk3576-node", help="Comma-separated node IDs")
    p.add_argument("--export-csv", action="store_true", help="Export CSV dataset")
    p.add_argument("--export-json", action="store_true", help="Export JSON dataset")
    p.add_argument("--export-parquet", action="store_true", help="Export Parquet dataset")
    p.add_argument("--output", type=str, default="/tmp/ml_dataset", help="Output directory")
    p.add_argument("--horizon", type=int, default=30, help="Prediction horizon in minutes")
    p.add_argument("--embedding", action="store_true", help="Compute and show node embeddings")
    p.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG","INFO","WARNING"])
    return p.parse_args()

# =============================================================================
# CONTINUOUS PIPELINE
# =============================================================================

def run_continuous(nodes: List[str], interval: int):
    """Continuously push metrics and build feature vectors."""
    log.info("Starting continuous pipeline — interval=%ds, nodes=%s", interval, nodes)
    engine = WindowEngine()
    builder = FeatureBuilder(engine)

    # Simulated metric streams per node (replace with real Prometheus queries)
    import random
    metrics = ["gpu_util", "cpu_util", "mem_util", "queue_size"]

    while True:
        ts = datetime.now()
        for node in nodes:
            for metric in metrics:
                value = random.uniform(10, 90)
                engine.push(node, metric, value, ts)

        for node in nodes:
            fv = builder.build(node, ts)
            log.info(
                "node=%s gpu_mean_5m=%.1f queue_mean_5m=%.1f health_score=%.1f",
                node,
                fv.features.get("gpu_mean_5m", 0),
                fv.features.get("queue_mean_5m", 0),
                fv.features.get("health_score", 0),
            )
        time.sleep(interval)

# =============================================================================
# DATASET EXPORT
# =============================================================================

def run_export(output_dir: str, export_csv: bool, export_json: bool,
               export_parquet: bool, horizon: int):
    """Export ML dataset."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    exporter = DatasetExporter(horizon_minutes=horizon)

    if export_csv:
        for split in ["train", "val", "test"]:
            path = exporter.export_csv(output_dir, split=split)
            log.info("Exported %s CSV → %s", split, path)

    if export_json:
        path = exporter.export_json(output_dir)
        log.info("Exported JSON → %s", path)

    if export_parquet:
        try:
            path = exporter.export_parquet(output_dir)
            log.info("Exported Parquet → %s", path)
        except ImportError as e:
            log.warning("Skipping Parquet: %s", e)

# =============================================================================
# EMBEDDING
# =============================================================================

def run_embedding(nodes: List[str]):
    """Compute and display node embeddings."""
    emb_builder = NodeEmbeddingBuilder()

    profiles = {
        "rtx-node": NodeProfile(
            node_id="rtx-node", role=NodeRole.GPU,
            gpu_capacity=10.0, cpu_cores=12, memory_gb=64,
            storage_gb=2000, network_mbps=1000,
            historical_failure_rate=0.5, avg_latency_ms=2.0,
            queue_volatility=3.5,
        ),
        "rk3576-node": NodeProfile(
            node_id="rk3576-node", role=NodeRole.CPU,
            gpu_capacity=0.5, cpu_cores=8, memory_gb=16,
            storage_gb=256, network_mbps=1000,
            historical_failure_rate=0.2, avg_latency_ms=5.0,
            queue_volatility=1.2,
        ),
    }

    embeddings = {}
    for node in nodes:
        if node in profiles:
            emb = emb_builder.build_from_profile(profiles[node])
        else:
            emb = emb_builder.build_from_features({})
        embeddings[node] = emb
        log.info("node=%s embedding=%s", node, emb[:4].tolist())

    # Show similar nodes
    for node in nodes:
        similar = emb_builder.find_similar_nodes(embeddings[node], embeddings, top_k=3)
        log.info("Similar to %s: %s", node, similar)

# =============================================================================
# MAIN
# =============================================================================

def main():
    args = parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    nodes = args.nodes.split(",")

    if args.validate_registry:
        log.info("Validating feature registry (%d features)...", len(get_feature_names()))
        validate_registry()
        log.info("✓ Registry valid")
        return

    if args.continuous:
        run_continuous(nodes, args.interval)
        return

    do_export = args.export_csv or args.export_json or args.export_parquet
    if do_export:
        run_export(args.output, args.export_csv, args.export_json,
                   args.export_parquet, args.horizon)
        return

    if args.embedding:
        run_embedding(nodes)
        return

    # Default: run once with demo data
    log.info("Running demo pipeline...")
    engine = WindowEngine()
    builder = FeatureBuilder(engine)

    import random
    ts = datetime.now()
    for node in nodes:
        for metric in ["gpu_util", "cpu_util", "mem_util", "queue_size"]:
            for _ in range(20):
                engine.push(node, metric, random.uniform(10, 90), ts)

    for node in nodes:
        fv = builder.build(node, ts)
        log.info("Feature vector for %s: %d features", node, len(fv.features))

if __name__ == "__main__":
    main()

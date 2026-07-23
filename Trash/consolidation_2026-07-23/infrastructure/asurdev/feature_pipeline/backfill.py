#!/usr/bin/env python3
"""
Backfill Script — Historical Feature Reconstruction from TimescaleDB
Enables ML training on fully historical data (no Prometheus gap).

Usage:
    # Backfill last 7 days for all nodes
    python backfill.py --days 7

    # Backfill specific window
    python backfill.py --start "2026-03-01" --end "2026-03-29"

    # Backfill + export immediately
    python backfill.py --days 7 --export-csv --output /data/ml
"""
import os
import sys
import argparse
import structlog
from datetime import datetime, timezone, timedelta
from typing import Optional, List

logger = structlog.get_logger()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from feature_pipeline import FeatureBuilder, FeatureExporter, build_features


DSN = os.environ.get('CLUSTER_DSN', 'postgresql://cluster:password@localhost:5432/cluster_metrics')


def backfill_range(
    start: datetime,
    end: datetime,
    export_dir: Optional[str] = None,
    nodes: Optional[List[str]] = None
):
    """
    Reconstruct features from TimescaleDB continuous aggregates.
    Queries metrics_5m (primary) with full historical fidelity.
    """
    import psycopg2

    conn = psycopg2.connect(DSN)
    cur = conn.cursor()

    node_filter = f"AND node_id IN ({','.join(repr(n) for n in nodes)})" if nodes else ""

    query = f"""
    SELECT
        bucket,
        node_id,
        metric,
        avg,
        min,
        max,
        stddev,
        p50,
        p95,
        p99
    FROM metrics_5m
    WHERE bucket >= %s
      AND bucket <= %s
      {node_filter}
    ORDER BY bucket, node_id, metric
    """
    cur.execute(query, (start, end))
    rows = cur.fetchall()
    logger.info("retrieved_rows", count=len(rows), start=start.isoformat(), end=end.isoformat())

    from collections import defaultdict
    buckets: dict = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        bucket, node_id, metric, avg, min_v, max_v, stddev, p50, p95, p99 = row
        buckets[bucket][node_id][metric] = {
            'avg': avg, 'min': min_v, 'max': max_v,
            'stddev': stddev, 'p50': p50, 'p95': p95, 'p99': p99
        }

    builder = FeatureBuilder()
    all_vectors = []

    for bucket, nodes_data in sorted(buckets.items()):
        for node_id, metrics in nodes_data.items():
            fv = build_features(node_id, metrics)
            if fv:
                all_vectors.append(fv)

    logger.info("feature_vectors_built", count=len(all_vectors))

    if export_dir and all_vectors:
        exporter = FeatureExporter(export_dir)
        exporter.export_csv(all_vectors)
        logger.info("exported", path=export_dir)

    cur.close()
    conn.close()
    return all_vectors


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--start', type=str)
    parser.add_argument('--end', type=str)
    parser.add_argument('--export-csv', action='store_true')
    parser.add_argument('--output', default='/tmp/ml_dataset')
    args = parser.parse_args()

    if args.start and args.end:
        start = datetime.fromisoformat(args.start)
        end = datetime.fromisoformat(args.end)
    else:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=args.days)

    if args.export_csv:
        os.makedirs(args.output, exist_ok=True)

    backfill_range(start, end, export_dir=args.output if args.export_csv else None)

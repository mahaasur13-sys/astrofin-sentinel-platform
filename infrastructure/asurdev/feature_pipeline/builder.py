#!/usr/bin/env python3
"""
Feature Builder — registry-driven ML feature computation.
Dual backend:
  - TimescaleDB (PROD): queries continuous aggregates directly
  - Prometheus (FALLBACK): scrape live metrics

Usage:
    builder = FeatureBuilder(backend='timescalebd')  # PRO
    builder = FeatureBuilder(backend='prometheus')    # DEV
    vectors = builder.build_batch(['rtx-node', 'rk3576'])
"""
import os
import structlog
from typing import Dict, List, Optional, Literal
from dataclasses import asdict

logger = structlog.get_logger()

Backend = Literal['timescale', 'prometheus']


class FeatureBuilder:
    """
    Computes feature vectors from either TimescaleDB (primary) or Prometheus (fallback).
    Uses window_engine internally for sliding-window aggregation.
    """

    def __init__(
        self,
        backend: Backend = 'timescale',
        tsdb_dsn: Optional[str] = None,
        prometheus_url: str = 'http://localhost:9090',
    ):
        self.backend = backend
        self.tsdb_dsn = tsdb_dsn or os.environ.get(
            'CLUSTER_DSN',
            'postgresql://cluster:password@localhost:5432/cluster_metrics'
        )
        self.prometheus_url = prometheus_url
        self._conn = None
        self._prom_client = None

    # -------------------------------------------------------------------------
    # TimescaleDB path (PROD)
    # -------------------------------------------------------------------------
    def _tsdb_connect(self):
        import psycopg2
        if self._conn is None:
            self._conn = psycopg2.connect(self.tsdb_dsn)
        return self._conn

    def _query_tsdb(self, node_id: str, window_minutes: int = 5) -> Dict[str, Dict]:
        """Query TimescaleDB continuous aggregate for a node."""
        conn = self._tsdb_connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT metric, avg, min, max, stddev, p50, p95, p99
            FROM metrics_5m
            WHERE node_id = %s
              AND bucket >= NOW() - INTERVAL '%s minutes'
            ORDER BY bucket DESC
            LIMIT 1000
        """, (node_id, window_minutes))
        rows = cur.fetchall()
        result: Dict[str, Dict] = {}
        for metric, avg, min_v, max_v, stddev, p50, p95, p99 in rows:
            if metric not in result:
                result[metric] = {'avg': avg, 'min': min_v, 'max': max_v,
                                   'stddev': stddev, 'p50': p50, 'p95': p95, 'p99': p99}
        return result

    # -------------------------------------------------------------------------
    # Prometheus path (FALLBACK/DEV)
    # -------------------------------------------------------------------------
    def _query_prometheus(self, node_id: str) -> Dict[str, float]:
        import requests
        queries = {
            'gpu_util': f'avg by (node) (DCGM_FI_DEV_GPU_UTIL{{node="{node_id}"}})',
            'gpu_mem':  f'avg by (node) (DCGM_FI_DEV_FB_USED{{node="{node_id}"}})',
            'cpu_util': f'avg by (node) (rate(node_cpu_seconds_total{{mode="idle",node="{node_id}"}}[%s])) * 100',
            'mem_used': f'node_memory_MemAvailable_bytes{{node="{node_id}"}}',
        }
        result = {}
        for key, query in queries.items():
            try:
                r = requests.get(
                    f'{self.prometheus_url}/api/v1/query',
                    params={'query': query},
                    timeout=5
                )
                if r.status_code == 200 and r.json()['status'] == 'success':
                    data = r.json()['data']['result']
                    if data:
                        result[key] = float(data[0]['value'][1])
            except Exception:
                pass
        return result

    # -------------------------------------------------------------------------
    # Build
    # -------------------------------------------------------------------------
    def build(self, node_id: str) -> Dict:
        """
        Build a single feature vector for node_id.
        Uses TimescaleDB if backend='timescale', Prometheus otherwise.
        """
        if self.backend == 'timescale':
            metrics = self._query_tsdb(node_id)
        else:
            raw = self._query_prometheus(node_id)
            metrics = {k: {'avg': v, 'min': v, 'max': v, 'stddev': 0, 'p50': v, 'p95': v, 'p99': v}
                       for k, v in raw.items()}

        from feature_pipeline import build_features
        return build_features(node_id, metrics)

    def build_batch(self, node_ids: List[str]) -> List[Dict]:
        return [fv for node_id in node_ids if (fv := self.build(node_id))]


def build_features(node_id: str, metrics: Dict) -> Dict:
    """
    Convert raw metrics dict into a feature vector, using window_engine aggregations.
    Called by FeatureBuilder internally.
    """
    from feature_pipeline.window_engine import WindowEngine
    from feature_pipeline.feature_registry import get_feature_names

    engine = WindowEngine()
    for metric, vals in metrics.items():
        for stat, val in vals.items():
            if val is not None:
                engine.push(node_id, f'{metric}_{stat}', val)

    vec = {'node_id': node_id, 'features': {}, 'registry_version': 'v1'}
    for feat_name in get_feature_names():
        agg = engine.aggregate(node_id, feat_name)
        vec['features'][feat_name] = agg
    return vec

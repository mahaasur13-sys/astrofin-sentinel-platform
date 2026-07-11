#!/usr/bin/env python3
"""
Dataset Builder — constructs ML-ready train/val/test sets from TimescaleDB.
Assembles features + labels, handles node filtering, version tracking.
"""

import logging
from datetime import datetime, timedelta

import pandas as pd

from feature_pipeline import FeatureBuilder

logger = logging.getLogger(__name__)


class DatasetBuilder:
    def __init__(
        self,
        tsdb_host: str = "localhost",
        tsdb_port: int = 5432,
        tsdb_user: str = "postgres",
        tsdb_password: str = "postgres",
        tsdb_db: str = "cluster_metrics",
    ):
        self._builder = FeatureBuilder(
            tsdb_host=tsdb_host,
            tsdb_port=tsdb_port,
            tsdb_user=tsdb_user,
            tsdb_password=tsdb_password,
            tsdb_db=tsdb_db,
        )

    def build(
        self,
        node_ids: list[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        horizon_minutes: int = 30,
        window_type: str = "5m",
        min_samples: int = 100,
    ) -> pd.DataFrame:
        """
        Build feature dataset with failure labels for ML training.

        Args:
            node_ids: filter to specific nodes (None = all nodes)
            start_time: start of window (default: 7 days ago)
            end_time: end of window (default: now)
            horizon_minutes: how far ahead to predict failures
            window_type: feature aggregation window
            min_samples: minimum samples per node

        Returns:
            DataFrame with features + label columns
        """
        end_time = end_time or datetime.utcnow()
        start_time = start_time or (end_time - timedelta(days=7))

        logger.info(
            f"Building dataset: start={start_time}, end={end_time}, " f"horizon={horizon_minutes}m, nodes={node_ids}"
        )

        # Pull raw feature vectors from TimescaleDB
        features_df = self._builder.build_batch(
            node_ids=node_ids,
            start_time=start_time,
            end_time=end_time,
            window_type=window_type,
        )

        # Pull labels (failure events in horizon window)
        labels_df = self._label_from_timescale(
            start_time=start_time,
            end_time=end_time,
            horizon_minutes=horizon_minutes,
            node_ids=node_ids,
        )

        if features_df.empty:
            logger.warning("No features found in time range")
            return pd.DataFrame()

        if labels_df.empty:
            logger.warning("No labels found — all samples will be labeled non-failure")
            features_df["label_failure"] = 0
            features_df["label_queue_depth"] = 0.0
            features_df["label_gpu_util"] = features_df.get("gpu_util_5m_avg", 0.0)
            return features_df

        # Merge features with labels on node + time window
        features_df = features_df.copy()
        features_df["time_bucket"] = features_df["time"].dt.floor(f"{window_type.replace('m', 'min')}")

        labels_df = labels_df.copy()
        labels_df["label_bucket"] = labels_df["failure_time"].dt.floor(f"{window_type.replace('m', 'min')}")

        df = features_df.merge(
            labels_df[["node_id", "label_bucket", "label_failure", "label_queue_depth", "label_gpu_util"]],
            left_on=["node_id", "time_bucket"],
            right_on=["node_id", "label_bucket"],
            how="left",
        )

        df["label_failure"] = df["label_failure"].fillna(0).astype(int)
        df["label_queue_depth"] = df["label_queue_depth"].fillna(0)
        df["label_gpu_util"] = df["label_gpu_util"].fillna(df.get("gpu_util_5m_avg", 0.0))

        # Filter low-sample nodes
        node_counts = df.groupby("node_id").size()
        valid_nodes = node_counts[node_counts >= min_samples].index
        df = df[df["node_id"].isin(valid_nodes)]

        logger.info(
            f"Dataset built: {len(df)} rows, {df['label_failure'].sum()} failures, " f"{len(valid_nodes)} nodes"
        )
        return df

    def _label_from_timescale(
        self,
        start_time: datetime,
        end_time: datetime,
        horizon_minutes: int,
        node_ids: list[str] | None = None,
    ) -> pd.DataFrame:
        """Query TimescaleDB for failure/load labels within horizon window."""
        try:
            import psycopg2
        except ImportError:
            logger.warning("psycopg2 not available — returning empty labels")
            return pd.DataFrame()

        conn_str = (
            f"host={self._builder._tsdb_host} port={self._builder._tsdb_port} "
            f"dbname={self._builder._tsdb_db} user={self._builder._tsdb_user} "
            f"password={self._builder._tsdb_password}"
        )
        try:
            conn = psycopg2.connect(conn_str)
        except Exception:  # noqa: BLE001
            return pd.DataFrame()

        node_filter = ""
        if node_ids:
            placeholders = ", ".join([f"'{n}'" for n in node_ids])
            node_filter = f"AND node_id IN ({placeholders})"

        query = f"""
        SELECT
            node_id,
            time AS failure_time,
            GREATEST(
                COALESCE(lead(queue_depth) OVER w, queue_depth),
                COALESCE(lead(gpu_util) OVER w, gpu_util)
            ) AS label_queue_depth,
            GREATEST(
                COALESCE(lead(gpu_util) OVER w, gpu_util),
                0
            ) AS label_gpu_util,
            CASE WHEN event_type = 'FAILED' THEN 1 ELSE 0 END AS label_failure
        FROM job_events
        WHERE time >= %(start)s AND time < %(end)s - INTERVAL '{horizon_minutes} minutes'
        {node_filter}
        WINDOW w AS (PARTITION BY node_id ORDER BY time ROWS BETWEEN 1 FOLLOWING AND {max(1, horizon_minutes // 5)} FOLLOWING)
        ORDER BY node_id, time;
        """

        try:
            labels_df = pd.read_sql(query, conn, params={"start": start_time, "end": end_time})
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Label query failed: {e}")
            labels_df = pd.DataFrame()
        finally:
            conn.close()

        return labels_df

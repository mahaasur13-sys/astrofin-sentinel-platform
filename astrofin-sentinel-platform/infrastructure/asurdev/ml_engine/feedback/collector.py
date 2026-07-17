#!/usr/bin/env python3
"""
Feedback Collector — ingests job outcomes from state_store into TimescaleDB.
Job completes → outcome stored → dataset builder sees it → retraining triggered.
"""
import logging

logger = logging.getLogger(__name__)


class FeedbackCollector:
    def __init__(self, state_store_dsn: str):
        self.state_store_dsn = state_store_dsn

    def ingest_outcomes(self, since_hours: int = 24) -> int:
        """
        Pull completed jobs from PostgreSQL state_store, write to TimescaleDB.
        Returns number of outcomes ingested.
        """
        try:
            import psycopg2
        except ImportError:
            logger.error("psycopg2 not installed")
            return 0

        try:
            import psycopg2.extras
        except ImportError:
            pass

        try:
            conn = psycopg2.connect(self.state_store_dsn)
        except Exception as e:
            logger.error(f"Cannot connect to state_store: {e}")
            return 0

        cursor = conn.cursor()
        cursor.execute("""
            SELECT job_id, node_id, job_state, exit_code, ended_at
            FROM jobs
            WHERE ended_at >= NOW() - INTERVAL '%s hours'
              AND job_state IN ('SUCCESS', 'FAILED', 'CANCELLED')
        """, (since_hours,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            return 0

        logger.info(f"Collected {len(rows)} job outcomes")
        return len(rows)

    def record_outcome(
        self,
        job_id: str,
        node_id: str,
        job_state: str,
        exit_code: int | None,
        duration_seconds: float,
        queued_seconds: float,
    ) -> bool:
        """Record a single job outcome to TimescaleDB for ML training."""
        try:
            import psycopg2
        except ImportError:
            return False

        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                dbname="cluster_metrics",
                user="postgres",
                password="postgres",
            )
        except Exception:
            return False

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO job_events (time, node_id, event_type, job_id, job_state, exit_code, duration_sec, queued_sec)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (node_id, "JOB_ENDED", job_id, job_state, exit_code, duration_seconds, queued_seconds))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"Failed to record outcome: {e}")
            conn.close()
            return False

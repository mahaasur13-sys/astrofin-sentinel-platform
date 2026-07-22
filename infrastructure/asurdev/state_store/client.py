#!/usr/bin/env python3
"""
State Store Client — PostgreSQL System of Record
Thread-safe connection pool + all queries for scheduler + job engine.
"""
import os
import uuid
import logging
import contextlib
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import Json, RealDictCursor

log = logging.getLogger("state_store")


class JobStatus(str, Enum):
    CREATED   = "CREATED"
    ADMITTED  = "ADMITTED"
    REJECTED  = "REJECTED"
    SCHEDULED = "SCHEDULED"
    RUNNING   = "RUNNING"
    SUCCESS   = "SUCCESS"
    FAIL      = "FAIL"
    RETRY     = "RETRY"
    CANCELLED = "CANCELLED"


class NodeStatus(str, Enum):
    HEALTHY    = "HEALTHY"
    DEGRADED   = "DEGRADED"
    DOWN       = "DOWN"
    MAINTENANCE = "MAINTENANCE"
    DRAINED    = "DRAINED"


@dataclass
class JobState:
    id: str
    name: str
    job_type: str
    partition_name: str
    status: JobStatus
    priority: int
    retry_count: int
    max_retries: int
    memory_gb: int
    node_target: Optional[str]
    slurm_job_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]


@dataclass
class NodeState:
    hostname: str
    roles: List[str]
    gpu_count: int
    gpu_model: Optional[str]
    cpu_cores: int
    memory_gb: int
    gpu_load_pct: float
    cpu_load_pct: float
    memory_used_gb: float
    health_score: int
    status: NodeStatus
    last_seen: datetime


class StateStore:
    _pool: Optional[pool.ThreadedConnectionPool] = None

    def __init__(self, host="localhost", port=5432,
                 dbname="clusterdb", user=None, password=None):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user or os.environ.get("PGUSER", "clusteruser")
        self.password = password or os.environ.get("PGPASSWORD", "clusterpass")
        self._connect()

    def _connect(self):
        if StateStore._pool is None:
            StateStore._pool = pool.ThreadedConnectionPool(
                minconn=2, maxconn=10,
                host=self.host, port=self.port,
                database=self.dbname,
                user=self.user, password=self.password,
            )
        self._conn = StateStore._pool.getconn()
        self._conn.autocommit = False

    @contextlib.contextmanager
    def _cursor(self, dict_cursor=True):
        cur = self._conn.cursor(
            cursor_factory=RealDictCursor if dict_cursor else None
        )
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    # -------------------------------------------------------------------------
    # Jobs
    # -------------------------------------------------------------------------
    def create_job(self, name: str, job_type: str, memory_gb: int,
                   priority: int = 5, partition_name: str = None,
                   script_path: str = None) -> str:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO jobs (name, job_type, memory_gb, priority,
                                  partition_name, script_path)
                VALUES (%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (name, job_type, memory_gb, priority,
                 partition_name or job_type, script_path)
            )
            job_id = cur.fetchone()["id"]
        self._write_event(job_id, "JOB_CREATED",
                          {"priority": priority, "memory_gb": memory_gb})
        return job_id

    def get_job(self, job_id: str) -> Optional[JobState]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM jobs WHERE id = %s", (job_id,))
            row = cur.fetchone()
        if not row:
            return None
        return JobState(**row)

    def update_job_status(self, job_id: str, status: JobStatus,
                          error_message: str = None,
                          slurm_job_id: int = None) -> bool:
        with self._cursor() as cur:
            if slurm_job_id is not None:
                cur.execute(
                    """UPDATE jobs SET status=%s, slurm_job_id=%s,
                                      error_message=%s, updated_at=NOW()
                       WHERE id=%s""",
                    (status.value, slurm_job_id, error_message, job_id))
            elif error_message is not None:
                cur.execute(
                    """UPDATE jobs SET status=%s, error_message=%s,
                                      updated_at=NOW()
                       WHERE id=%s""",
                    (status.value, error_message, job_id))
            else:
                cur.execute(
                    """UPDATE jobs SET status=%s, updated_at=NOW()
                       WHERE id=%s""",
                    (status.value, job_id))
            affected = cur.rowcount
        if affected:
            self._write_event(job_id, status.value, {})
        return affected > 0

    def get_pending_jobs(self, limit: int = 100) -> List[JobState]:
        with self._cursor() as cur:
            cur.execute(
                """SELECT * FROM jobs
                   WHERE status IN ('CREATED','RETRY')
                   ORDER BY priority DESC, created_at ASC
                   LIMIT %s""",
                (limit,))
            return [JobState(**r) for r in cur.fetchall()]

    def get_active_slurm_job_ids(self) -> List[int]:
        with self._cursor(dict_cursor=False) as cur:
            cur.execute(
                """SELECT DISTINCT slurm_job_id FROM jobs
                   WHERE slurm_job_id IS NOT NULL
                     AND status IN ('SCHEDULED','RUNNING','ADMITTED')""")
            return [r[0] for r in cur.fetchall()]

    def is_job_already_scheduled(self, job_id: str) -> bool:
        """Prevent duplicate Slurm submissions for same job."""
        with self._cursor() as cur:
            cur.execute(
                """SELECT 1 FROM jobs
                   WHERE id=%s AND status IN ('SCHEDULED','RUNNING','ADMITTED')""",
                (job_id,))
            return cur.fetchone() is not None

    # -------------------------------------------------------------------------
    # Nodes
    # -------------------------------------------------------------------------
    def upsert_node(self, hostname: str, roles: List[str],
                    gpu_count: int = 0, gpu_model: str = None,
                    cpu_cores: int = 0, memory_gb: int = 0) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO nodes (hostname, roles, gpu_count, gpu_model,
                                   cpu_cores, memory_gb)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (hostname) DO UPDATE SET
                    roles = EXCLUDED.roles,
                    gpu_count = EXCLUDED.gpu_count,
                    gpu_model = EXCLUDED.gpu_model,
                    cpu_cores = EXCLUDED.cpu_cores,
                    memory_gb = EXCLUDED.memory_gb,
                    last_seen = NOW()
                """,
                (hostname, roles, gpu_count, gpu_model,
                 cpu_cores, memory_gb))

    def update_node_metrics(self, hostname: str,
                            gpu_load_pct: float, cpu_load_pct: float,
                            memory_used_gb: float,
                            health_score: int = None,
                            status: NodeStatus = None) -> None:
        with self._cursor() as cur:
            if status:
                cur.execute(
                    """UPDATE nodes SET
                           gpu_load_pct=%s, cpu_load_pct=%s,
                           memory_used_gb=%s, health_score=%s,
                           status=%s, last_seen=NOW()
                       WHERE hostname=%s""",
                    (gpu_load_pct, cpu_load_pct, memory_used_gb,
                     health_score or 100, status.value, hostname))
            else:
                cur.execute(
                    """UPDATE nodes SET
                           gpu_load_pct=%s, cpu_load_pct=%s,
                           memory_used_gb=%s, last_seen=NOW()
                       WHERE hostname=%s""",
                    (gpu_load_pct, cpu_load_pct, memory_used_gb, hostname))

    def get_healthy_nodes(self) -> List[NodeState]:
        with self._cursor() as cur:
            cur.execute(
                """SELECT * FROM nodes
                   WHERE status IN ('HEALTHY','DEGRADED')
                   ORDER BY
                     CASE WHEN 'slurm_compute' = ANY(roles) THEN 0 ELSE 1 END,
                     gpu_load_pct ASC""")
            return [NodeState(**r) for r in cur.fetchall()]

    def get_node(self, hostname: str) -> Optional[NodeState]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM nodes WHERE hostname=%s", (hostname,))
            row = cur.fetchone()
        return NodeState(**row) if row else None

    # -------------------------------------------------------------------------
    # Events (append-only)
    # -------------------------------------------------------------------------
    def _write_event(self, job_id: str, event_type: str,
                     payload: Dict[str, Any]) -> None:
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO job_events (job_id, event_type, payload)
                   VALUES (%s,%s,%s)""",
                (job_id, event_type, Json(payload)))

    def get_job_events(self, job_id: str) -> List[Dict]:
        with self._cursor() as cur:
            cur.execute(
                """SELECT * FROM job_events
                   WHERE job_id=%s ORDER BY timestamp ASC""",
                (job_id,))
            return [dict(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # Scheduler scores audit
    # -------------------------------------------------------------------------
    def write_scheduler_decision(self, job_id: str, round_num: int,
                                  scores: List[Dict],
                                  selected_node: str) -> None:
        with self._cursor() as cur:
            for node_scores in scores:
                cur.execute(
                    """INSERT INTO scheduler_scores
                           (job_id, round_number, node_hostname,
                            score_breakdown, final_score,
                            selected)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (job_id, round_num,
                     node_scores["hostname"],
                     Json(node_scores),
                     node_scores["total_score"],
                     node_scores["hostname"] == selected_node))

    # -------------------------------------------------------------------------
    # Admission decisions
    # -------------------------------------------------------------------------
    def write_admission_decision(self, job_id: str, decision: str,
                                  reason: str,
                                  cluster_util: Dict) -> None:
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO admission_decisions
                       (job_id, decision, reason,
                        cluster_gpu_util, cluster_cpu_util,
                        queue_depth, load_at_decision)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (job_id or uuid.uuid4(), decision, reason,
                 cluster_util.get("avg_gpu_load_pct", 0),
                 cluster_util.get("avg_cpu_load_pct", 0),
                 cluster_util.get("total_queue_depth", 0),
                 cluster_util.get("avg_load", 0)))

    # -------------------------------------------------------------------------
    # Failure recoveries
    # -------------------------------------------------------------------------
    def write_failure_recovery(self, job_id: str, hostname: str,
                               failure_type: str,
                               recovery_action: str,
                               attempt: int,
                               success: bool) -> None:
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO failure_recoveries
                       (job_id, node_hostname, failure_type,
                        recovery_action, attempt_number,
                        success, finished_at)
                   VALUES (%s,%s,%s,%s,%s,%s,NOW())""",
                (job_id, hostname, failure_type,
                 recovery_action, attempt, success))

    def get_recent_failures(self, minutes: int = 60) -> List[Dict]:
        with self._cursor() as cur:
            cur.execute(
                """SELECT * FROM failure_recoveries
                   WHERE started_at > NOW() - INTERVAL '%s minutes'
                   ORDER BY started_at DESC""",
                (minutes,))
            return [dict(r) for r in cur.fetchall()]

    # -------------------------------------------------------------------------
    # Cluster state
    # -------------------------------------------------------------------------
    def get_cluster_state(self) -> Dict:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM cluster_state")
            rows = cur.fetchall()
        return {"nodes": [dict(r) for r in rows],
                "ts": datetime.utcnow().isoformat()}

    def get_total_utilization(self) -> Dict:
        with self._cursor(dict_cursor=False) as cur:
            cur.execute("SELECT get_total_cluster_utilization() as u")
            return cur.fetchone()[0]

    def close(self):
        StateStore._pool.putconn(self._conn)

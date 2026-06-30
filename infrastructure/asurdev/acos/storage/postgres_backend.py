"""ACOS PostgreSQL Storage Backend — primary persistent storage."""
import os
import json
from typing import Any
from datetime import datetime

try:
    import psycopg2
    HAS_PSYCOPG = True
except ImportError:
    HAS_PSYCOPG = False

class PostgresTraceStorage:
    """PostgreSQL-backed trace storage. Requires DATABASE_URL env var."""
    
    def __init__(self, conn_string: str | None = None):
        if not HAS_PSYCOPG:
            raise ImportError("psycopg2 required: pip install psycopg2-binary")
        self._conn_string = conn_string or os.environ.get("DATABASE_URL")
        if not self._conn_string:
            raise ValueError("DATABASE_URL environment variable not set")
        self._conn = None
    
    def _get_conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self._conn_string)
        return self._conn
    
    def write(self, trace: dict) -> str:
        import json
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO acos_traces (trace_id, trace)
                VALUES (%s, %s)
                ON CONFLICT (trace_id) DO UPDATE SET trace = EXCLUDED.trace
                """,
                (trace["trace_id"], json.dumps(trace))
            )
            conn.commit()
        return trace["trace_id"]
    
    def fetch(self, trace_id: str) -> dict | None:
        import json
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT trace FROM acos_traces WHERE trace_id = %s", (trace_id,))
            row = cur.fetchone()
            return json.loads(row[0]) if row else None
    
    def query(self, filters: dict | None = None) -> list[dict]:
        import json
        conn = self._get_conn()
        with conn.cursor() as cur:
            if not filters:
                cur.execute("SELECT trace FROM acos_traces ORDER BY created_at DESC LIMIT 100")
            else:
                # Simple key-value filter
                where = " AND ".join(f"trace->>%s = %s" for _ in filters)
                cur.execute(
                    f"SELECT trace FROM acos_traces WHERE {where} ORDER BY created_at DESC LIMIT 100",
                    list(filters.keys()) + list(filters.values())
                )
            return [json.loads(row[0]) for row in cur.fetchall()]
    
    def update(self, trace_id: str, patch: dict) -> None:
        import json
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE acos_traces SET trace = trace || %s WHERE trace_id = %s",
                (json.dumps(patch), trace_id)
            )
            conn.commit()

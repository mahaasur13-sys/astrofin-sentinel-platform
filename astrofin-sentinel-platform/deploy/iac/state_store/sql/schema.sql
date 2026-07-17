-- =============================================================================
-- HOME CLUSTER — SYSTEM OF RECORD (PostgreSQL)
-- All state: jobs, nodes, events, admission decisions
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for fuzzy search

-- ---------------------------------------------------------------------------
-- jobs — core job state
-- ---------------------------------------------------------------------------
CREATE TABLE jobs (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name           TEXT        NOT NULL,
    job_type       TEXT        NOT NULL,  -- 'gpu' | 'cpu' | 'arm' | 'vps'
    partition_name TEXT        NOT NULL,  -- 'gpu' | 'cpu' | 'arm' | 'vps'
    status         TEXT        NOT NULL   DEFAULT 'CREATED',
        -- CREATED → ADMITTED → SCHEDULED → RUNNING → SUCCESS
        --                ↓                      ↓
        --             REJECTED               FAIL
        --                                     ↓
        --                                  RETRY → SCHEDULED
    priority       INTEGER     NOT NULL DEFAULT 5,  -- 1-10, higher = more urgent
    retry_count    INTEGER     NOT NULL DEFAULT 0,
    max_retries    INTEGER     NOT NULL DEFAULT 3,
    memory_gb      INTEGER     NOT NULL,
    node_target    TEXT,                           -- assigned node hostname
    slurm_job_id   INTEGER,                        -- actual Slurm job ID
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at     TIMESTAMPTZ,
    finished_at    TIMESTAMPTZ,
    error_message  TEXT,
    script_path    TEXT,
    CHECK (priority BETWEEN 1 AND 10),
    CHECK (retry_count <= max_retries)
);

CREATE INDEX idx_jobs_status     ON jobs(status);
CREATE INDEX idx_jobs_type       ON jobs(job_type);
CREATE INDEX idx_jobs_priority   ON jobs(priority DESC);
CREATE INDEX idx_jobs_created    ON jobs(created_at DESC);

-- ---------------------------------------------------------------------------
-- job_events — immutable event log (append-only)
-- ---------------------------------------------------------------------------
CREATE TABLE job_events (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id      UUID        NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    event_type  TEXT        NOT NULL,
        -- JOB_CREATED | JOB_ADMITTED | JOB_REJECTED | JOB_SCHEDULED |
        -- JOB_STARTED | JOB_SUCCESS | JOB_FAIL | JOB_RETRY | JOB_CANCELLED |
        -- SCHEDULER_QUERY | NODE_HEALTH_UPDATE | ADMISSION_DECISION
    payload     JSONB       NOT NULL DEFAULT '{}',
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_job_id  ON job_events(job_id);
CREATE INDEX idx_events_type    ON job_events(event_type);
CREATE INDEX idx_events_ts       ON job_events(timestamp DESC);

-- ---------------------------------------------------------------------------
-- nodes — current cluster node state
-- ---------------------------------------------------------------------------
CREATE TABLE nodes (
    hostname        TEXT        PRIMARY KEY,
    roles           TEXT[]      NOT NULL DEFAULT '{}',
        -- ['slurm_controller','slurm_compute','ceph_osd','ceph_mon',
        --  'ray_head','ray_worker','wg_peer']
    gpu_count       INTEGER     NOT NULL DEFAULT 0,
    gpu_model       TEXT,
    cpu_cores       INTEGER     NOT NULL DEFAULT 0,
    memory_gb       INTEGER     NOT NULL DEFAULT 0,
    gpu_load_pct    NUMERIC(5,2) NOT NULL DEFAULT 0,  -- 0.00 to 100.00
    cpu_load_pct    NUMERIC(5,2) NOT NULL DEFAULT 0,
    memory_used_gb  NUMERIC(10,2) NOT NULL DEFAULT 0,
    health_score    NUMERIC(3)  NOT NULL DEFAULT 100,  -- 0-100
    status          TEXT        NOT NULL DEFAULT 'UNKNOWN',
        -- HEALTHY | DEGRADED | DOWN | MAINTENANCE | DRAINED
    last_seen       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_nodes_status   ON nodes(status);
CREATE INDEX idx_nodes_health   ON nodes(health_score ASC);

-- ---------------------------------------------------------------------------
-- admission_decisions — audit log for backpressure
-- ---------------------------------------------------------------------------
CREATE TABLE admission_decisions (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id          UUID,
    decision        TEXT        NOT NULL,  -- 'ADMIT' | 'REJECT'
    reason          TEXT,
    cluster_gpu_util NUMERIC(5,2),
    cluster_cpu_util NUMERIC(5,2),
    queue_depth      INTEGER,
    load_at_decision NUMERIC(5,2),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_adm_timestamp  ON admission_decisions(timestamp DESC);
CREATE INDEX idx_adm_decision   ON admission_decisions(decision);

-- ---------------------------------------------------------------------------
-- failure_recoveries — failure tracking for single-path guarantee
-- ---------------------------------------------------------------------------
CREATE TABLE failure_recoveries (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id          UUID        REFERENCES jobs(id) ON DELETE SET NULL,
    node_hostname   TEXT        NOT NULL,
    failure_type    TEXT        NOT NULL,
        -- GPU_OOM | NODE_CRASH | NETWORK_PARTITION | CEPH_OSD_DOWN |
        -- SLURM_WORKER_DOWN | RAY_WORKER_CRASH | WIREGUARD_DROP
    recovery_action TEXT        NOT NULL,
    attempt_number  INTEGER     NOT NULL DEFAULT 1,
    success         BOOLEAN,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX idx_fail_node      ON failure_recoveries(node_hostname);
CREATE INDEX idx_fail_job      ON failure_recoveries(job_id);
CREATE INDEX idx_fail_type     ON failure_recoveries(failure_type);

-- ---------------------------------------------------------------------------
-- scheduler_scores — decision audit trail (for determinism testing)
-- ---------------------------------------------------------------------------
CREATE TABLE scheduler_scores (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id              UUID        NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    round_number        INTEGER     NOT NULL DEFAULT 1,
    node_hostname       TEXT        NOT NULL,
    score_breakdown     JSONB       NOT NULL DEFAULT '{}',
        -- {gpu: 42.5, cpu: 15.2, mem: 8.1, latency: -2.0, locality: 3.0, total: 66.8}
    final_score         NUMERIC(8,4) NOT NULL,
    selected            BOOLEAN     NOT NULL DEFAULT FALSE,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ss_job         ON scheduler_scores(job_id);
CREATE INDEX idx_ss_round        ON scheduler_scores(round_number);
CREATE INDEX idx_ss_selected     ON scheduler_scores(selected) WHERE selected = TRUE;

-- ---------------------------------------------------------------------------
-- TRIGGER: auto-update updated_at
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_nodes_updated_at
    BEFORE UPDATE ON nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ---------------------------------------------------------------------------
-- VIEW: cluster_state (denormalized current snapshot)
-- ---------------------------------------------------------------------------
CREATE VIEW cluster_state AS
SELECT
    n.hostname,
    n.roles,
    n.gpu_count,
    n.cpu_cores,
    n.memory_gb,
    n.gpu_load_pct,
    n.cpu_load_pct,
    n.memory_used_gb,
    n.memory_gb - n.memory_used_gb  AS memory_free_gb,
    n.health_score,
    n.status,
    n.last_seen,
    -- queue depth from Slurm
    COALESCE(q.queue_depth, 0)     AS queue_depth,
    COALESCE(q.running_jobs, 0)    AS running_jobs
FROM nodes n
LEFT JOIN LATERAL (
    SELECT COUNT(*) FILTER (WHERE state = 'RUNNING')  AS running_jobs,
           COUNT(*) FILTER (WHERE state IN ('PENDING','CONFIGURING')) AS queue_depth
    FROM jobs
    WHERE node_target = n.hostname
) q ON TRUE;

-- ---------------------------------------------------------------------------
-- FUNCTION: get_total_cluster_utilization()
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_total_cluster_utilization()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_gpu_count',     SUM(gpu_count),
        'total_memory_gb',     SUM(memory_gb),
        'avg_gpu_load_pct',    ROUND(AVG(gpu_load_pct)::NUMERIC, 2),
        'avg_cpu_load_pct',    ROUND(AVG(cpu_load_pct)::NUMERIC, 2),
        'avg_memory_used_pct', ROUND(AVG(memory_used_gb::NUMERIC / NULLIF(memory_gb,0) * 100)::NUMERIC, 2),
        'total_queue_depth',   SUM(
            CASE WHEN status = 'CREATED' THEN 1 ELSE 0 END
        ),
        'total_running',       SUM(
            CASE WHEN status = 'RUNNING' THEN 1 ELSE 0 END
        ),
        'healthy_nodes',       COUNT(*) FILTER (WHERE status = 'HEALTHY'),
        'degraded_nodes',      COUNT(*) FILTER (WHERE status = 'DEGRADED'),
        'down_nodes',          COUNT(*) FILTER (WHERE status = 'DOWN')
    ) INTO result
    FROM nodes;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

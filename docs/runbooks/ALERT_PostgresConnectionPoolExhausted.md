# ALERT: PostgresConnectionPoolExhausted

## Severity
**HIGH** — all `/agent/run` and `/dashboard` requests fail with 500 until resolved.

## Symptoms

- Grafana: `asyncpg_pool_available_connections == 0`
- App: `psycopg.OperationalError: connection pool exhausted` in logs
- `/health` deep check: `DB: FAIL` (connection timeout)
- `/dashboard`: 500, `"error": "database unavailable"`
- All agent responses return `NEUTRAL` (fallback path)

## Cause Classification

| Cause | Check |
|-------|-------|
| Hung long-running query | `SELECT pid, state, now() - query_start FROM pg_stat_activity WHERE state = 'active'` |
| Connection leak (agent not releasing) | Pool metrics: `asyncpg_pool_checked_out` steadily rising |
| Load spike | `docker stats postgres`, `pg_stat_activity` count > 40 |
| Deadlock | `SELECT * FROM pg_locks WHERE NOT granted` |

## Actions (5-minute response)

### Step 1: Check current state

```bash
cd /home/workspace
docker-compose exec postgres psql -U astrofin -d astrofin -c "
  SELECT count(*) AS total_connections,
         count(*) FILTER (WHERE state = 'active') AS active,
         count(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_txn
  FROM pg_stat_activity
  WHERE datname = 'astrofin';
"
```

### Step 2: Identify hung queries

```sql
SELECT pid,
       state,
       now() - query_start AS duration,
       left(query, 120) AS query_preview
FROM pg_stat_activity
WHERE state = 'active'
  AND datname = 'astrofin'
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY duration DESC
LIMIT 10;
```

### Step 3: Kill hung queries (if safe)

```sql
-- Kill queries running > 5 minutes (careful — may be important)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < now() - interval '5 minutes'
  AND datname = 'astrofin'
  AND query NOT ILIKE '%pg_stat%';
```

### Step 4: Add headroom

If Step 2 shows systemic issue (not a single hung query):

```bash
# Increase pool max
# In .env (or .env.prod):
DB_POOL_MAX_SIZE=50     # was 20
DB_POOL_MIN_SIZE=5      # was 2

# Restart app
systemctl restart astrofin-api  # or docker-compose restart api
```

### Step 5: Verify recovery

```bash
docker-compose exec postgres psql -U astrofin -d astrofin -c "
  SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
"
# Should be < 40
curl http://localhost:8000/health | jq '.checks.db'
# Should be "ok"
```

## If No Postgres Available At All

→ **WAL-G restore** on replica (see `docs/runbooks/WALG_RESTORE_DRILL.md`)

## Escalation

| After | Action |
|-------|--------|
| 5 min | Ping `#oncall-astrofin` in Slack |
| 10 min | Call on-call primary |
| 15 min | PagerDuty page (severity: critical) |

## Prevention

- Monitor `asyncpg_pool_available_connections` in Grafana — alert at < 3
- Set `idle_in_transaction_session_timeout = 5min` in `postgresql.conf`
- Connection pool: use async context manager (`async with pool.acquire()`)
- Review agent code for `await conn.close()` in finally blocks
- Monthly: run `pg_stat_statements` to identify slow queries, add indexes

## Related

- `docs/runbooks/WALG_RESTORE_DRILL.md` — full database disaster recovery
- `docs/performance/query-baseline.md` — expected query performance
- `deploy/monitoring/recording_rules.yml` — SLO alarms

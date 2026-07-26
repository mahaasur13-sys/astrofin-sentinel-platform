# ALERT: Storm Response (≥20 alerts/min)

## Detection

Grafana dashboard: Alertmanager → Alerts Firing Rate.

- **Warning:** > 10 alerts/min for > 2 min
- **Critical:** > 50 alerts/min for > 1 min

## Immediate Actions (5 min)

### 1. Identify root cause

\`\`\`bash
# Check what's firing
curl -s http://localhost:9093/api/v2/alerts | jq '.[].labels.alertname' | sort | uniq -c | sort -rn
\`\`\`

### 2. Silence by pattern

\`\`\`bash
# Silence all "TestAlert_*" for 30 min
amtool silence add alertname=~"TestAlert_.*" --duration=30m --comment="Storm response"
\`\`\`

### 3. Check system health

\`\`\`bash
curl http://localhost:8000/health | jq .
curl http://localhost:8000/readyz | jq .
docker stats --no-stream
\`\`\`

### 4. If agent errors

\`\`\`bash
# Check agent logs for exceptions
docker compose logs api | grep -i "error\|exception\|timeout" | tail -50
\`\`\`

## Root Causes & Fixes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| All agents reporting error | External API down (CoinGecko, Ephemeris) | Circuit breaker should handle; check `core/external/circuit_breaker.py` |
| DB connection pool exhausted | Long-running query | Kill hung queries → `SELECT pg_terminate_backend(pid)` |
| Redis connection refused | Redis OOM | `redis-cli FLUSHDB` (only if rate limiter + cache) |
| Meta-RL inference timeout | Checkpoint stale | Fallback to static weights is automatic |

## Escalation

- **If > 50 alerts/min > 5 min:** PagerDuty page on-call
- **If DB-related:** escalate to DBA
- **If external API:** check status.coingecko.com, wait for recovery

## Prevention

- Circuit breakers on all external calls (already in place)
- Rate limiter prevents cascading failures
- Alert grouping: `group_by: [alertname, severity]` in Alertmanager config
- Dedup: `group_interval: 5m` prevents repeated notifications

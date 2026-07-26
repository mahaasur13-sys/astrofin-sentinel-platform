# ALERT: RedisMemoryHigh

## Severity
**MEDIUM** — performance degrades (cache misses increase, rate limiter resets), but app stays up.

## Symptoms

- `redis_memory_used_bytes > 80%` of `maxmemory` (Grafana alert fires)
- `redis_evicted_keys_total` rate > 0
- Latency spikes on `/agent/run` (cache misses for Meta-RL weights)
- Rate limiter starts rejecting valid requests (because Redis can't store counters)

## Cause Classification

| Cause | Check |
|-------|-------|
| Key accumulation (no TTL) | `redis-cli --bigkeys` — keys with `ttl=-1` |
| Rate limiter leak | `redis-cli KEYS 'rate_limit:*' \| wc -l` |
| Cache growth (RAG/LLM) | `redis-cli KEYS 'rag:*' \| wc -l` |
| Session bloat | `redis-cli KEYS 'session:*' \| wc -l` |
| Large key values | `redis-cli --bigkeys --memkeys` |

## Actions (5-minute response)

### Step 1: Diagnose

```bash
# Memory overview
docker-compose exec redis redis-cli INFO memory | grep -E 'used_memory_human|maxmemory_human|evicted_keys|mem_fragmentation_ratio'

# Top 5 largest keys
docker-compose exec redis redis-cli --bigkeys -i 0.1 | head -20

# Keys without TTL (potential leak)
docker-compose exec redis redis-cli --scan --pattern '*' 2>/dev/null | while read k; do
  ttl=$(docker-compose exec redis redis-cli TTL "$k")
  if [ "$ttl" = "-1" ]; then echo "NO_TTL: $k"; fi
done | head -20
```

### Step 2: Classify and act

```bash
# If rate limiter keys dominate (>10K keys):
docker-compose exec redis redis-cli --scan --pattern 'rate_limit:*' | xargs docker-compose exec redis redis-cli DEL

# If RAG cache dominates (>100MB):
docker-compose exec redis redis-cli --scan --pattern 'rag:*' | xargs docker-compose exec redis redis-cli DEL
# Then verify: curl http://localhost:8000/health | jq '.checks.redis'

# If sessions dominate:
docker-compose exec redis redis-cli --scan --pattern 'session:*' | xargs docker-compose exec redis redis-cli DEL
# WARNING: logs out all users — only use as last resort
```

### Step 3: Emergency flush (last resort)

```bash
# FLUSHDB (clears current DB) — use only if:
# 1. Rate limiter is self-inflicted lockout (>50% rejections)
# 2. App is unusable
# 3. Sessions can be re-established
docker-compose exec redis redis-cli FLUSHDB
# OR targeted:
docker-compose exec redis redis-cli --scan --pattern 'rate_limit:*' | xargs docker-compose exec redis redis-cli DEL
docker-compose exec redis redis-cli --scan --pattern 'rag:*' | xargs docker-compose exec redis redis-cli DEL
```

### Step 4: Verify recovery

```bash
docker-compose exec redis redis-cli INFO memory | grep used_memory_human
# Should be < 70% of maxmemory
curl http://localhost:8000/agent/run -X POST -H 'Content-Type: application/json' -d '{"agentId":"12","prompt":"test"}' | jq '.status'
# Should return normally, not 429
```

### Step 5: Apply permanent fix

```bash
# Set eviction policy (if not already set)
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Persist in redis.conf or docker-compose:
# command: redis-server --maxmemory-policy allkeys-lru --maxmemory 512mb
```

## Escalation

| After | Action |
|-------|--------|
| 5 min | Ping `#oncall-astrofin` in Slack |
| 10 min | Call on-call backup |
| 15 min | PagerDuty page (severity: warning) |

## Prevention

- Set `maxmemory` explicitly: `--maxmemory 512mb` in docker-compose
- Set `maxmemory-policy allkeys-lru` (auto-evicts old keys)
- Monitor in Grafana:
  - `redis_memory_used_bytes / redis_config_maxmemory_bytes * 100` (alert > 80%)
  - `rate(redis_evicted_keys_total[5m])` (alert > 0)
- Ensure all application keys have TTL:
  - rate limit: 60s
  - sessions: 3600s
  - RAG cache: 300s
  - LLM cache: 600s

## Related

- `docker-compose.yml` — Redis service config
- `core/rate_limiter.py` — Rate limiter Redis backend
- `meta_rl/persistence.py` — Meta-RL checkpoint (uses Redis if available)

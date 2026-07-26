# ALERT: DashboardLatencyHigh

**Alert rule:** `DashboardLatencyHigh` — p95 latency > 200ms for `/api/v1/dashboard`

## Step 1: Verify

```bash
curl -w "\n%{time_total}s\n" -o /dev/null -s http://localhost:8000/api/v1/dashboard?symbol=BTCUSDT
```

If `time_total` < 0.3s — transient spike, wait 5 min and re-check.

## Step 2: Check DB Pool

```bash
docker exec astrofin-postgres psql -U astrofin -c "SELECT count(*) FROM pg_stat_activity WHERE datname='astrofin';"
```

If count > 15 — pool near max. Check for stuck queries:

```bash
docker exec astrofin-postgres psql -U astrofin -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state='active' ORDER BY duration DESC LIMIT 5;"
```

## Step 3: Check CoinGecko

```bash
curl -w "\n%{time_total}s\n" -o /dev/null -s "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=90"
```

If `time_total` > 2s — CoinGecko degraded. Circuit breaker should be open. Check:

```bash
curl http://localhost:8000/metrics | grep circuit_breaker_state
```

## Step 4: Scale Up (if persistent)

1. Increase pool: `POSTGRES_POOL_MAX=30` in `.env`, restart API
2. Add Redis cache layer for CoinGecko responses (TTL 60s)

## Escalation

After 15 min unresolved → escalate to PagerDuty (primary on-call).

# Stress Test — 100 RPS Breaking Point

> **Date:** (заполнить после выполнения)  |  **Tester:** Felix / asurdev
> **Environment:** staging (docker-compose.staging.yml)

## Methodology

\`\`\`bash
docker-compose -f docker-compose.staging.yml up -d
sleep 15
locust -f tests/load/locustfile_sprint_e.py --host http://localhost:8000 -u 100 -r 10 --run-time 15m --html docs/performance/stress-test-100rps.html
\`\`\`

## Results

| Metric | 50 RPS (Sprint E) | 100 RPS (Hardening) | Breaking Point |
|--------|-------------------|---------------------|----------------|
| Dashboard p95 | (fill) ms | (fill) ms | (fill) RPS |
| Agent/Run p95 | (fill) ms | (fill) ms | (fill) RPS |
| Error rate | (fill) % | (fill) % | (fill) % |
| CPU % | (fill) | (fill) | — |
| Memory MB | (fill) | (fill) | — |
| DB connections | (fill) | (fill) | — |

## Target SLO

- /dashboard: p95 < 200ms, error rate < 0.1%
- /agent/run: p95 < 800ms, error rate < 0.1%
- /health: p95 < 50ms, error rate 0%

## Breaking Point Definition

The RPS at which **either**:
1. Dashboard p95 > 500ms
2. Agent/run p95 > 2000ms
3. Error rate > 1%

This defines the **horizontal scaling ceiling** for v1.0.0.

## Analysis

(Заполнить после выполнения — что стало узким местом, какие оптимизации нужны)

## Recommendations

- If DB pool exhausted → increase `DB_POOL_MAX_SIZE` 50→80
- If Meta-RL inference slow → add async cache TTL 60s
- If CPU-bound → scale to 2 web workers

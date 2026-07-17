# P2-04 RAG Observability

## Overview

This sprint adds labeled Prometheus metrics across the RAG retrieval stack so
we can answer operational questions that used to be invisible:

- Are queries flowing? At what rate, and to which backend?
- How slow are they, in p50/p95?
- How often do they fail, and at which stage?
- Is the in-process BM25 index fresh?
- How many chunks do we actually return per query?
- What's the relevance quality of the most recent results?

All metrics are exposed by `tools/metrics_server.py` on `/metrics` (default
port 9091). Authentication is optional via `METRICS_AUTH_ENABLED` and
`METRICS_API_KEY`.

## Metrics

### `astrofin_rag_queries_total` (Counter, labeled)

Total RAG queries, partitioned by:

| Label    | Values                              |
|----------|-------------------------------------|
| `status` | `ok` \| `error`                     |
| `backend`| `pgvector` \| `faiss` \| `hybrid`   |
| `domain` | `trading` \| `technical` \| `astrology` \| `general` \| `all` |

Replaces the legacy `astrofin_rag_query_cache_hits` / `astrofin_rag_query_cache_misses`
counters, which conflated cache semantics with success semantics.

Example PromQL:

```promql
# Total QPS
sum(rate(astrofin_rag_queries_total[5m]))

# Error rate
sum(rate(astrofin_rag_queries_total{status="error"}[5m]))
  / sum(rate(astrofin_rag_queries_total[5m]))

# QPS by backend
sum by (backend) (rate(astrofin_rag_queries_total[5m]))
```

### `astrofin_rag_errors_total` (Counter, labeled)

RAG errors by failure stage and exception kind.

| Label   | Values                                          |
|---------|-------------------------------------------------|
| `stage` | `retrieve` \| `retrieve_fallback` \| `store`    |
| `kind`  | exception class name (e.g. `AttributeError`)    |

Example PromQL:

```promql
# Errors by stage
sum by (stage) (rate(astrofin_rag_errors_total[5m]))
```

### `astrofin_rag_latency_seconds` (Histogram)

End-to-end RAG query latency, observed from the moment `RAGClient.retrieve()`
is called until the result is returned (or the exception is raised).

Buckets: `0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0` (seconds).

Example PromQL:

```promql
# p50, p95, p99 latency
histogram_quantile(0.50, sum by (le) (rate(astrofin_rag_latency_seconds_bucket[5m])))
histogram_quantile(0.95, sum by (le) (rate(astrofin_rag_latency_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(astrofin_rag_latency_seconds_bucket[5m])))
```

### `astrofin_rag_chunks_returned` (Histogram)

Number of chunks returned per query, post-filter (i.e. after `min_score`).
Used to spot queries that are returning too few (or too many) chunks.

Buckets: `0, 1, 2, 3, 5, 8, 13, 21`.

Example PromQL:

```promql
# p50 chunks per query
histogram_quantile(0.50, sum by (le) (rate(astrofin_rag_chunks_returned_bucket[5m])))
```

### `astrofin_rag_relevance_score` (Histogram)

Per-chunk relevance score distribution. The `observe()` call happens for each
chunk in each successful retrieval.

Buckets: `0.1, 0.3, 0.5, 0.7, 0.9, 1.0`.

### `astrofin_rag_relevance_avg` (Gauge)

The average relevance score of the most recent query. Set on every successful
retrieval from both `core.rag_client` and `knowledge.rag_retriever`.

### `astrofin_rag_bm25_refresh_timestamp` (Gauge)

Unix epoch (seconds) at which the in-process BM25 index was last built by
`PersistentBM25Retriever.refresh()`. Value `0` means "never built".

Watch for stalls: if this stops advancing, `refresh()` is broken or
`HybridRetriever` is not being instantiated.

```promql
# Age in seconds
time() - astrofin_rag_bm25_refresh_timestamp
```

### Legacy / back-compat

The following metrics are kept as deprecated no-op Counters so old import
paths don't break. New code must use the labeled metrics above.

- `astrofin_rag_query_cache_hits` (use `astrofin_rag_queries_total{status="ok"}`)
- `astrofin_rag_query_cache_misses` (use `astrofin_rag_queries_total{status="error"}`)

Removal is scheduled for P2-05.

## Instrumented call sites

| Metric                          | `core/rag_client` | `knowledge/rag_retriever` | `knowledge/persistent_bm25_retriever` |
|---------------------------------|:-----------------:|:-------------------------:|:-------------------------------------:|
| `RAG_QUERIES_TOTAL`             | ✅ retrieve       | ✅ retrieve               | —                                     |
| `RAG_ERRORS_TOTAL`              | ✅ retrieve, store| ✅ retrieve               | —                                     |
| `RAG_LATENCY_SECONDS`           | ✅ retrieve       | ✅ retrieve               | ✅ refresh                            |
| `RAG_CHUNKS_RETURNED`           | ✅ retrieve       | ✅ retrieve               | —                                     |
| `RAG_RELEVANCE_AVG`             | ✅ retrieve       | ✅ retrieve               | —                                     |
| `RAG_RELEVANCE_SCORE` (hist)    | ✅ retrieve       | ✅ retrieve               | —                                     |
| `RAG_BM25_REFRESH_TIMESTAMP`    | —                 | —                         | ✅ refresh                            |

Both the new pgvector path (`RAGClient`) and the legacy FAISS path
(`RAGRetriever`) emit the same metric names — that was the whole point of
this sprint: a single set of panels regardless of which backend the request
landed on.

## Grafana dashboard

`deploy/monitoring/grafana/rag_dashboard.json` ships a ready-to-import
dashboard with nine panels:

1. **Throughput** (queries/s by backend)
2. **Error Rate** (single-stat with thresholds)
3. **Latency p50/p95/p99** (time series)
4. **Errors by stage × kind** (time series)
5. **BM25 Index Last Refresh** (single-stat, "0 = never")
6. **BM25 Index Age** (single-stat with red/yellow/green thresholds)
7. **Chunks Returned** (p50/p95 time series)
8. **Avg Relevance Score** (time series)
9. **Errors by Stage (total)** (bar gauge for the selected time range)

To import:

1. Open Grafana → Dashboards → Import.
2. Upload `deploy/monitoring/grafana/rag_dashboard.json`.
3. Select your Prometheus datasource when prompted.
4. The dashboard assumes `/metrics` is scraped from the `tools/metrics_server`
   process (default port 9091). If you scrape through a service mesh sidecar,
   adjust the datasource job label to match.

## Local smoke check

```bash
# In one terminal: start the metrics server
python -m tools.metrics_server --port 9091

# In another: do a few RAG queries (pgvector backend)
python -c "import asyncio; from core.rag_client import get_rag_client; \
asyncio.run(get_rag_client().retrieve('test query', top_k=3))"

# Curl the metrics
curl -s http://localhost:9091/metrics | grep -E '^(astrofin_rag_|# HELP astrofin_rag_)'
```

You should see non-zero `astrofin_rag_queries_total` and at least one
`astrofin_rag_latency_seconds` sample.

## Migration notes (from P2-03c / pre-P2-04)

- The previous `_update_rag_metrics` static method on `RAGClient` was a no-op
  shim (it called `.set(avg)` on a `Histogram`, which silently failed). It
  is kept as a back-compat shim but is not used in the new code paths.
- `tools/rag_admin.py` was updated to read from the new labeled
  `RAG_QUERIES_TOTAL` counter via `REGISTRY.collect()` instead of the legacy
  `_value.get()` on the bare Counter.
- Old Grafana panels that reference `astrofin_rag_query_cache_hits` /
  `astrofin_rag_query_cache_misses` will read zero — please update them to
  `astrofin_rag_queries_total{status="ok"}` / `{status="error"}` respectively.

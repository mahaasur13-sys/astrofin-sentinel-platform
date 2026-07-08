# Kubernetes Probes Configuration

This document explains how to wire the AstroFin Sentinel web service into
Kubernetes using the liveness and readiness probes exposed by
`deploy/monitoring/health_endpoints.py`.

## Available endpoints

| Path       | Purpose                              | Expected latency |
|------------|--------------------------------------|------------------|
| `/livez`   | Liveness — process is up             | < 5 ms           |
| `/readyz`  | Readiness — downstream deps reachable| < 200 ms         |
| `/health`  | Legacy alias for `/livez`            | < 5 ms           |
| `/metrics` | Prometheus metrics (text format)     | < 50 ms          |

## Recommended probe configuration

```yaml
livenessProbe:
  httpGet:
    path: /livez
    port: http
  initialDelaySeconds: 15
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /readyz
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /livez
    port: http
  failureThreshold: 30
  periodSeconds: 5
```

## Why three probes

- **`/livez`** answers as long as the Python process is responsive. The
  kubelet will restart the container only if it stops answering.
- **`/readyz`** checks Redis, Postgres, and any in-process caches. When it
  fails the pod is removed from Service endpoints (no traffic), but not
  restarted — letting the downstream recover.
- **`/metrics`** is scraped by Prometheus on a separate port via the
  annotations `prometheus.io/scrape: "true"`, `prometheus.io/port: "8050"`.

## Graceful shutdown interaction

When a `SIGTERM` is received the WSGI app (see `web/wsgi.py`) flips
`/readyz` to return `503` and `/health` continues to answer `200` until the
drain timeout expires. This gives Kubernetes enough time to remove the
pod from the Service endpoints before the process exits.

The `terminationGracePeriodSeconds` should be at least 30 s to allow
draining in-flight requests:

```yaml
spec:
  terminationGracePeriodSeconds: 30
```

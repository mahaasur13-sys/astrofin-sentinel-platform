# AstroFin Sentinel V5 - Deployment Guide

## Quick Start

```bash
# Development
cd deploy/docker
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| app | 8000 | Main application |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache |
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Visualization |

## Health Checks

```bash
# App health
curl http://localhost:8000/health

# KARL metrics
curl http://localhost:8000/metrics/karl

# Prometheus targets
curl http://localhost:9090/api/v1/targets
```

## Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check pods
kubectl get pods -l app=astrofin

# View logs
kubectl logs -l app=astrofin -f
```

## Alerts

Configured alerts:
- `HighOOSFailRate` - OOS fail > 35%
- `KARLDrift` - System drift detected
- `LowWinRate` - Win rate < 50%
- `HighDrawdown` - Drawdown > 15%
- `DatabaseDown` - PostgreSQL unreachable
- `RedisDown` - Redis unreachable

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql://... | PostgreSQL connection |
| REDIS_URL | redis://... | Redis connection |
| LOG_LEVEL | INFO | Logging level |
| KARL_SYNC_INTERVAL | 10 | KARL sync interval |
| KARL_DECISION_THRESHOLD | 0.65 | Min confidence threshold |

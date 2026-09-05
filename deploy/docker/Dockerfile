FROM python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534  # refresh: docker buildx imagetools inspect python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt* ./

# Install Python dependencies
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy application code
COPY . .

# Make the app entrypoint executable for the non-root user
RUN chmod +x /app/deploy/docker/app-entrypoint.sh

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check — the daemon (orchestration.sentinel_v5) serves Prometheus
# /metrics on METRICS_PORT (9191), not :8000. Check the port it actually binds.
# Token is the shared compose secret (same source Prometheus uses).
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f -H "Authorization: Bearer $(cat /run/secrets/metrics_token)" http://localhost:9191/metrics || exit 1

ENTRYPOINT ["/app/deploy/docker/app-entrypoint.sh"]

CMD ["python", "-m", "orchestration.sentinel_v5"]

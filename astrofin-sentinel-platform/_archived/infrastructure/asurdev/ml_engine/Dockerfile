FROM python:3.12-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists*
COPY pyproject.toml .
RUN pip install --no-user --prefix=/install -e .

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists*
WORKDIR /app
COPY --from=builder /install /usr/local
COPY ml_engine/ ml_engine/
COPY models/    models/
RUN useradd -m -r acos && chown -R acos:acos /app
USER acos
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/health')"
ENTRYPOINT ["python", "-m", "uvicorn", "ml_engine.inference.api:app", "--host", "0.0.0.0", "--port", "8081"]
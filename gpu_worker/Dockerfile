FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir --break-system-packages httpx pydantic
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "bridge.roma.gpu_worker.server"]

import time

import psutil
from fastapi import FastAPI

app = FastAPI()
app.state.start_time = time.time()


@app.get("/health")
def health():
    return {"status": "alive", "uptime": time.time() - app.state.start_time}


@app.get("/metrics")
def metrics():
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_used_mb": mem.used // 2**20,
        "memory_total_mb": mem.total // 2**20,
        "uptime_seconds": time.time() - app.state.start_time,
        "timestamp": time.time(),
    }


@app.get("/metrics/gpu")
def gpu_metrics():
    return {"gpus": []}  # In production: nvidia-smi query


@app.get("/metrics/queue")
def queue_metrics():
    return {"depth": 0, "scheduled": 0, "completed": 0, "failed": 0}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)

import threading
import time
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
workers: Dict[str, dict] = {}
_lock = threading.Lock()

class WorkerRegister(BaseModel):
    worker_id: str
    gpu_id: str
    gpu_mem_mb: int
    status: str = "alive"

@app.get("/health")
def health():
    return {"status": "alive", "workers": len(workers)}

@app.post("/register")
def register(w: WorkerRegister):
    with _lock:
        workers[w.worker_id] = {"worker_id": w.worker_id, "gpu_id": w.gpu_id, "gpu_mem_mb": w.gpu_mem_mb, "status": w.status, "last_seen": time.time()}
    return {"registered": w.worker_id}

@app.get("/workers")
def list_workers():
    return {"workers": list(workers.values())}

@app.post("/heartbeat")
def heartbeat(worker_id: str):
    with _lock:
        if worker_id in workers:
            workers[worker_id]["last_seen"] = time.time()
            return {"ok": True}
    return {"ok": False}

def heartbeat_loop():
    while True:
        time.sleep(10)
        with _lock:
            now = time.time()
            for wid in list(workers.keys()):
                if now - workers[wid]["last_seen"] > 30:
                    workers[wid]["status"] = "timeout"

@app.on_event("startup")
def start():
    t = threading.Thread(target=heartbeat_loop, daemon=True)
    t.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

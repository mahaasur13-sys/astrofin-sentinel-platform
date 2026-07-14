from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import threading
import time

app = FastAPI()
locks = {}
_lock = threading.Lock()

class LockReq(BaseModel):
    gpu_id: str
    job_id: str
    ttl_seconds: int = 3600

@app.get("/health")
def health(): return {"status": "alive", "locked_gpus": len(locks)}

@app.post("/lock/acquire")
def acquire(req: LockReq):
    with _lock:
        if req.gpu_id in locks and time.time() < locks[req.gpu_id]["expires_at"]:
            if locks[req.gpu_id]["job_id"] != req.job_id:
                raise HTTPException(status_code=409, detail="Already locked")
        locks[req.gpu_id] = {"gpu_id": req.gpu_id, "job_id": req.job_id, "expires_at": time.time() + req.ttl_seconds}
    return {"acquired": req.gpu_id, "ttl_seconds": req.ttl_seconds}

@app.post("/lock/release")
def release(gpu_id: str, job_id: str):
    with _lock:
        if gpu_id in locks and locks[gpu_id]["job_id"] == job_id:
            del locks[gpu_id]
            return {"released": gpu_id}
    raise HTTPException(status_code=403, detail="Not owner or not locked")

@app.get("/lock/status/{gpu_id}")
def status(gpu_id: str):
    with _lock:
        if gpu_id in locks:
            l = locks[gpu_id]
            return {"locked": True, "job_id": l["job_id"], "expires_in": max(0, l["expires_at"] - time.time())}
    return {"locked": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

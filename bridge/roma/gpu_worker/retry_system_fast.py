import threading
import time
from collections import deque

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
failed_queue = {}
RETRY_DELAYS = [10, 30, 60, 120, 300]
recovered = deque(maxlen=100)


class RetryReq(BaseModel):
    job_id: str
    error: str


@app.get("/health")
def health():
    return {"status": "alive", "pending": len(failed_queue)}


@app.post("/retry/add")
def add_retry(req: RetryReq):
    if req.job_id not in failed_queue:
        failed_queue[req.job_id] = {
            "job_id": req.job_id,
            "error": req.error,
            "attempt": 1,
            "next_retry": time.time() + RETRY_DELAYS[0],
            "created_at": time.time(),
        }
    else:
        f = failed_queue[req.job_id]
        f["attempt"] += 1
        if f["attempt"] <= len(RETRY_DELAYS):
            f["next_retry"] = time.time() + RETRY_DELAYS[f["attempt"] - 1]
    return {"queued": req.job_id, "attempt": failed_queue[req.job_id]["attempt"]}


@app.get("/retry/pending")
def get_pending():
    now = time.time()
    return {
        "pending": len(failed_queue),
        "jobs": [f for f in failed_queue.values() if f["next_retry"] <= now],
    }


@app.post("/retry/remove/{job_id}")
def remove(job_id: str):
    if job_id in failed_queue:
        failed_queue.pop(job_id)
        return {"removed": job_id}
    return {"removed": None}


def cleanup_loop():
    while True:
        time.sleep(30)
        now = time.time()
        for jid in [k for k, v in failed_queue.items() if v["expires_at"] < now]:
            failed_queue.pop(jid, None)


@app.on_event("startup")
def start():
    t = threading.Thread(target=cleanup_loop, daemon=True)
    t.start()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

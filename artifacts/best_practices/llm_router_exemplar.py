"""
BEST PRACTICE EXEMPLAR: LLM Router (core/llm_router.py)

Why this is an exemplar:
1. LAZY INITIALIZATION — OpenAI client and SentenceTransformer are loaded only when
   first needed, not at module import time. This prevents crashes when
   OPENROUTER_API_KEY is missing and allows apps to import the module safely.

2. SINGLE RESPONSIBILITY — Each function does exactly one thing:
   - classify_complexity() → decides local vs cloud
   - local_llm() / cloud_llm() → calls the respective backend
   - route() → orchestrates the flow
   - log_request() → persists audit trail

3. AUDIT TRAIL — Every LLM request is logged to JSONL with timestamp, backend,
   model, and response length. This enables offline analysis and cost tracking.

4. SESSION CACHING — TTL-based cache prevents jitter from re-classifying the
   same prompt within 5 minutes.

5. GRACEFUL DEGRADATION — If OPENROUTER_API_KEY is not set, a clear RuntimeError
   is raised (not a cryptic traceback).

PATTERNS TO REPLICATE:
- Lazy global state via _get_*() factory functions
- JSONL logging for observability
- TTL caching for expensive operations
- Explicit error messages for missing configuration
"""

import json
import os
import time
from pathlib import Path

import numpy as np
import ollama
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# ── Lazy clients ───────────────────────────────────────────────────────
_cloud_client = None
_embedder = None


def _get_cloud_client():
    global _cloud_client
    if _cloud_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. "
                "Set it in .env or export OPENROUTER_API_KEY=sk-or-v1-..."
            )
        _cloud_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return _cloud_client


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

# ── Session cache (TTL 5 min) ──────────────────────────────────────────
_session_last_model: dict[str, str] = {}
_session_last_call: dict[str, float] = {}
TTL = 300

# ── Complexity centroids ───────────────────────────────────────────────
_centroids_computed = False
_simple_centroid = None
_complex_centroid = None


def _init_centroids():
    global _centroids_computed, _simple_centroid, _complex_centroid
    if not _centroids_computed:
        embedder = _get_embedder()
        _simple_centroid = embedder.encode("fix formatting of the report")
        _complex_centroid = embedder.encode(
            "analyze correlation between VIX and S&P 500 options flow"
        )
        _centroids_computed = True

# ── Logging ────────────────────────────────────────────────────────────
LOG_FILE = Path("logs/llm_requests.jsonl")
LOG_FILE.parent.mkdir(exist_ok=True)


def log_request(prompt: str, backend: str, model: str, response: str) -> None:
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({
            "timestamp": time.time(),
            "prompt": prompt[:100],
            "backend": backend,
            "model": model,
            "response_length": len(response),
        }) + "\n")


def classify_complexity(prompt: str) -> str:
    _init_centroids()
    embedder = _get_embedder()
    vec = embedder.encode(prompt)
    sim_simple = np.dot(vec, _simple_centroid)
    sim_complex = np.dot(vec, _complex_centroid)
    return "local" if sim_simple > sim_complex else "cloud"


def local_llm(prompt: str) -> str:
    response = ollama.chat(
        model=os.getenv("ZO_LOCAL_LLM", "llama3.2:1b"),
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]


def cloud_llm(prompt: str) -> str:
    client = _get_cloud_client()
    resp = client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"HTTP-Referer": "https://astrofin.io"},
    )
    return resp.choices[0].message.content


def route(prompt: str, session_id: str = None) -> str:
    now = time.time()
    backend = "unknown"
    model = "unknown"

    if session_id and session_id in _session_last_model:
        if now - _session_last_call[session_id] < TTL:
            backend = _session_last_model[session_id]
            _session_last_call[session_id] = now
            if backend == "local":
                response = local_llm(prompt)
                model = os.getenv("ZO_LOCAL_LLM", "llama3.2:1b")
            else:
                response = cloud_llm(prompt)
                model = "openrouter-auto"
            log_request(prompt, backend, model, response)
            return response

    backend = classify_complexity(prompt)
    if session_id:
        _session_last_model[session_id] = backend
        _session_last_call[session_id] = now

    if backend == "local":
        response = local_llm(prompt)
        model = os.getenv("ZO_LOCAL_LLM", "llama3.2:1b")
    else:
        response = cloud_llm(prompt)
        model = "openrouter-auto"

    log_request(prompt, backend, model, response)
    return response

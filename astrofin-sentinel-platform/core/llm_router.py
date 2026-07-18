"""
AstroFin Sentinel v5 — Intelligent LLM Router

Routes prompts to local Ollama (free, fast) or OpenRouter cloud
(capable, paid) based on semantic complexity classification.

Architecture:
    classify_complexity(prompt) → "local" | "cloud"
    local_llm(prompt)           → ollama.chat(llama3.2:1b)
    cloud_llm(prompt)           → openrouter auto-model
    route(prompt, session_id)   → cached routing + logging
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


# ── Public API ─────────────────────────────────────────────────────────

def classify_complexity(prompt: str) -> str:
    """Return 'local' for simple prompts, 'cloud' for complex ones."""
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
    """
    Route a prompt to the best backend based on complexity.

    Uses session-aware caching with 5-minute TTL.
    Logs every request to logs/llm_requests.jsonl.
    """
    now = time.time()
    backend = "unknown"
    model = "unknown"

    # Check session cache
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

    # Classify and route
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

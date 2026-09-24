"""Tests for core.jev_client (OpenRouter Decisions API client).

All HTTP tests run against a loopback fake server (no live network). The
client is fail-closed: every failure path raises JevError, never a default
"allow".
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import pathlib
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from core.jev_client import (
    JevClient,
    JevError,
    JevDecisions,
    PINNED_JEV_MODEL,
)
from core.settings import settings

NOUL_Q = {"type": "noul", "instructions": "is this an incident?"}
CHOICE_Q = {
    "type": "choice",
    "instructions": "route the ticket",
    "criteria": {"answer": "answer it", "escalate": "escalate", "billing": "to billing"},
}


# ── Fake loopback server ────────────────────────────────────────────────


class _JevHandler(BaseHTTPRequestHandler):
    cfg: dict = {"status": 200, "body": b"{}", "sleep": 0.0, "location": None}

    def do_POST(self):  # noqa: N802 — http.server API
        sleep = self.cfg.get("sleep", 0.0)
        if sleep:
            time.sleep(sleep)
        try:
            self.send_response(self.cfg.get("status", 200))
            if self.cfg.get("location"):
                self.send_header("Location", self.cfg["location"])
            body = self.cfg.get("body", b"{}")
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):  # noqa: D401 — silence access logs
        pass


@contextlib.contextmanager
def fake_jev_server():
    _JevHandler.cfg = {"status": 200, "body": b"{}", "sleep": 0.0, "location": None}
    server = ThreadingHTTPServer(("127.0.0.1", 0), _JevHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield port, _JevHandler.cfg
    finally:
        server.shutdown()
        thread.join(timeout=2)


def _client(port: int, *, model: str = PINNED_JEV_MODEL, max_retries: int = 0, timeout: float = 0.5, client=None) -> JevClient:
    return JevClient(
        base_url=f"http://127.0.0.1:{port}/api/alpha",
        model=model,
        api_key="test-key",
        timeout=timeout,
        max_retries=max_retries,
        client=client,
    )


async def _decide(port: int, state=None, questions=None, *, timeout: float | None = None) -> JevDecisions:
    async with httpx.AsyncClient() as c:
        client = _client(port, client=c)
        return await client.decide(
            state if state is not None else {"ticket_id": "hash-1", "plan": "pro"},
            questions if questions is not None else {"ok": NOUL_Q},
            timeout=timeout,
        )


# ── Fail-closed validation (no network) ─────────────────────────────────


def test_model_pin_rejects_latest():
    with pytest.raises(JevError) as ei:
        _client(1, model="typesafe/jev-latest")
    assert ei.value.reason == "model_pin"


def test_model_pin_accepts_pinned():
    c = _client(1, model="typesafe/jev-1.13")
    assert c.model == PINNED_JEV_MODEL


def test_foreign_host_rejected():
    with pytest.raises(JevError) as ei:
        JevClient(base_url="https://evil.example/api/alpha", model=PINNED_JEV_MODEL, api_key="k")
    assert ei.value.reason == "host_deny"


def test_missing_key_rejected():
    with pytest.raises(JevError) as ei:
        JevClient(base_url="http://127.0.0.1:1/api/alpha", model=PINNED_JEV_MODEL, api_key="")
    assert ei.value.reason == "no_key"


def test_budget_overflow_rejected():
    with fake_jev_server() as (port, _cfg):
        huge = "x" * (33_000 * 4)  # ~33K tokens → over the 32K budget
        with pytest.raises(JevError) as ei:
            asyncio.run(_decide(port, state=huge))
        assert ei.value.reason == "budget_overflow"


# ── HTTP paths (fake server) ────────────────────────────────────────────


def test_valid_response_parsed():
    body = {
        "model": "typesafe/jev-1.13-2026-09",
        "answers": {
            "ok": {"noul": 0.85},
            "route": {"choice": "escalate", "probabilities": {"answer": 0.1, "escalate": 0.8, "billing": 0.1}, "confidence": 0.8},
        },
        "usage": {"input_tokens": 120, "output_tokens": 40, "cost": 0.000005},
    }
    with fake_jev_server() as (port, cfg):
        cfg["body"] = json.dumps(body).encode()
        result = asyncio.run(_decide(port, questions={"ok": NOUL_Q, "route": CHOICE_Q}))

    assert result.model == "typesafe/jev-1.13-2026-09"
    assert result.answers["ok"].type == "noul"
    assert result.answers["ok"].value == pytest.approx(0.85)
    assert result.answers["ok"].confidence == pytest.approx(0.85)  # noul: prob == confidence
    assert result.answers["route"].type == "choice"
    assert result.answers["route"].value == "escalate"
    assert result.answers["route"].probabilities == {"answer": 0.1, "escalate": 0.8, "billing": 0.1}
    assert result.answers["route"].confidence == pytest.approx(0.8)
    assert result.usage.input_tokens == 120
    assert result.usage.output_tokens == 40
    assert result.usage.cost == pytest.approx(0.000005)
    assert result.usage.provider == "openrouter"


def test_http_400_raises():
    with fake_jev_server() as (port, cfg):
        cfg["status"] = 400
        cfg["body"] = b'{"error":"bad request"}'
        with pytest.raises(JevError) as ei:
            asyncio.run(_decide(port))
        assert ei.value.status == 400


def test_http_500_raises():
    with fake_jev_server() as (port, cfg):
        cfg["status"] = 500
        cfg["body"] = b'{"error":"boom"}'
        with pytest.raises(JevError):
            asyncio.run(_decide(port))


def test_timeout_raises():
    with fake_jev_server() as (port, cfg):
        cfg["sleep"] = 0.5
        with pytest.raises(JevError) as ei:
            asyncio.run(_decide(port, timeout=0.1))
        assert ei.value.reason == "timeout"


def test_redirect_rejected():
    with fake_jev_server() as (port, cfg):
        cfg["status"] = 302
        cfg["location"] = "https://evil.example/decisions"
        with pytest.raises(JevError) as ei:
            asyncio.run(_decide(port))
        assert ei.value.reason == "redirect"


def test_invalid_schema_raises():
    with fake_jev_server() as (port, cfg):
        cfg["body"] = b'{"model":"typesafe/jev-1.13","answers":[]}'
        with pytest.raises(JevError) as ei:
            asyncio.run(_decide(port))
        assert ei.value.reason == "invalid_schema"


# ── Canon parity + pin hygiene ──────────────────────────────────────────


def test_thresholds_parity_with_canon():
    canon = json.loads(pathlib.Path("docs/decisions/jev-agent-canon.json").read_text())
    assert settings.jev_thresholds == canon


def test_model_default_is_pinned():
    assert settings.jev_model == PINNED_JEV_MODEL == "typesafe/jev-1.13"


def test_no_jev_latest_as_model_value_in_source():
    src = pathlib.Path("core/jev_client.py").read_text()
    # "typesafe/jev-latest" may appear in docstrings/comments, but never as an
    # assigned model value.
    assert '= "typesafe/jev-latest"' not in src
    assert "= 'typesafe/jev-latest'" not in src
    assert '"typesafe/jev-1.13"' in src  # the pin is present

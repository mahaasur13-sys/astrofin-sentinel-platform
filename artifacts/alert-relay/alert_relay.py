#!/usr/bin/env python3
"""P1-T5 alert relay: Grafana webhook -> Telegram Bot API.

Зачем отдельный релей, а не нативный contact point Grafana:
  Grafana не подставляет $__env{VAR} в поле bottoken (проверено: 401 Unauthorized,
  в лог уходил литерал "$__env{IDIA_BOT_TOKEN}"), а хранить токен plaintext в grafana.db
  противоречит R-10 (секреты — только в .env). Релей читает токен из env/.env и держит
  Grafana БД чистой.

Env:
  IDIA_BOT_TOKEN / TELEGRAM_BOT_TOKEN — токен бота (env или /home/workspace/.env)
  TELEGRAM_CHAT_ID — chat id получателя (тот же fallback)
  RELAY_PORT      — порт (default 8099), слушает только 127.0.0.1
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ENV_FILE = Path("/home/workspace/.env")
LOG_PATH = Path("/dev/shm/alert-relay.log")


def log(event: str, **kw) -> None:
    import datetime

    rec = {
        "ts": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event,
    }
    rec.update(kw)
    line = json.dumps(rec, ensure_ascii=False)
    print(line, flush=True)
    try:
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def read_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if val:
        return val
    try:
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if raw.startswith(name + "="):
                return raw.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception as exc:  # noqa: BLE001
        log("env_read_error", error=type(exc).__name__)
    return ""


def send_telegram(token: str, chat_id: str, text: str) -> tuple[bool, str]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text[:3800], "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            _body = resp.read().decode("utf-8", "replace")
            return resp.status == 200, f"http={resp.status}"
    except Exception as exc:  # noqa: BLE001
        detail = ""
        if hasattr(exc, "read"):
            try:
                detail = exc.read().decode("utf-8", "replace")[:200]
            except Exception:
                detail = ""
        return False, f"{type(exc).__name__}: {detail or exc}"


def format_payload(payload: dict) -> str:
    # Alertmanager v4 posts an object; Grafana's legacy webhook posts a bare list.
    if isinstance(payload, list):
        payload = {"alerts": payload}
    if not isinstance(payload, dict):
        payload = {}
    common = payload.get("commonLabels") or {}
    title = payload.get("title") or common.get("alertname") or "Grafana alert"
    status = payload.get("status") or "?"
    lines = [f"[{status.upper()}] {title}"]
    for alert in (payload.get("alerts") or [])[:5]:
        st = alert.get("status", "?")
        labels = alert.get("labels") or {}
        ann = alert.get("annotations") or {}
        name = labels.get("alertname", "alert")
        summary = ann.get("summary") or ann.get("description") or ""
        lines.append(f"- {st}: {name} | {summary[:220]}")
    if payload.get("externalURL"):
        lines.append(payload["externalURL"])
    return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    server_version = "alert-relay/1.0"

    def _reply(self, code: int, body: str = "") -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self) -> None:
        if self.path.startswith("/health"):
            self._reply(200, "ok")
        else:
            self._reply(404, "not found")

    def do_POST(self) -> None:
        if not self.path.startswith("/notify"):
            self._reply(404, "not found")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            payload = json.loads(raw.decode("utf-8", "replace") or "{}")
        except Exception as exc:  # noqa: BLE001
            log("relay_bad_request", error=type(exc).__name__)
            self._reply(400, "bad request")
            return

        token = read_env("IDIA_BOT_TOKEN") or read_env("TELEGRAM_BOT_TOKEN")
        chat_id = read_env("TELEGRAM_CHAT_ID") or read_env("TELEGRAM_CHAT")
        if not token or not chat_id:
            log(
                "relay_missing_secret",
                bot_token_present=bool(token),
                chat_present=bool(chat_id),
            )
            self._reply(500, "missing secret")
            return

        ok, info = send_telegram(token, chat_id, format_payload(payload))
        log(
            "relay_delivery",
            ok=ok,
            detail=info,
            chat_len=len(chat_id),
            token_len=len(token),
        )
        self._reply(200 if ok else 502, "sent" if ok else "telegram error")

    def log_message(self, fmt: str, *args) -> None:  # silence default stderr spam
        return


def main() -> int:
    port = int(os.environ.get("RELAY_PORT", "8099"))
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    log("relay_start", pid=os.getpid(), port=port, env_file_exists=ENV_FILE.exists())
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

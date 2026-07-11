#!/usr/bin/env python3
"""Healthcheck для AstroFinSentinelV5 — проверка окружения и сервисов."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def check_venv() -> dict:
    """Проверка виртуального окружения."""
    in_venv = sys.prefix != sys.base_prefix
    return {
        "active": in_venv,
        "path": sys.prefix,
        "python": sys.executable,
    }


def check_postgresql() -> dict:
    """Проверка доступности PostgreSQL (попытка docker-compose при отсутствии)."""
    try:
        result = subprocess.run(
            ["pg_isready", "-h", "localhost", "-p", "5432"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        accepting = result.returncode == 0
    except FileNotFoundError:
        # pg_isready не установлен — пытаемся через docker
        try:
            subprocess.run(
                ["docker-compose", "up", "-d", "postgres"],
                cwd=ROOT,
                capture_output=True,
                timeout=30,
            )
            # после запуска проверяем снова
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            accepting = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            accepting = False
    except subprocess.TimeoutExpired:
        accepting = False

    return {
        "available": accepting,
        "host": "localhost",
        "port": 5432,
    }


def check_ollama() -> dict:
    """Проверка доступности Ollama API."""
    import urllib.request

    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
        return {"available": True, "models": models}
    except Exception:  # noqa: BLE001
        return {"available": False, "models": []}


def run_all_checks() -> dict:
    return {
        "status": "ok",
        "checks": {
            "venv": check_venv(),
            "postgresql": check_postgresql(),
            "ollama": check_ollama(),
        },
    }


def main():
    results = run_all_checks()
    # exit code 1 если есть хотя бы одна проблема (но не критическая)
    has_issues = (
        not results["checks"]["venv"]["active"]
        or not results["checks"]["postgresql"]["available"]
        or not results["checks"]["ollama"]["available"]
    )
    json.dump(results, sys.stdout, indent=2)
    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()

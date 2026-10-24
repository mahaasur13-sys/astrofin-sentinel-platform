#!/usr/bin/env python3
"""pg-watchdog: каждое событие уходит и в stdout, и в файл журнала.

Инвариант нужен для доставки в Loki: supervisord перенаправляет stdout программы
в /dev/shm/pg-watchdog.log, откуда его забирает Promtail ({job="zo_services"}).
Файл /var/lib/pg-watchdog/watchdog.log — durable-копия (R3). Пропажа любой из двух
половин означает либо слепой мониторинг, либо потерю истории после рестарта.

Логика проверок сторожа не затрагивается: тест вызывает только emit().
"""

import importlib.util
import json
from pathlib import Path

WATCHDOG = Path(__file__).resolve().parents[1] / "artifacts" / "pg-watchdog" / "pg_watchdog.py"

_spec = importlib.util.spec_from_file_location("pg_watchdog", WATCHDOG)
watchdog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(watchdog)


def _redirect(monkeypatch, tmp_path, log_name="watchdog.log"):
    state_dir = tmp_path / "state"
    monkeypatch.setattr(watchdog, "STATE_DIR", str(state_dir))
    monkeypatch.setattr(watchdog, "LOG_PATH", str(state_dir / log_name))
    return state_dir


def test_event_goes_to_stdout_and_file(monkeypatch, tmp_path, capsys):
    state_dir = _redirect(monkeypatch, tmp_path)

    watchdog.emit(event="pg_recovered", attempt=1)

    stdout_lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert len(stdout_lines) == 1
    emitted = json.loads(stdout_lines[0])
    assert emitted["event"] == "pg_recovered"
    assert emitted["attempt"] == 1
    assert emitted["ts"].endswith("Z")

    file_lines = (state_dir / "watchdog.log").read_text(encoding="utf-8").splitlines()
    assert file_lines == stdout_lines


def test_file_write_failure_still_reaches_stdout(monkeypatch, tmp_path, capsys):
    state_dir = _redirect(monkeypatch, tmp_path)
    monkeypatch.setattr(watchdog, "LOG_PATH", str(state_dir / "missing" / "watchdog.log"))

    watchdog.emit(event="pg_down")

    stdout_lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    events = [json.loads(ln)["event"] for ln in stdout_lines]
    assert events == ["pg_down", "log_write_failed"]

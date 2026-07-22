#!/usr/bin/env python3
"""
Failure Orchestrator — Main Loop
Runs detectors, applies recovery based on rules, logs + escalates.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s ORCH %(levelname)s %(message)s",
)
log = logging.getLogger("orchestrator")

STATE_FILE = "/var/run/orchestrator_state.json"
ESCALATION_FILE = "/var/run/orchestrator_escalation.json"


def load_state() -> dict:
    if Path(STATE_FILE).exists():
        try:
            return json.loads(Path(STATE_FILE).read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict):
    Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(STATE_FILE).write_text(json.dumps(state, indent=2))


def load_escalation() -> dict:
    if Path(ESCALATION_FILE).exists():
        try:
            return json.loads(Path(ESCALATION_FILE).read_text())
        except Exception:
            pass
    return {}


def save_escalation(state: dict):
    Path(ESCALATION_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(ESCALATION_FILE).write_text(json.dumps(state, indent=2))


class RecoveryEngine:
    MAX_RETRIES = 3
    BACKOFF_BASE = 5

    def __init__(self):
        self.attempt_counts: dict = {}
        self.last_recovery_time: dict = {}

    def should_retry(self, detector_name: str) -> bool:
        count = self.attempt_counts.get(detector_name, 0)
        return count < self.MAX_RETRIES

    def record_attempt(self, detector_name: str):
        self.attempt_counts[detector_name] = self.attempt_counts.get(detector_name, 0) + 1
        self.last_recovery_time[detector_name] = time.time()

    def reset(self, detector_name: str):
        self.attempt_counts[detector_name] = 0


engine = RecoveryEngine()

RECOVERY_MAP = {
    "slurm_controller": "restart_slurm_controller",
    "slurm_worker_rk3576": "restart_slurm_worker",
    "ceph_health": "restart_ceph",
    "ceph_osd_down": "restart_ceph_osd",
    "ray_head": "restart_ray_head",
    "ray_worker_rk3576": "restart_ray_worker",
    "wireguard_wg0": "restart_wireguard",
    "gpu": "restart_nvidia_driver",
}


def escalate(message: str, severity: str):
    escalation_state = load_escalation()
    last_escalation = escalation_state.get("last_ts", 0)
    cooldown = 3600

    if time.time() - last_escalation < cooldown:
        return

    escalation_state["last_ts"] = time.time()
    save_escalation(escalation_state)

    log.error(f"ESCALATION [{severity.upper()}]: {message}")

    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if telegram_bot_token and telegram_chat_id:
        try:
            import requests
            requests.post(
                f"https://api.telegram.org/{telegram_bot_token}/sendMessage",
                json={"chat_id": telegram_chat_id, "text": f"[{severity.upper()}] {message}"},
                timeout=10,
            )
        except Exception as e:
            log.error(f"Telegram escalation failed: {e}")

    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if slack_webhook:
        try:
            import requests
            requests.post(slack_webhook, json={"text": f"[{severity.upper()}] {message}"}, timeout=10)
        except Exception as e:
            log.error(f"Slack escalation failed: {e}")


def run_cycle():
    from .detectors import all_detectors
    from . import recovery as rec_module

    state = load_state()
    results = all_detectors()

    for name, (is_down, reason, severity) in results.items():
        if is_down:
            recovery_fn_name = RECOVERY_MAP.get(name)
            if not recovery_fn_name:
                log.warning(f"No recovery mapped for: {name} ({reason})")
                continue

            recovery_fn = getattr(rec_module, recovery_fn_name, None)
            if not recovery_fn:
                log.error(f"Recovery function not found: {recovery_fn_name}")
                continue

            if engine.should_retry(name):
                engine.record_attempt(name)
                attempt = engine.attempt_counts[name]
                backoff = engine.BACKOFF_BASE ** attempt

                log.warning(f"Failure detected [{name}]: {reason} → attempt {attempt}/{engine.MAX_RETRIES} (backoff={backoff}s)")

                time.sleep(backoff)
                ok, msg = recovery_fn()

                if ok:
                    log.info(f"Recovery SUCCESS [{name}]: {msg}")
                    engine.reset(name)
                    state[f"{name}_status"] = "recovered"
                else:
                    log.error(f"Recovery FAILED [{name}]: {msg}")
                    state[f"{name}_status"] = "failed"
                    if engine.attempt_counts[name] >= engine.MAX_RETRIES:
                        escalate(f"{name} failed after {engine.MAX_RETRIES} attempts: {msg}", severity)
                        engine.reset(name)
            else:
                engine.reset(name)

        else:
            if state.get(f"{name}_status") == "recovered":
                log.info(f"Previously failed detector now OK: {name}")
            state[f"{name}_status"] = "ok"
            engine.reset(name)

    save_state(state)


def main(interval: int = 30):
    log.info(f"Failure orchestrator started (interval={interval}s)")
    while True:
        try:
            run_cycle()
        except Exception as e:
            log.error(f"Cycle error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    main(interval)

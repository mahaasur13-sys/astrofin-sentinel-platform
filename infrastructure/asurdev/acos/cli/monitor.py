#!/usr/bin/env python3
"""
ACOS Monitor CLI — unified monitoring interface switcher.
Usage: acos monitor [status|switch|list|logs|alerts]
"""
from __future__ import annotations
import os, sys, json, subprocess, time, socket
from pathlib import Path

CONFIG_DIR = Path(os.getenv("ACOS_CONFIG_DIR", "/etc/acos"))
CONFIG_FILE = CONFIG_DIR / "monitoring.json"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

BACKENDS = {
    "grafana":  {"port": 3000, "url": "http://localhost:3000", "label": "Grafana Web UI"},
    "beszel":   {"port": 8090, "url": "http://localhost:8090", "label": "Beszel Web UI"},
    "perses":   {"port": 8080, "url": "http://localhost:8080", "label": "Perses Web UI"},
    "grafatui": {"port": None, "url": "terminal", "label": "Grafatui Terminal"},
}
DEFAULT_BACKEND = "grafana"

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"active_backend": DEFAULT_BACKEND, "victoria_url": "http://localhost:8428"}

def save_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.error, OSError):
        return False

def get_tunnel_status() -> dict:
    try:
        result = subprocess.run(["ip", "addr", "show", "wg0"],
            capture_output=True, text=True, timeout=5)
        up = result.returncode == 0 and "inet " in result.stdout
        return {"interface": "wg0", "up": up}
    except Exception:
        return {"interface": "wg0", "up": False}

def cmd_status() -> int:
    cfg = load_config()
    active = cfg.get("active_backend", DEFAULT_BACKEND)
    victoria_url = cfg.get("victoria_url", "http://localhost:8428")
    print("═══════════════════════════════════════")
    print("  ACOS Cluster Status")
    print("═══════════════════════════════════════")
    tunnel = get_tunnel_status()
    print(f"  {'✅' if tunnel['up'] else '❌'} AmneziaWG Tunnel (wg0): {'UP' if tunnel['up'] else 'DOWN'}")
    # VictoriaMetrics
    try:
        import urllib.request
        req = urllib.request.urlopen(f"{victoria_url}/health", timeout=3)
        vm_up = req.status == 200
    except Exception:
        vm_up = False
    print(f"  {'✅' if vm_up else '❌'} VictoriaMetrics: {victoria_url} [{'up' if vm_up else 'DOWN'}]")
    # Backends
    print()
    print("  Monitoring Backends:")
    for name, info in BACKENDS.items():
        marker = "◀ ACTIVE" if name == active else "  "
        if info["port"] is None:
            icon, status = "⚠️ ", "terminal"
        else:
            up = check_port("localhost", info["port"])
            icon = "✅" if up else "❌"
            status = "up" if up else "DOWN"
        print(f"    {marker} {icon} {name:12} {info['label']:20} [{status}]")
    print()
    return 0

def cmd_switch(backend: str) -> int:
    if backend not in BACKENDS:
        print(f"ERROR: Unknown backend '{backend}'. Available: {', '.join(BACKENDS.keys())}")
        return 1
    cfg = load_config()
    old = cfg.get("active_backend", DEFAULT_BACKEND)
    cfg["active_backend"] = backend
    save_config(cfg)
    print(f"Switched: {old} → {backend}  [{BACKENDS[backend]['label']}]")
    # Log event
    try:
        sys.path.insert(0, "/opt/acos")
        from acos.events.event_log import EventLog
        from acos.events.types import EventType
        log = EventLog()
        log.emit("acos-monitor", EventType.DAG_CREATED,
            {"action": "MONITOR_SWITCH", "from": old, "to": backend})
        print("  ✅ Event logged to EventLog")
    except Exception:
        print("  ⚠️  EventLog unavailable")
    return 0

HELP = """ACOS Monitor CLI

Usage: acos monitor <command>

Commands:
  status              Show cluster health + all backends
  switch <backend>    Switch active backend (grafana|beszel|perses|grafatui)
  list                List all backends

Examples:
  acos monitor status
  acos monitor switch beszel
  acos monitor list
"""

def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "--help"):
        print(HELP); return 0
    cmd = sys.argv[1]
    if cmd == "status": return cmd_status()
    elif cmd == "switch":
        if len(sys.argv) < 3: print("Usage: acos monitor switch <backend>"); return 1
        return cmd_switch(sys.argv[2])
    elif cmd == "list":
        cfg = load_config()
        active = cfg.get("active_backend", DEFAULT_BACKEND)
        for name, info in BACKENDS.items():
            print(f"  {'◀ ' if name == active else '  '}{name:12} {info['label']}")
        return 0
    else:
        print(f"Unknown: {cmd}"); print(HELP); return 1

if __name__ == "__main__":
    sys.exit(main())

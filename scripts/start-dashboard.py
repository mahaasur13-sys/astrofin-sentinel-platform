#!/usr/bin/env python3
"""Start dashboard services (freeze-compliant — no code changes).

Usage:
    python scripts/start-dashboard.py [--host HOST] [--port PORT]

Environment:
    WEB_PORT    Dashboard port (default: 8050)
    API_PORT    FastAPI port (default: 8000)
    AUTH_MODE   api_key | none (default: api_key)
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _env(key, default):
    return os.environ.get(key, default)


def check_port(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    parser = argparse.ArgumentParser(description="Start AstroFin Sentinel dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--api-port", type=int, default=int(_env("API_PORT", "8000")))
    parser.add_argument("--web-port", type=int, default=int(_env("WEB_PORT", "8050")))
    args = parser.parse_args()

    print("=" * 60)
    print("  AstroFin Sentinel Dashboard Launcher")
    print("  Version: v1.0.0-rc")
    print(f"  Host: {args.host}")
    print("=" * 60)

    # Check for existing processes
    for port, name in [(args.api_port, "FastAPI"), (args.web_port, "Dash")]:
        if check_port(port):
            print(f"[!] {name} already running on {args.host}:{port}")
            print(f"    Kill with: kill $(lsof -t -i:{port})")
            sys.exit(1)

    # Start FastAPI
    print(f"\n[1/2] Starting FastAPI on {args.host}:{args.api_port}...")
    api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app",
         "--host", args.host, "--port", str(args.api_port),
         "--log-level", "info"],
        cwd=str(ROOT),
    )
    time.sleep(2)

    # Start Dash
    web_port = args.web_port
    print(f"[2/2] Starting Dashboard on {args.host}:{web_port}...")
    dash_proc = subprocess.Popen(
        [sys.executable, "-m", "web.app"],
        cwd=str(ROOT),
        env={**os.environ, "DASH_HOST": args.host, "WEB_PORT": str(web_port)},
    )
    time.sleep(2)

    print("\n" + "=" * 60)
    print("  Dashboard Ready")
    print(f"  FastAPI:   http://{args.host}:{args.api_port}/docs")
    print(f"  Health:    http://{args.host}:{args.api_port}/health")
    print(f"  Dashboard: http://{args.host}:{web_port}")
    print("=" * 60)
    print("\nPress Ctrl+C to stop all services.")

    try:
        api_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        api_proc.terminate()
        dash_proc.terminate()
        api_proc.wait()
        dash_proc.wait()
        print("Stopped.")


if __name__ == "__main__":
    main()

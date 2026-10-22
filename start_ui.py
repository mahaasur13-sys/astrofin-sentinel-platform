#!/usr/bin/env python3
"""Launcher for sentinel-ui-v2 — wraps web/app.py."""
import sys
import os

# Ensure workspace root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4200))
    app.run(host="0.0.0.0", port=port, debug=False)

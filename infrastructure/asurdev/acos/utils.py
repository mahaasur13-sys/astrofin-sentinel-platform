#!/usr/bin/env python3
"""ACOS shared utilities - SINGLETON for cross-module helpers."""
from __future__ import annotations
from typing import Any

def payload_to_dict(p: Any) -> dict:
    """Convert Event.payload to dict. Handles tuple (frozen dataclass) and dict."""
    if isinstance(p, dict): return p
    if isinstance(p, tuple): return dict(p)
    return {}

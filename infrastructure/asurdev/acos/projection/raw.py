#!/usr/bin/env python3
"""
ACOS SCL v6 — RawEventProjection (READ-SIDE, read-only).
Returns raw event list. No state reconstruction.
"""
from __future__ import annotations

class RawEventProjection:
    """Read raw events. Read-side ONLY."""
    
    def __init__(self, log):
        self._log = log
    
    def get_trace_events(self, trace_id: str) -> list:
        return self._log.get_trace(trace_id)
    
    def get_all_events(self) -> list:
        return self._log.get_all()

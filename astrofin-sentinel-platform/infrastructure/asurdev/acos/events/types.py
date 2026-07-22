"""ACOS Event Types — re-exported from acos-contracts (S2 migration).

Local definition moved to ``acos_contracts.events.EventType``. This module
remains as a thin re-export so existing call sites
(``from acos.events.types import EventType``) keep working unchanged.
"""
from __future__ import annotations

from acos_contracts.events import EventType

__all__ = ["EventType"]

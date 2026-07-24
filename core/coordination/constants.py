"""core/coordination/constants.py — ATOM-COORD-001: Feature Flags"""

from __future__ import annotations

import os

# Feature flag: полное отключение
PRESSURE_FIELD_ENABLED = os.getenv("PRESSURE_FIELD_ENABLED", "false").lower() == "true"

# Параметры pressure field
PRESSURE_FIELD_K_NEIGHBORS = int(os.getenv("PRESSURE_FIELD_K_NEIGHBORS", "3"))
PRESSURE_FIELD_INFLUENCE_STRENGTH = float(
    os.getenv("PRESSURE_FIELD_INFLUENCE_STRENGTH", "0.15")
)
PRESSURE_FIELD_MIN_CONSENSUS = float(os.getenv("PRESSURE_FIELD_MIN_CONSENSUS", "0.5"))

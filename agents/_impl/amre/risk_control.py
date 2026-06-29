"""amre/risk_control.py — ATOM-KARL-015 Phase 5: Risk Controller via position_lag

Динамически корректирует размер позиции на основе метрики position_lag:
  - position_lag < -threshold  → позиция УМЕНЬШАЕТСЯ (перегрев / отставание вверх)
  - position_lag > +threshold  → позиция УВЕЛИЧИВАЕТСЯ (недоторговля)
  - иначе → без изменений

Все параметры управляются через env.
"""

from __future__ import annotations


import logging
import os

logger = logging.getLogger(__name__)

# ─── Config from env ─────────────────────────────────────────────────────────────

RISK_USE_POSITION_LAG = os.getenv("RISK_USE_POSITION_LAG", "true").lower() == "true"
RISK_POSITION_LAG_THRESHOLD = float(os.getenv("RISK_POSITION_LAG_THRESHOLD", "0.3"))
RISK_REDUCTION_FACTOR = float(os.getenv("RISK_REDUCTION_FACTOR", "0.8"))
RISK_INCREASE_FACTOR = float(os.getenv("RISK_INCREASE_FACTOR", "1.1"))
RISK_MIN_POSITION = float(os.getenv("RISK_MIN_POSITION", "0.01"))
RISK_MAX_POSITION = float(os.getenv("RISK_MAX_POSITION", "0.20"))


def apply_position_lag_risk(current_position_pct: float, position_lag: float) -> float:
    """
    Adjust position size based on position_lag metric.

    Parameters
    ----------
    current_position_pct : float
        Текущий размер позиции (0.0–1.0+).
    position_lag : float
        Метрика отклонения позиции от скользящей средней.
        > 0  — текущая позиция меньше средней (недоторговка, можно наращивать)
        < 0  — текущая позиция больше средней (перегрев, нужно сокращать)

    Returns
    -------
    float
        Скорректированный размер позиции, приведённый к [RISK_MIN_POSITION, RISK_MAX_POSITION].

    Notes
    -----
    Threshold логики:
      if position_lag < -RISK_POSITION_LAG_THRESHOLD  →  reduce (перегрев)
      if position_lag > +RISK_POSITION_LAG_THRESHOLD  →  increase (недоторговка)
    """
    if not RISK_USE_POSITION_LAG:
        return current_position_pct

    new_pos = current_position_pct

    if position_lag < -RISK_POSITION_LAG_THRESHOLD:
        # Перегрев: позиция слишком велика относительно средней → сокращаем
        new_pos = current_position_pct * RISK_REDUCTION_FACTOR
        logger.debug(
            f"[RiskControl] position_lag={position_lag:+.3f} < {-RISK_POSITION_LAG_THRESHOLD} "
            f"→ REDUCE ×{RISK_REDUCTION_FACTOR}: "
            f"{current_position_pct:.4f} → {new_pos:.4f}"
        )
    elif position_lag > RISK_POSITION_LAG_THRESHOLD:
        # Недоторговка: позиция слишком мала → наращиваем
        new_pos = current_position_pct * RISK_INCREASE_FACTOR
        logger.debug(
            f"[RiskControl] position_lag={position_lag:+.3f} > {+RISK_POSITION_LAG_THRESHOLD} "
            f"→ INCREASE ×{RISK_INCREASE_FACTOR}: "
            f"{current_position_pct:.4f} → {new_pos:.4f}"
        )
    else:
        # Внутри порога — без изменений
        return current_position_pct

    # Clip к допустимому диапазону
    clipped = max(RISK_MIN_POSITION, min(RISK_MAX_POSITION, new_pos))
    if clipped != new_pos:
        logger.debug(
            f"[RiskControl] clipped to [{RISK_MIN_POSITION}, {RISK_MAX_POSITION}]: {new_pos:.4f} → {clipped:.4f}"
        )
    return clipped


# ─── Exported constants for testing ─────────────────────────────────────────────

__all__ = [
    "apply_position_lag_risk",
    "RISK_USE_POSITION_LAG",
    "RISK_POSITION_LAG_THRESHOLD",
    "RISK_REDUCTION_FACTOR",
    "RISK_INCREASE_FACTOR",
    "RISK_MIN_POSITION",
    "RISK_MAX_POSITION",
]

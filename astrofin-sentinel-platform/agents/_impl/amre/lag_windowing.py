"""amre/lag_windowing.py — ATOM-KARL-015 Phase 5: Adaptive Lag Windowing

Сглаживание сигналов агента через EMA с адаптивным размером окна.

Функции:
- EMA smoothing (α = 2/(W+1)) для снижения шума в confidence
- Adaptive window: меньше окно при высокой волатильности (быстрая реакция),
  больше окно при низкой (сильное сглаживание)
- Warmup phase: повышенный blend (0.3) для первых 20 решений
- Lag adjustment: метрика отставания/опережения EMA относительно raw signal

Использование:
    from agents._impl.amre.lag_windowing import LagWindow

    lw = LagWindow()
    result = lw.add(confidence=85, position_pct=0.15, volatility=0.008)
    # result = {final_confidence: int, ema: float, lag_adj: float, ...}
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


# ─── Config from env ─────────────────────────────────────────────────────────────


def _env_bool(key: str, default: str = "true") -> bool:
    return os.getenv(key, default).lower() == "true"


def _env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    try:
        return int(val) if val else default
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    val = os.getenv(key)
    try:
        return float(val) if val else default
    except ValueError:
        return default


# ─── Constants ───────────────────────────────────────────────────────────────────

DEFAULT_BASE_WINDOW = 50
DEFAULT_MIN_WINDOW = 20
DEFAULT_MAX_WINDOW = 100
DEFAULT_VOL_LOW = 0.005  # 0.5% внутридневной волатильности
DEFAULT_VOL_HIGH = 0.02  # 2%
WARMUP_THRESHOLD = 20  # первые 20 решений — warmup phase
BLEND_WARMUP = 0.30  # 30% weight на EMA в warmup
BLEND_MATURE = 0.15  # 15% weight на EMA в mature


# ─── LagWindow ───────────────────────────────────────────────────────────────────


class LagWindow:
    """
    EMA-based signal smoother with adaptive window size.

    Parameters
    ----------
    adaptive_window_enabled : bool
        Включить адаптивное изменение окна по волатильности.
        Управляется через env LAG_ADAPTIVE_WINDOW (default: true).
    base_window_size : int
        Базовый размер окна. Управляется через env LAG_BASE_WINDOW_SIZE (default: 50).
    min_window_size : int
        Минимальный размер окна. Управляется через env LAG_MIN_WINDOW_SIZE (default: 20).
    max_window_size : int
        Максимальный размер окна. Управляется через env LAG_MAX_WINDOW_SIZE (default: 100).
    volatility_low_threshold : float
        Нижний порог волатильности. Ниже этого — увеличиваем окно.
        Управляется через env LAG_VOL_LOW_THRESH (default: 0.005).
    volatility_high_threshold : float
        Верхний порог волатильности. Выше этого — уменьшаем окно.
        Управляется через env LAG_VOL_HIGH_THRESH (default: 0.02).
    """

    def __init__(
        self,
        adaptive_window_enabled: bool | None = None,
        base_window_size: int | None = None,
        min_window_size: int | None = None,
        max_window_size: int | None = None,
        volatility_low_threshold: float | None = None,
        volatility_high_threshold: float | None = None,
    ):
        # Env-driven defaults with constructor overrides
        self.adaptive_enabled = (
            adaptive_window_enabled
            if adaptive_window_enabled is not None
            else _env_bool("LAG_ADAPTIVE_WINDOW", "true")
        )
        self.base_window_size = (
            base_window_size
            if base_window_size is not None
            else _env_int("LAG_BASE_WINDOW_SIZE", DEFAULT_BASE_WINDOW)
        )
        self.min_window_size = (
            min_window_size
            if min_window_size is not None
            else _env_int("LAG_MIN_WINDOW_SIZE", DEFAULT_MIN_WINDOW)
        )
        self.max_window_size = (
            max_window_size
            if max_window_size is not None
            else _env_int("LAG_MAX_WINDOW_SIZE", DEFAULT_MAX_WINDOW)
        )
        self.vol_low = (
            volatility_low_threshold
            if volatility_low_threshold is not None
            else _env_float("LAG_VOL_LOW_THRESH", DEFAULT_VOL_LOW)
        )
        self.vol_high = (
            volatility_high_threshold
            if volatility_high_threshold is not None
            else _env_float("LAG_VOL_HIGH_THRESH", DEFAULT_VOL_HIGH)
        )

        # Internal state
        self.window_size = self.base_window_size
        self.alpha: float = 2.0 / (self.window_size + 1)
        self._ema: float | None = None
        self._count: int = 0
        self._position_history: list[float] = []

        logger.debug(
            f"[LagWindow] init: adaptive={self.adaptive_enabled} window={self.window_size} alpha={self.alpha:.4f} vol_thresh=[{self.vol_low}, {self.vol_high}]"
        )

    # ─── Alpha recalculation ──────────────────────────────────────────────────

    def _update_alpha(self):
        """Пересчитать alpha при изменении window_size."""
        self.alpha = 2.0 / (self.window_size + 1)

    # ─── Adaptive window sizing ───────────────────────────────────────────────

    def _update_window_size(self, volatility: float):
        """
        Адаптивно изменить window_size на основе волатильности.

        Rules:
        - volatility <= vol_low  → увеличить окно (base * 1.5, capped at max)
        - volatility >= vol_high → уменьшить окно (base // 2, floored at min)
        - иначе → base_window_size
        """
        old_size = self.window_size

        if volatility <= self.vol_low:
            new_size = min(self.max_window_size, int(self.base_window_size * 1.5))
        elif volatility >= self.vol_high:
            new_size = max(self.min_window_size, int(self.base_window_size // 2))
        else:
            new_size = self.base_window_size

        if new_size != old_size:
            old_alpha = self.alpha
            self.window_size = new_size
            self._update_alpha()

            logger.info(
                f"[LagWindow] adaptive window changed: {old_size} → {new_size} (alpha {old_alpha:.4f} → {self.alpha:.4f}, vol={volatility:.4f})"
            )

    # ─── Main entry point ────────────────────────────────────────────────────

    def add(
        self,
        confidence: int,
        position_pct: float = 0.0,
        volatility: float | None = None,
    ) -> dict[str, Any]:
        """
        Обработать новое значение confidence через EMA smoothing.

        Parameters
        ----------
        confidence : int
            Текущее значение confidence (0–100).
        position_pct : float
            Текущий размер позиции (0.0–1.0+). Используется для position_lag.
        volatility : float, optional
            Текущая волатильность (std dev доходности, ATR, и т.д.).
            Если передана и adaptive_enabled=True → пересчитать window_size.

        Returns
        -------
        dict
            {
                "final_confidence": int,     # сглаженное итоговое confidence
                "raw_confidence": int,       # исходное значение
                "ema": float,                # текущее EMA
                "lag_adj": float,            # lag adjustment (EMA - raw) / raw
                "position_lag": float,       # отклонение позиции от среднего по окну
                "window_size": int,         # текущий размер окна
                "alpha": float,              # текущий alpha
                "blend": float,              # текущий blend (warmup vs mature)
                "count": int,                # номер решения
            }
        """
        x_t = float(confidence)

        # ── Adaptive window update ─────────────────────────────────────────────
        if self.adaptive_enabled and volatility is not None:
            self._update_window_size(volatility)

        # ── EMA update ─────────────────────────────────────────────────────────
        if self._ema is None:
            self._ema = x_t
        else:
            self._ema = self.alpha * x_t + (1 - self.alpha) * self._ema

        # ── Position history ─────────────────────────────────────────────────
        self._position_history.append(position_pct)
        if len(self._position_history) > self.max_window_size:
            self._position_history.pop(0)

        self._count += 1

        # ── Blend: warmup vs mature ───────────────────────────────────────────
        blend = BLEND_WARMUP if self._count < WARMUP_THRESHOLD else BLEND_MATURE

        # ── Lag adjustment ─────────────────────────────────────────────────────
        # Положительное → EMA выше raw (сигнал "отстаёт" вверх)
        # Отрицательное → EMA ниже raw (сигнал "опережает" вверх)
        lag_adj = (self._ema - x_t) / max(x_t, 1.0)

        # ── Position lag ─────────────────────────────────────────────────────
        position_lag = 0.0
        if len(self._position_history) >= 5:
            avg_position = sum(self._position_history) / len(self._position_history)
            position_lag = (avg_position - position_pct) / max(abs(position_pct), 1e-6)

        # ── Final blended confidence ─────────────────────────────────────────
        final_confidence = int(round((1 - blend) * x_t + blend * self._ema))

        result = {
            "final_confidence": final_confidence,
            "raw_confidence": confidence,
            "ema": round(self._ema, 4),
            "lag_adj": round(lag_adj, 4),
            "position_lag": round(position_lag, 4),
            "window_size": self.window_size,
            "alpha": round(self.alpha, 6),
            "blend": blend,
            "count": self._count,
        }

        logger.debug(
            f"[LagWindow] {result['raw_confidence']} → {result['final_confidence']} (ema={result['ema']:.2f}, lag_adj={result['lag_adj']:+.3f})"
        )

        return result

    # ─── Diagnostic getters ───────────────────────────────────────────────────

    def get_state(self) -> dict[str, Any]:
        """Вернуть текущее состояние для диагностики."""
        return {
            "ema": round(self._ema, 4) if self._ema is not None else None,
            "window_size": self.window_size,
            "alpha": round(self.alpha, 6),
            "count": self._count,
            "adaptive_enabled": self.adaptive_enabled,
            "position_history_len": len(self._position_history),
        }

    def reset(self):
        """Сбросить внутреннее состояние EMA и счётчик."""
        self._ema = None
        self._count = 0
        self._position_history.clear()
        self.window_size = self.base_window_size
        self._update_alpha()
        logger.debug("[LagWindow] reset")


# ─── Global singleton ─────────────────────────────────────────────────────────

_LAG_WINDOW: LagWindow | None = None


def get_lag_window() -> LagWindow:
    """Вернуть глобальный экземпляр LagWindow."""
    global _LAG_WINDOW
    if _LAG_WINDOW is None:
        _LAG_WINDOW = LagWindow()
    return _LAG_WINDOW


def reset_lag_window():
    """Сбросить глобальный экземпляр. Используется в тестах."""
    global _LAG_WINDOW
    if _LAG_WINDOW is not None:
        _LAG_WINDOW.reset()


# ─── Module-level exports ────────────────────────────────────────────────────────
__all__ = [
    "LagWindow",
    "get_lag_window",
    "reset_lag_window",
    # Constants for external use (e.g. karl_synthesis.py)
    "DEFAULT_BASE_WINDOW",
    "DEFAULT_MIN_WINDOW",
    "DEFAULT_MAX_WINDOW",
    "WARMUP_THRESHOLD",
    "BLEND_WARMUP",
    "BLEND_MATURE",
]

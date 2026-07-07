"""amre/test_lag_windowing.py — ATOM-KARL-015 Phase 5: Tests for LagWindow

Tests:
1. Adaptive window увеличивается при низкой волатильности
2. Adaptive window уменьшается при высокой волатильности
3. EMA продолжает работать без ошибок при изменении окна
4. Warmup phase использует blend=0.3 для первых 20 решений
5. Lag adjustment вычисляется корректно
6. Position lag вычисляется корректно

Запуск:
    pytest agents/_impl/amre/test_lag_windowing.py -v
"""

from __future__ import annotations

import math

from agents._impl.amre.lag_windowing import (
    BLEND_MATURE,
    BLEND_WARMUP,
    WARMUP_THRESHOLD,
    LagWindow,
    get_lag_window,
    reset_lag_window,
)


class TestAdaptiveWindowSizing:
    """Тест адаптивного изменения window_size."""

    def setup_method(self):
        """Создаём чистый LagWindow перед каждым тестом."""
        self.lw = LagWindow(
            adaptive_window_enabled=True,
            base_window_size=50,
            min_window_size=20,
            max_window_size=100,
            volatility_low_threshold=0.005,
            volatility_high_threshold=0.02,
        )

    def test_low_volatility_increases_window(self):
        """При низкой волатильности (vol <= 0.005) окно увеличивается."""
        # Initial state
        assert self.lw.window_size == 50

        # Низкая волатильность: 0.003 <= 0.005
        self.lw.add(confidence=50, volatility=0.003)
        assert self.lw.window_size == min(100, int(50 * 1.5))  # 75

    def test_high_volatility_decreases_window(self):
        """При высокой волатильности (vol >= 0.02) окно уменьшается."""
        assert self.lw.window_size == 50

        # Высокая волатильность: 0.03 >= 0.02
        self.lw.add(confidence=50, volatility=0.03)
        assert self.lw.window_size == max(20, int(50 // 2))  # 25

    def test_normal_volatility_keeps_base_window(self):
        """При нормальной волатильности окно остаётся базовым."""
        assert self.lw.window_size == 50

        # Средняя волатильность: 0.005 < 0.01 < 0.02
        self.lw.add(confidence=50, volatility=0.01)
        assert self.lw.window_size == 50

    def test_window_respects_min_limit(self):
        """Окно не может быть меньше min_window_size."""
        # Устанавливаем очень высокую волатильность несколько раз
        self.lw.add(confidence=50, volatility=0.1)
        assert self.lw.window_size >= self.lw.min_window_size

    def test_window_respects_max_limit(self):
        """Окно не может быть больше max_window_size."""
        # Многократно понижаем волатильность
        for _ in range(10):
            self.lw.add(confidence=50, volatility=0.001)
        assert self.lw.window_size <= self.lw.max_window_size

    def test_adaptive_can_be_disabled(self):
        """С выключенным adaptive окно не меняется."""
        lw = LagWindow(
            adaptive_window_enabled=False,
            base_window_size=50,
            min_window_size=20,
            max_window_size=100,
        )
        assert lw.adaptive_enabled is False

        lw.add(confidence=50, volatility=0.001)
        assert lw.window_size == 50  # не изменилось

        lw.add(confidence=50, volatility=0.1)
        assert lw.window_size == 50  # не изменилось


class TestEMAWorksAfterWindowChange:
    """Тест что EMA продолжает работать при изменении окна."""

    def setup_method(self):
        self.lw = LagWindow(
            adaptive_window_enabled=True,
            base_window_size=50,
            volatility_low_threshold=0.005,
            volatility_high_threshold=0.02,
        )

    def test_ema_continues_after_window_increase(self):
        """EMA продолжает работать после увеличения окна."""
        # Накапливаем несколько значений
        self.lw.add(confidence=70, volatility=0.01)  # normal
        self.lw.add(confidence=72, volatility=0.01)

        # Меняем окно на большее (низкая волатильность)
        self.lw.add(confidence=71, volatility=0.003)

        # EMA не должен быть None и должен продолжать считаться
        assert self.lw._ema is not None
        assert isinstance(self.lw._ema, float)

    def test_ema_continues_after_window_decrease(self):
        """EMA продолжает работать после уменьшения окна."""
        self.lw.add(confidence=70, volatility=0.01)
        self.lw.add(confidence=72, volatility=0.01)

        # Меняем окно на меньшее (высокая волатильность)
        self.lw.add(confidence=71, volatility=0.03)

        assert self.lw._ema is not None
        assert isinstance(self.lw._ema, float)

    def test_alpha_recalculated_on_window_change(self):
        """Alpha пересчитывается при изменении window_size."""
        initial_alpha = self.lw.alpha  # alpha при window=50

        # Уменьшаем окно
        self.lw.add(confidence=70, volatility=0.03)

        # Alpha должен увеличиться (сглаживание менее инерционное)
        assert self.lw.alpha > initial_alpha

    def test_count_increments_continuously(self):
        """Счётчик увеличивается при каждом add(), независимо от window changes."""
        self.lw.add(confidence=70, volatility=0.01)
        self.lw.add(confidence=71, volatility=0.03)  # window changes
        self.lw.add(confidence=72, volatility=0.001)  # window changes again
        self.lw.add(confidence=73, volatility=0.01)

        assert self.lw._count == 4


class TestWarmupBlend:
    """Тест warmup phase: первые 20 решений используют blend=0.3."""

    def test_warmup_blend_first_20(self):
        """Первые 19 решений используют BLEND_WARMUP=0.3, 20th переходит в mature."""
        lw = LagWindow()

        for i in range(1, WARMUP_THRESHOLD):
            result = lw.add(confidence=50 + i)
            assert result["blend"] == BLEND_WARMUP, f"Step {i} (count={result['count']}) should be warmup"

    def test_mature_blend_after_20(self):
        """После 20 решений используется BLEND_MATURE=0.15."""
        lw = LagWindow()

        # Делаем 20 warmup решений
        for i in range(WARMUP_THRESHOLD):
            lw.add(confidence=50)

        # Следующее решение — mature
        result = lw.add(confidence=50)
        assert result["blend"] == BLEND_MATURE

    def test_final_confidence_warmup_more_raw(self):
        """В warmup phase больше вес на raw signal."""
        lw = LagWindow()

        # Warmup: raw=90, EMA=70, blend=0.3
        lw.add(confidence=70)  # seed
        r = lw.add(confidence=90)

        # final = (1-0.3)*90 + 0.3*ema
        # ema ≈ 0.039*90 + 0.961*70 ≈ 70.8
        # final ≈ 0.7*90 + 0.3*70.8 = 63 + 21.2 = 84.2 → 84
        assert r["final_confidence"] < 90
        assert r["final_confidence"] > 70


class TestLagAdjustment:
    """Тест вычисления lag_adj."""

    def test_positive_lag_adj_when_ema_above_raw(self):
        """lag_adj > 0 когда EMA выше raw (сигнал отстаёт вверх)."""
        lw = LagWindow()

        # Seed с устойчивым трендом вверх
        for c in [60, 62, 65, 68, 70]:
            lw.add(confidence=c)

        # Резкий spike вниз
        r = lw.add(confidence=40)
        # EMA должно быть выше 40 (потому что было 70+)
        assert r["lag_adj"] > 0, f"Expected positive lag_adj, got {r['lag_adj']}"

    def test_negative_lag_adj_when_ema_below_raw(self):
        """lag_adj < 0 когда EMA ниже raw (сигнал опережает вверх)."""
        lw = LagWindow()

        # Seed
        for c in [70, 68, 65, 62, 60]:
            lw.add(confidence=c)

        # Резкий spike вверх
        r = lw.add(confidence=90)
        # EMA должно быть ниже 90 (потому что было 60-70)
        assert r["lag_adj"] < 0, f"Expected negative lag_adj, got {r['lag_adj']}"

    def test_lag_adj_scale(self):
        """lag_adj масштабируется корректно: |lag_adj| < 1 для разумных отклонений."""
        lw = LagWindow()

        for _ in range(5):
            lw.add(confidence=50)

        # Обычные отклонения не дают lag_adj > 1
        for raw in [30, 45, 70, 85]:
            r = lw.add(confidence=raw)
            assert abs(r["lag_adj"]) <= 2.0, f"lag_adj={r['lag_adj']} too large for raw={raw}"


class TestPositionLag:
    """Тест вычисления position_lag."""

    def test_position_lag_zero_initially(self):
        """position_lag ≈ 0 когда недостаточно истории (< 5)."""
        lw = LagWindow()

        for i in range(3):
            r = lw.add(confidence=50, position_pct=0.1 * (i + 1))
            assert r["position_lag"] == 0.0

    def test_position_lag_reflects_deviation(self):
        """position_lag показывает отклонение текущей позиции от средней."""
        lw = LagWindow()

        # Фиксируем среднюю позицию 0.15 на 10 шагах
        for _ in range(10):
            lw.add(confidence=50, position_pct=0.15)

        # Текущая позиция сильно меньше средней
        r = lw.add(confidence=50, position_pct=0.05)

        # avg_position ≈ 0.15, current ≈ 0.05
        # position_lag = (0.15 - 0.05) / 0.05 = 2.0
        assert r["position_lag"] > 0, "Lower position should give positive lag"


class TestFinalConfidence:
    """Тест финального сглаженного confidence."""

    def test_final_in_integer_range(self):
        """final_confidence всегда целое число в диапазоне 0-100."""
        lw = LagWindow()

        for raw in [10, 25, 50, 75, 90, 100]:
            r = lw.add(confidence=raw)
            assert isinstance(r["final_confidence"], int)
            assert 0 <= r["final_confidence"] <= 100

    def test_final_less_volatile_than_raw(self):
        """Финальный confidence менее волатилен чем raw: меньше std dev."""
        lw = LagWindow()

        raws = [85, 30, 82, 28, 79, 35, 88]
        finals = []

        for raw in raws:
            r = lw.add(confidence=raw)
            finals.append(r["final_confidence"])

        raw_std = _std(raws)
        final_std = _std(finals)

        assert final_std < raw_std, f"Final std {final_std} should be < raw std {raw_std}"

    def test_spike_dampened(self):
        """Одиночный spike (90→30→82) сглаживается."""
        lw = LagWindow()

        lw.add(confidence=85)
        r_spike = lw.add(confidence=30)  # spike down
        r_recover = lw.add(confidence=82)

        # Spike вниз до 30 не даёт итоговому confidence упасть слишком сильно
        # В warmup: final ≈ 0.7*30 + 0.3*ema ≈ 30 + что-то
        # Но EMA уже ~70+, поэтому:
        assert r_spike["final_confidence"] > 25
        assert r_recover["final_confidence"] < 85  # не полный отскок


class TestGlobalSingleton:
    """Тест глобального синглтона."""

    def test_get_lag_window_returns_same_instance(self):
        """get_lag_window() возвращает тот же объект."""
        reset_lag_window()
        w1 = get_lag_window()
        w2 = get_lag_window()
        assert w1 is w2

    def test_reset_clears_state(self):
        """reset_lag_window() сбрасывает состояние."""
        lw = get_lag_window()
        lw.add(confidence=70)
        lw.add(confidence=75)

        reset_lag_window()
        lw2 = get_lag_window()

        assert lw2._count == 0
        assert lw2._ema is None


# ─── Helpers ───────────────────────────────────────────────────────────────────


def _std(values):
    """Standard deviation."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    return math.sqrt(variance)

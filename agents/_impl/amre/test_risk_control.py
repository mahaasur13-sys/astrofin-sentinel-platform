"""amre/test_risk_control.py — ATOM-KARL-015 Phase 5: Tests for risk_control.py

Tests:
1. Feature flag off → no changes
2. Перегрев (lag < -0.3) → позиция умножается на 0.8
3. Недоторговка (lag > +0.3) → позиция умножается на 1.1
4. Лаг внутри порога → без изменений
5. Границы min/max срабатывают
6. Граничные значения порога

Запуск:
    pytest agents/_impl/amre/test_risk_control.py -v
"""
from __future__ import annotations


from unittest.mock import patch

# Импортируем после patch окружения
from agents._impl.amre.risk_control import (
    RISK_MAX_POSITION,
    RISK_MIN_POSITION,
    apply_position_lag_risk,
)


class TestFeatureFlag:
    """Тест feature flag RISK_USE_POSITION_LAG."""

    def test_flag_disabled_returns_unchanged(self):
        """Когда RISK_USE_POSITION_LAG=False, функция возвращает позицию без изменений."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", False):
            pos = 0.10
            result = apply_position_lag_risk(pos, 5.0)  # любой lag
            assert result == pos

    def test_flag_enabled_changes_position(self):
        """Когда RISK_USE_POSITION_LAG=True, функция корректирует позицию."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.10
            # Сильная недоторговка (lag > +0.3) → увеличиваем
            result = apply_position_lag_risk(pos, 2.0)
            assert result != pos


class TestOverheatReduction:
    """Тест reduction при перегреве (position_lag < -threshold)."""

    def test_reduction_factor_applied(self):
        """lag < -0.3 → позиция умножается на 0.8."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.10
            result = apply_position_lag_risk(pos, -0.5)
            assert abs(result - pos * 0.8) < 1e-9

    def test_reduction_boundary(self):
        """lag = -0.3 (ровно на границе) → без изменений."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.10
            result = apply_position_lag_risk(pos, -0.3)
            assert result == pos

    def test_reduction_deep_overheat(self):
        """Сильный перегрев (lag = -1.0) → позиция значительно сокращается."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.15
            result = apply_position_lag_risk(pos, -1.0)
            expected = pos * 0.8
            assert result == expected


class TestUndertradeIncrease:
    """Тест увеличения при недоторговке (position_lag > +threshold)."""

    def test_increase_factor_applied(self):
        """lag > +0.3 → позиция умножается на 1.1."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.10
            result = apply_position_lag_risk(pos, 0.5)
            assert abs(result - pos * 1.1) < 1e-9

    def test_increase_boundary(self):
        """lag = +0.3 (ровно на границе) → без изменений."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.10
            result = apply_position_lag_risk(pos, 0.3)
            assert result == pos

    def test_increase_strong_undertrade(self):
        """Сильная недоторговка (lag = 2.0) → позиция увеличивается."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.05
            result = apply_position_lag_risk(pos, 2.0)
            expected = pos * 1.1
            assert result == expected


class TestNeutralZone:
    """Тест нейтральной зоны (-threshold < lag < +threshold)."""

    def test_within_threshold_no_change(self):
        """lag внутри [-0.3, +0.3] → без изменений."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.10
            for lag in [-0.29, -0.1, 0.0, 0.15, 0.29]:
                result = apply_position_lag_risk(pos, lag)
                assert result == pos, f"lag={lag} should not change position"

    def test_zero_lag_no_change(self):
        """lag = 0 → без изменений."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.12
            result = apply_position_lag_risk(pos, 0.0)
            assert result == pos


class TestMinMaxBounds:
    """Тест границ RISK_MIN_POSITION и RISK_MAX_POSITION."""

    def test_min_position_enforced_on_reduction(self):
        """При reduction нельзя опуститься ниже RISK_MIN_POSITION=0.01."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.012  # 0.012 * 0.8 = 0.0096 → clipped to 0.01
            result = apply_position_lag_risk(pos, -5.0)  # сильный перегрев
            assert result == RISK_MIN_POSITION

    def test_max_position_enforced_on_increase(self):
        """При increase нельзя превысить RISK_MAX_POSITION=0.20."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.19  # близко к максимуму
            result = apply_position_lag_risk(pos, 2.0)
            assert result <= RISK_MAX_POSITION

    def test_reduction_clipped_to_min(self):
        """0.012 * 0.8 = 0.0096.clip(0.01) = 0.01."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.012  # 0.012 * 0.8 = 0.0096 → clipped to 0.01
            result = apply_position_lag_risk(pos, -5.0)  # сильный перегрев
            assert result == RISK_MIN_POSITION

    def test_increase_clipped_to_max(self):
        """Increase до 0.22.clip(0.20) = 0.20."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.19
            result = apply_position_lag_risk(pos, 10.0)  # сильная недоторговка
            assert result == RISK_MAX_POSITION


class TestEdgeCases:
    """Edge cases."""

    def test_zero_position(self):
        """Нулевая позиция — clipping не должен ломать."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            result = apply_position_lag_risk(0.0, 2.0)
            assert 0.0 <= result <= RISK_MAX_POSITION

    def test_small_position_at_min_reduction(self):
        """Очень маленькая позиция при reduction → не ниже min."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.011
            result = apply_position_lag_risk(pos, -1.0)
            assert result >= RISK_MIN_POSITION - 1e-9

    def test_large_position_at_max_increase(self):
        """Большая позиция при increase → не выше max."""
        with patch("agents._impl.amre.risk_control.RISK_USE_POSITION_LAG", True):
            pos = 0.21
            result = apply_position_lag_risk(pos, 1.0)
            assert result <= RISK_MAX_POSITION + 1e-9

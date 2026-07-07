"""amre/oap_optimizer.py — OAP + KPI Control Loop (ATOM-KARL-010)
Оптимизация позиций + адаптивный control loop на основе KPI.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .audit import get_audit_log


class OptimizationStatus(Enum):
    OPTIMIZED = "optimized"
    STABLE = "stable"
    DEGRADED = "degraded"


class ControlAction(Enum):
    """Действия control loop"""

    INCREASE_TTC_DEPTH = "increase_ttc_depth"
    DECREASE_TTC_DEPTH = "decrease_ttc_depth"
    BOOST_EXPLORATION = "boost_exploration"
    TIGHTEN_GROUNDING = "tighten_grounding"
    REDUCE_POSITION = "reduce_position"
    INCREASE_POSITION = "increase_position"
    RESET_AGENTS = "reset_agents"
    NO_ACTION = "no_action"


@dataclass
class OAPConfig:
    """Конфигурация OAP"""

    min_confidence: int = 65
    max_position_pct: float = 0.10
    uncertainty_threshold: float = 0.60
    kelly_fraction: float = 0.25

    # Control loop thresholds
    uncertainty_high_threshold: float = 0.60
    entropy_low_threshold: float = 0.30
    oos_fail_high_threshold: float = 0.40

    # Adaptive parameters
    base_ttc_depth: int = 3
    base_exploration_rate: float = 0.10
    base_grounding_strength: float = 0.80


@dataclass
class ValidationState:
    """Состояние после валидации OAP"""

    decision_id: str
    timestamp: str
    status: OptimizationStatus
    confidence: int
    position_pct: float
    confidence_boost: int
    regime: str
    issues: list[str]
    control_actions: list[ControlAction]


@dataclass
class KPIControlState:
    """Текущее состояние KPI control loop"""

    current_ttc_depth: int
    current_exploration_rate: float
    current_grounding_strength: float

    uncertainty_avg: float
    entropy_avg: float
    oos_fail_rate: float

    # History
    control_history: list[dict[str, Any]]

    def to_dict(self) -> dict:
        return {
            "ttc_depth": self.current_ttc_depth,
            "exploration_rate": self.current_exploration_rate,
            "grounding_strength": self.current_grounding_strength,
            "uncertainty_avg": round(self.uncertainty_avg, 4),
            "entropy_avg": round(self.entropy_avg, 4),
            "oos_fail_rate": round(self.oos_fail_rate, 4),
            "control_actions_count": len(self.control_history),
        }


class OAPOptimizer:
    """
    OAP (Optimal Advantage Positioner) + KPI Control Loop.

    Control loop:
        if kpi["uncertainty"] > 0.6: increase_ttc_depth()
        if kpi["entropy"] < 0.3: boost_exploration()
        if kpi["oos_fail_rate"] > 0.4: tighten_grounding()

    Превращает систему в self-regulating adaptive system.
    """

    def __init__(self, config: OAPConfig | None = None):
        self.config = config or OAPConfig()
        self.history: list[ValidationState] = []

        # KPI Control State
        self.kpi_state = KPIControlState(
            current_ttc_depth=self.config.base_ttc_depth,
            current_exploration_rate=self.config.base_exploration_rate,
            current_grounding_strength=self.config.base_grounding_strength,
            uncertainty_avg=0.5,
            entropy_avg=0.5,
            oos_fail_rate=0.0,
            control_history=[],
        )

    def validate_and_adjust(
        self,
        amre_data: dict[str, Any],
        base_confidence: int,
        base_position: float,
    ) -> ValidationState:
        """
        Валидирует решение и применяет OAP adjustments.
        """
        uncertainty = amre_data.get("uncertainty", {}).get("total", 0.5)
        q_star = amre_data.get("q_star", 0.5)
        regime = amre_data.get("regime", "NORMAL")

        conf_boost = 0
        pos_adj = 1.0
        issues = []
        control_actions: list[ControlAction] = []

        # OAP Validation Rules
        if uncertainty > self.config.uncertainty_threshold:
            conf_boost -= 15
            pos_adj *= 0.5
            issues.append(f"High uncertainty ({uncertainty:.2f}) - halving position")

        if regime == "EXTREME":
            conf_boost -= 15
            pos_adj *= 0.3
            issues.append("EXTREME regime - reducing position to 30%")

        if q_star < 0.4:
            conf_boost -= 10
            pos_adj *= 0.7
            issues.append(f"Low Q* ({q_star:.2f}) - reducing position to 70%")

        # Apply control loop adjustments
        control_actions = self._compute_control_actions(amre_data)
        for action in control_actions:
            conf_boost, pos_adj = self._apply_control_action(action, conf_boost, pos_adj, amre_data)

        final_conf = max(30, min(92, base_confidence + conf_boost))
        final_pos = min(self.config.max_position_pct, base_position * pos_adj)

        status = self._determine_status(issues, control_actions)

        state = ValidationState(
            decision_id=f"OAP_{len(self.history)}",
            timestamp=amre_data.get("timestamp", ""),
            status=status,
            confidence=final_conf,
            position_pct=round(final_pos, 4),
            confidence_boost=conf_boost,
            regime=regime,
            issues=issues,
            control_actions=control_actions,
        )

        self.history.append(state)
        return state

    def _compute_control_actions(self, amre_data: dict[str, Any]) -> list[ControlAction]:
        """
        Вычисляет actions для KPI control loop.

        Rules:
            if kpi["uncertainty"] > 0.6: increase_ttc_depth()
            if kpi["entropy"] < 0.3: boost_exploration()
            if kpi["oos_fail_rate"] > 0.4: tighten_grounding()
        """
        actions: list[ControlAction] = []

        kpi = amre_data.get("kpi", {})

        uncertainty = kpi.get("uncertainty", self.kpi_state.uncertainty_avg)
        entropy = kpi.get("entropy", self.kpi_state.entropy_avg)
        oos_fail_rate = kpi.get("oos_fail_rate", self.kpi_state.oos_fail_rate)

        # Update running averages
        self.kpi_state.uncertainty_avg = self.kpi_state.uncertainty_avg * 0.9 + uncertainty * 0.1
        self.kpi_state.entropy_avg = self.kpi_state.entropy_avg * 0.9 + entropy * 0.1
        self.kpi_state.oos_fail_rate = self.kpi_state.oos_fail_rate * 0.9 + oos_fail_rate * 0.1

        # Control rules
        if uncertainty > self.config.uncertainty_high_threshold:
            actions.append(ControlAction.INCREASE_TTC_DEPTH)

        if entropy < self.config.entropy_low_threshold:
            actions.append(ControlAction.BOOST_EXPLORATION)

        if oos_fail_rate > self.config.oos_fail_high_threshold:
            actions.append(ControlAction.TIGHTEN_GROUNDING)

        # Additional rules based on drift
        if amre_data.get("is_degrading", False):
            actions.append(ControlAction.TIGHTEN_GROUNDING)

        return actions

    def _apply_control_action(
        self,
        action: ControlAction,
        conf_boost: int,
        pos_adj: float,
        amre_data: dict[str, Any],
    ) -> tuple[int, float]:
        """Применяет control action к confidence и position"""

        if action == ControlAction.INCREASE_TTC_DEPTH:
            self.kpi_state.current_ttc_depth = min(5, self.kpi_state.current_ttc_depth + 1)
            self.kpi_state.control_history.append(
                {
                    "action": action.value,
                    "timestamp": amre_data.get("timestamp", ""),
                    "reason": f"High uncertainty: {self.kpi_state.uncertainty_avg:.2f}",
                }
            )

        elif action == ControlAction.DECREASE_TTC_DEPTH:
            self.kpi_state.current_ttc_depth = max(1, self.kpi_state.current_ttc_depth - 1)

        elif action == ControlAction.BOOST_EXPLORATION:
            self.kpi_state.current_exploration_rate = min(0.3, self.kpi_state.current_exploration_rate + 0.05)
            conf_boost -= 5  # Lower confidence when exploring more
            self.kpi_state.control_history.append(
                {
                    "action": action.value,
                    "timestamp": amre_data.get("timestamp", ""),
                    "reason": f"Low entropy: {self.kpi_state.entropy_avg:.2f}",
                }
            )

        elif action == ControlAction.TIGHTEN_GROUNDING:
            self.kpi_state.current_grounding_strength = min(1.0, self.kpi_state.current_grounding_strength + 0.1)
            self.kpi_state.control_history.append(
                {
                    "action": action.value,
                    "timestamp": amre_data.get("timestamp", ""),
                    "reason": f"High OOS fail rate: {self.kpi_state.oos_fail_rate:.2f}",
                }
            )

        elif action == ControlAction.REDUCE_POSITION:
            pos_adj *= 0.8
            conf_boost -= 5

        elif action == ControlAction.INCREASE_POSITION:
            pos_adj *= 1.2

        return conf_boost, pos_adj

    def _determine_status(
        self,
        issues: list[str],
        control_actions: list[ControlAction],
    ) -> OptimizationStatus:
        """Определяет статус оптимизации"""

        # Если были серьёзные issues
        if any("EXTREME" in i for i in issues):
            return OptimizationStatus.DEGRADED

        # Если применялись строгие control actions
        if ControlAction.TIGHTEN_GROUNDING in control_actions:
            return OptimizationStatus.STABLE

        # Если есть только minor issues
        if issues:
            return OptimizationStatus.STABLE

        return OptimizationStatus.OPTIMIZED

    def get_kpi_state(self) -> KPIControlState:
        """Returns текущее состояние KPI control"""
        return self.kpi_state

    def get_control_recommendations(self) -> list[str]:
        """Рекомендации для control loop"""
        recs = []

        if self.kpi_state.uncertainty_avg > self.config.uncertainty_high_threshold:
            recs.append(f"Consider increasing TTC depth (current: {self.kpi_state.current_ttc_depth})")

        if self.kpi_state.entropy_avg < self.config.entropy_low_threshold:
            recs.append(f"Consider boosting exploration (current: {self.kpi_state.current_exploration_rate:.2f})")

        if self.kpi_state.oos_fail_rate > self.config.oos_fail_high_threshold:
            recs.append(f"Consider tightening grounding (current: {self.kpi_state.current_grounding_strength:.2f})")

        return recs

    def sync_with_audit(self) -> dict[str, Any]:
        """
        Синхронизирует KPI state с данными из Audit Log.
        Вызывается периодически для корректировки.
        """
        audit = get_audit_log()

        if len(audit.records) < 10:
            return {"status": "insufficient_data"}

        # Анализируем последние решения
        recent = audit.get_recent(50)

        # OOS fail rate
        high_conf_decisions = [r for r in recent if r.confidence_final >= 70]
        oos_fails = [r for r in high_conf_decisions if r.kpi_snapshot.oos_fail_rate > 0.5]

        new_oos_fail_rate = len(oos_fails) / len(high_conf_decisions) if high_conf_decisions else 0

        # Entropy (из variance confidence)
        confs = [r.confidence_final for r in recent]
        import statistics

        entropy = statistics.stdev(confs) / 100 if len(confs) > 1 else 0

        # Apply corrections
        self.kpi_state.oos_fail_rate = self.kpi_state.oos_fail_rate * 0.7 + new_oos_fail_rate * 0.3
        self.kpi_state.entropy_avg = self.kpi_state.entropy_avg * 0.7 + entropy * 0.3

        return {
            "synced": True,
            "oos_fail_rate": round(self.kpi_state.oos_fail_rate, 4),
            "entropy": round(self.kpi_state.entropy_avg, 4),
            "recommendations": self.get_control_recommendations(),
        }


# =============================================================================
# Global singleton
# =============================================================================

_OAP_OPTIMIZER: OAPOptimizer | None = None


def get_oap_optimizer() -> OAPOptimizer:
    global _OAP_OPTIMIZER
    if _OAP_OPTIMIZER is None:
        _OAP_OPTIMIZER = OAPOptimizer()
    return _OAP_OPTIMIZER

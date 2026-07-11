#!/usr/bin/env python3
"""ROMA Cost Decision Gate — Enforces cost boundaries before execution.

Финальная версия шлюза стоимости для ROMA Execution Bridge.
Учитывает все выявленные проблемы:
- Динамическое определение BASE_DIR (убраны жёсткие пути)
- CostPredictor.predict() не принимает 'tier'
- Безопасная фильтрация kwargs
- Специальная обработка случая estimated_cost = $0.00
- Чёткая типизация и документация
- Надёжная обработка ошибок
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, TypedDict

# ====================== BASE DIRECTORY ======================
BASE_DIR = Path(__file__).resolve().parent.parent  # roma-execution-bridge/
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from cost.predictor import CostPredictor
from tenancy.manager import TenantManager


class GateResponse(TypedDict, total=False):
    """Стандартизированный ответ DecisionGate."""
    task: str
    tenant_id: str
    tier: str
    estimated_cost: float
    decision: str
    can_proceed: bool
    execution_blocked: bool
    requires_confirmation: bool
    approval_required: bool
    gate_message: str
    suggested_action: str
    risk_flags: List[str]
    gpu_seconds: int
    confidence: float


class DecisionGate:
    """
    Cost Decision Gate — основной шлюз контроля затрат в ROMA.

    Принимает решение:
      - APPROVED              → можно запускать сразу
      - REQUIRES_CONFIRMATION → нужно подтвердить (включая $0.00)
      - REJECTED              → блокировка выполнения
    """

    TIER_LIMITS: Dict[str, float] = {
        "FREE": 1.0,
        "PRO": 50.0,
        "ENTERPRISE": 500.0,
    }

    DEFAULT_LIMIT: float = 10.0

    def __init__(self):
        self.predictor = CostPredictor()
        self.tenancy = TenantManager()
        self.decision_history: List[GateResponse] = []

    def decide(self, task: str, plugin_type: str = "default",
               gpu_required: bool = False, tenant_id: str = "default-tenant",
               **kwargs) -> Dict[str, Any]:
        """
        Основной метод, который должен вызываться из CLI и API.
        Возвращает упрощённый словарь для удобства использования.
        """
        result = self.evaluate(task, gpu_required, plugin_type, tenant_id, **kwargs)

        return {
            "action": result["decision"],
            "reason": result.get("gate_message", ""),
            "final_cost": result["estimated_cost"],
            "can_proceed": result["can_proceed"],
            "execution_blocked": result["execution_blocked"],
            "requires_confirmation": result["requires_confirmation"],
            "full_response": result,
        }

    def evaluate(self, task: str, gpu_required: bool, plugin_type: str,
                 tenant_id: str = "default-tenant", **kwargs) -> GateResponse:
        """Основная логика оценки стоимости и принятия решения."""
        if not task or not isinstance(task, str):
            raise ValueError("Параметр 'task' обязателен и должен быть непустой строкой.")

        try:
            # Получаем тарифный план тенанта
            tenant_info = self.tenancy.get_tenant_info(tenant_id)
            tier: str = (tenant_info.get("plan") or "FREE").upper()

            # Фильтруем только разрешённые аргументы для CostPredictor
            allowed_kwargs = {
                "custom_duration", "duration_sec", "epochs", "batch_size",
                "dataset_size", "model_size", "image_count", "gpu_seconds", "steps"
            }
            clean_kwargs = {k: v for k, v in kwargs.items() if k in allowed_kwargs}

            # Вызываем предиктор (ВАЖНО: без параметра tier!)
            prediction: Dict[str, Any] = self.predictor.predict(
                task, gpu_required, plugin_type, **clean_kwargs
            )

            cost: float = float(prediction.get("estimated_cost", 0.0))
            decision: str = prediction.get("decision", "UNKNOWN")
            risk_flags: List[str] = prediction.get("risk_flags", [])
            breakdown: Dict = prediction.get("breakdown", {})

            # Автоматическое определение решения, если predictor его не вернул
            if decision not in ("APPROVED", "REQUIRES_CONFIRMATION", "REJECTED"):
                limit = self.TIER_LIMITS.get(tier, self.DEFAULT_LIMIT)
                if cost > limit:
                    decision = "REJECTED"
                elif cost == 0.0 or cost > limit * 0.7:   # $0.00 считаем как "требует подтверждения"
                    decision = "REQUIRES_CONFIRMATION"
                else:
                    decision = "APPROVED"

            response: GateResponse = {
                "task": task,
                "tenant_id": tenant_id,
                "tier": tier,
                "estimated_cost": cost,
                "decision": decision,
                "can_proceed": decision == "APPROVED",
                "execution_blocked": decision == "REJECTED",
                "requires_confirmation": decision == "REQUIRES_CONFIRMATION",
                "approval_required": decision != "APPROVED",
                "gate_message": self._gate_message(decision, cost, tier, risk_flags),
                "suggested_action": self._suggested_action(decision, tier),
                "risk_flags": risk_flags,
                "gpu_seconds": int(breakdown.get("gpu_seconds", 0)),
                "confidence": prediction.get("confidence", 0.85),
            }

            self.decision_history.append(response)
            return response

        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] DecisionGate: {type(e).__name__}: {e}", file=sys.stderr)
            return self._create_error_response(task, tenant_id, e)

    def _create_error_response(self, task: str, tenant_id: str, exc: Exception) -> GateResponse:
        return {
            "task": task,
            "tenant_id": tenant_id,
            "tier": "UNKNOWN",
            "estimated_cost": 0.0,
            "decision": "REJECTED",
            "can_proceed": False,
            "execution_blocked": True,
            "requires_confirmation": False,
            "approval_required": True,
            "gate_message": f"EXECUTOR BLOCKED: {type(exc).__name__} - {exc}",
            "suggested_action": "Contact support or try again later",
            "risk_flags": ["SYSTEM_ERROR"],
        }

    def _gate_message(self, decision: str, cost: float, tier: str, risk_flags: List[str]) -> str:
        limit = self.TIER_LIMITS.get(tier, self.DEFAULT_LIMIT)

        if decision == "REJECTED":
            return f"EXECUTOR BLOCKED: cost ${cost:.4f} exceeds {tier} plan limit ${limit:.2f}"
        elif decision == "REQUIRES_CONFIRMATION":
            flags = f" [{', '.join(risk_flags)}]" if risk_flags else ""
            return f"CONFIRMATION REQUIRED: cost ${cost:.4f} ({tier} limit ${limit:.2f}){flags}"
        return f"APPROVED: cost ${cost:.4f} within {tier} plan limits"

    def _suggested_action(self, decision: str, tier: str) -> str:
        if decision == "REJECTED":
            return "Upgrade to PRO/ENTERPRISE plan or reduce task duration."
        elif decision == "REQUIRES_CONFIRMATION":
            return "Confirm with: roma run --confirm-cost"
        return "Ready to execute — proceed with roma run"

    def get_gate_status(self, tenant_id: str = "default-tenant") -> Dict[str, Any]:
        """Статистика решений по тенанту."""
        tenant_decisions = [d for d in self.decision_history if d.get("tenant_id") == tenant_id]
        if not tenant_decisions:
            return {"total_evaluations": 0}

        return {
            "total_evaluations": len(tenant_decisions),
            "approved": sum(1 for d in tenant_decisions if d.get("decision") == "APPROVED"),
            "rejected": sum(1 for d in tenant_decisions if d.get("decision") == "REJECTED"),
            "requires_confirmation": sum(1 for d in tenant_decisions if d.get("decision") == "REQUIRES_CONFIRMATION"),
        }


# ====================== QUICK TEST ======================
if __name__ == "__main__":
    gate = DecisionGate()
    result = gate.evaluate(
        task="train model on GPU",
        gpu_required=True,
        plugin_type="default",
        tenant_id="default-tenant"
    )

    print("=== DecisionGate Test ===")
    print(f"Decision : {result['decision']}")
    print(f"Cost     : ${result['estimated_cost']:.4f}")
    print(f"Message  : {result['gate_message']}")
    print(f"Action   : {result['suggested_action']}")

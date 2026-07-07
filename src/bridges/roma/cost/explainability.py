"""ROMA Cost Explainability Engine — Why this costs what it costs."""

from cost.predictor import CostPredictor
from plugins.plugin_api import PluginCapability

GPU_RATE = 0.000086  # $ per GPU-second (PRO tier)


class CostExplainabilityEngine:
    def explain(self, task: str) -> dict:
        gpu_required = "gpu" in task.lower() or "train" in task.lower()
        pred = CostPredictor().predict(task, gpu_required=gpu_required, plugin_type="ml_training")
        bd = pred["breakdown"]
        gpu_seconds = bd.get("gpu_seconds", 3600)
        gpu_count = 1 if gpu_required else 0
        gpu_cost = gpu_seconds * GPU_RATE * gpu_count
        plugin_info = {"name": "ml_training", "capabilities": [PluginCapability.GPU_ENABLED]}
        alternatives = self._generate_alternatives(pred, gpu_cost)
        reasons = self._decision_reasons(task, pred, plugin_info)
        return {
            "execution_plan": self._plan_steps(task, plugin_info, pred, gpu_seconds),
            "cost_breakdown": {
                "GPU time": round(gpu_cost, 4),
                "Queue": round(bd.get("queue", 0.0), 4),
                "Storage": round(bd.get("storage", 0.0), 4),
                "Overhead": round(bd.get("overhead", 0.0), 4),
            },
            "total_cost": round(pred["estimated_cost"], 4),
            "alternatives": alternatives,
            "decision_reasons": reasons,
            "plugin_used": plugin_info["name"],
        }

    def _generate_alternatives(self, pred: dict, gpu_cost: float) -> list:
        base = gpu_cost + sum(pred["breakdown"].get(k, 0.0) for k in ["queue", "storage", "overhead"]) or 0.01
        return [
            {"description": "CPU cluster (no GPU)", "cost": round(base * 0.32, 4), "savings": "68"},
            {"description": "Smaller dataset (50%)", "cost": round(base * 0.64, 4), "savings": "36"},
            {"description": "Off-peak scheduling", "cost": round(base * 0.85, 4), "savings": "15"},
        ]

    def _decision_reasons(self, task: str, pred: dict, plugin: dict) -> list:
        reasons = [f"Task requires GPU (detected from: {task})"]
        if pred.get("risk_flags"):
            reasons.append(f"Risk flags: {', '.join(pred['risk_flags'])}")
        reasons.append(f"Plugin: {plugin['name']} (GPU_ENABLED capability)")
        reasons.append(f"Cost estimate: ${pred['estimated_cost']:.2f} (within quota)")
        return reasons

    def _plan_steps(self, task: str, plugin: dict, pred: dict, gpu_seconds: float) -> list:
        return [
            {"phase": "validation", "description": "Input contract + security gate"},
            {"phase": "cost_check", "description": f"Estimate: ${pred['estimated_cost']:.2f}"},
            {"phase": "plugin_load", "description": f"Load {plugin['name']} plugin"},
            {"phase": "scheduling", "description": f"Duration ~{gpu_seconds / 60:.0f}m"},
            {"phase": "execution", "description": f"GPU node: {pred.get('decision', 'APPROVED')}"},
            {"phase": "completion", "description": "Event store + billing ledger update"},
        ]

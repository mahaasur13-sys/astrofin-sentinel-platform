#!/usr/bin/env python3
"""
ROMA CLI — полноценный интерфейс командной строки.

Команды:
  run "task"          — оценка стоимости и отправка задачи на сервер
  explain "task"      — объяснение решения по задаче
  cost "task"         — только предварительный расчёт стоимости
  status [job_id]     — статус задачи (из API)
  health              — проверка здоровья сервера
  list                — список задач (заглушка)
  logs <job_id> [lines] — логи задачи (заглушка)
  dashboard           — запуск дашборда
"""

import json
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)


# ====================== БАЗОВЫЙ ПУТЬ ======================
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import urllib.error

# ---------- HTTP-клиент (без сторонних библиотек) ----------
import urllib.request

from cost.estimator import RuntimeEstimator
from cost.explainability import CostExplainabilityEngine
from cost.gate import DecisionGate
from cost.predictor import CostPredictor
from plugins.plugin_runtime import PluginRuntime

API_BASE = os.environ.get("ROMA_API_URL", "http://localhost:8080")


def _api_get(path: str) -> dict:
    """GET-запрос к API, возвращает распарсенный JSON."""
    url = f"{API_BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        log.info(f"❌ HTTP {e.code} {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        log.info(f"❌ Не могу подключиться к {API_BASE} ({e.reason})")
        sys.exit(1)


def _api_post(path: str, payload: dict) -> dict:
    """POST-запрос к API, возвращает JSON-ответ."""
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        log.info(f"❌ HTTP {e.code} {e.reason}")
        body = e.read().decode()
        if body:
            log.info(f"   Тело ответа: {body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        log.info(f"❌ Не удалось подключиться к серверу: {e.reason}")
        sys.exit(1)


class ROMA_CLI:
    PROMPT_OPTIONS = """
[yes]  Выполнить как запланировано
[opt]  Показать более дешёвые альтернативы
[cancel]  Отмена"""

    def __init__(self):
        self.predictor = CostPredictor()
        self.gate = DecisionGate()
        self.estimator = RuntimeEstimator()
        self.explainer = CostExplainabilityEngine()
        self.runtime = PluginRuntime()

    # =================================================================
    # ОСНОВНЫЕ КОМАНДЫ
    # =================================================================

    def cmd_run(self, task: str) -> int:
        """Оценка стоимости и отправка задачи на сервер."""
        log.info(f"\n🎯 Задача: {task}\n")
        log.info("⏳ Анализирую...")

        # Предсказание стоимости
        prediction = self.predictor.predict(
            task,
            gpu_required=("gpu" in task.lower() or "train" in task.lower())
        )

        # Вывод базовой информации
        log.info(f"\n💰 Ожидаемая стоимость: ${prediction['estimated_cost']:.2f}")
        log.info(f"⏱  Расчётная длительность: ~{self._format_duration(prediction.get('estimated_duration_minutes', 0))}")
        log.info(f"🖥  GPU: {prediction.get('gpu_node', 'cpu-cluster')} (×{prediction.get('gpu_count', 0)})")
        log.info(f"⚠️  Уровень риска: {prediction.get('risk_level', 'LOW')}\n")
        log.info(self._breakdown_str(prediction.get('breakdown', {})))

        # Принимаем решение через Gate
        decision = self.gate.decide(
            task,
            plugin_type="default",
            gpu_required=prediction.get("gpu_required", False),
            tenant_id="default-tenant",
            **prediction
        )

        if decision['action'] == "REJECTED":
            log.info(f"\n🚫 ОТКЛОНЕНО: {decision['reason']}")
            return 1

        if decision['action'] == "REQUIRES_CONFIRMATION":
            log.info(f"\n⚠️  Предупреждение: стоимость ${decision['final_cost']:.2f} — подтвердите?")
            log.info(self.PROMPT_OPTIONS)
            choice = input("\n> ").strip().lower()
            if choice in ("cancel", "c"):
                log.info("Отменено.")
                return 0
            if choice in ("opt", "o"):
                self._show_alternatives(task)
                return self.cmd_run(task)

        # Отправка задачи на сервер
        log.info(f"\n✅ {decision['action']}: ${decision.get('final_cost', prediction['estimated_cost']):.2f}")
        log.info("\n🚀 Отправляю задачу на сервер...")
        job_id = self._submit_job(task, prediction)

        if job_id:
            log.info(f"✅ Задача принята, job_id: {job_id}")
            log.info(f"   Проверить статус: roma status {job_id}")
            return 0
        else:
            log.info("❌ Не удалось отправить задачу.")
            return 1

    def cmd_explain(self, task: str) -> int:
        """Объяснение решения."""
        log.info(f"\n🧠 Объяснение: {task}\n")
        explanation = self.explainer.explain(task)
        log.info("=" * 50)
        log.info("📋 ПЛАН ВЫПОЛНЕНИЯ")
        for step in explanation['execution_plan']:
            log.info(f"  {step['phase']}: {step['description']}")
        log.info("\n💰 РАЗБОР СТОИМОСТИ")
        for item, cost in explanation['cost_breakdown'].items():
            log.info(f"  {item}: ${cost:.2f}")
        log.info(f"\n  ВСЕГО: ${explanation['total_cost']:.2f}")
        if explanation.get('alternatives'):
            log.info("\n💡 БОЛЕЕ ДЕШЁВЫЕ АЛЬТЕРНАТИВЫ")
            for alt in explanation['alternatives']:
                log.info(f"  • {alt['description']} → ${alt['cost']:.2f} (экономия {alt['savings']}%)")
        log.info("\n🔍 ПОЧЕМУ ТАКОЕ РЕШЕНИЕ")
        for reason in explanation['decision_reasons']:
            log.info(f"  • {reason}")
        return 0

    def cmd_cost(self, task: str) -> int:
        """Быстрый расчёт стоимости."""
        log.info(f"\n💰 Оценка стоимости: {task}\n")
        prediction = self.predictor.predict(
            task,
            gpu_required=("gpu" in task.lower() or "train" in task.lower())
        )
        # Выводим только ключевые цифры
        result = {
            "estimated_cost": round(prediction['estimated_cost'], 4),
            "duration_minutes": prediction.get('estimated_duration_minutes', 0),
            "gpu_node": prediction.get('gpu_node', 'cpu-cluster'),
            "risk": prediction.get('risk_level', 'LOW')
        }
        log.info(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    def cmd_status(self, job_id: str = None) -> int:
        """Статус задачи через API."""
        if not job_id:
            log.info("⚠️  Укажите job_id (например, roma status <id>)")
            return 1

        data = _api_get(f"/status/{job_id}")
        log.info(f"\n🖥  Задача: {data['job_id']}")
        log.info(f"📌 Статус: {data['status']}")
        log.info(f"🕒 Создана: {data['created_at']}")
        if data.get('started_at'):
            log.info(f"▶️  Запущена: {data['started_at']}")
        if data.get('completed_at'):
            log.info(f"✅ Завершена: {data['completed_at']}")
        if data.get('error'):
            log.info(f"❌ Ошибка: {data['error']}")
        return 0

    def cmd_health(self) -> int:
        """Проверка здоровья сервера."""
        data = _api_get("/health")
        log.info(f"✅ Статус: {data['status']}")
        log.info(f"📦 Глубина очереди: {data.get('queue_depth', '?')}")
        log.info(f"📊 Всего задач: {data.get('jobs', '?')}")
        return 0

    def cmd_list(self) -> int:
        """Список задач (заглушка)."""
        log.info("⚠️  Эндпоинт /list пока не реализован на сервере.")
        log.info("   Используйте 'status <job_id>' для проверки конкретной задачи.")
        return 1

    def cmd_logs(self, job_id: str, lines: int = 20) -> int:
        """Логи задачи (заглушка)."""
        log.info(f"⚠️  Эндпоинт /logs/{job_id} пока не реализован на сервере.")
        log.info("   Логи появятся позже.")
        return 1

    # =================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =================================================================

    def _submit_job(self, task: str, prediction: dict) -> str:
        """Отправляет задачу на сервер и возвращает job_id."""
        payload = {
            "task": task,
            "gpu_required": prediction.get("gpu_required", False),
            "priority": 5,
            "execution_mode": "k8s_job"
        }
        result = _api_post("/submit", payload)
        return result.get("job_id")

    def _show_alternatives(self, task: str) -> None:
        explanation = self.explainer.explain(task)
        log.info("\n💡 АЛЬТЕРНАТИВЫ:")
        if explanation.get('alternatives'):
            for alt in explanation['alternatives']:
                log.info(f"  • {alt['description']} → ${alt['cost']:.2f} (экономия {alt['savings']}%)")
        else:
            log.info("  (дешёвых альтернатив не найдено)")

    def _format_duration(self, minutes: float) -> str:
        if not minutes:
            return "0m"
        h = int(minutes // 60)
        m = int(minutes % 60)
        return f"{h}h {m}m" if h else f"{m}m"

    def _breakdown_str(self, breakdown: dict) -> str:
        """Форматирует детализацию стоимости для вывода."""
        lines = []
        for k, v in breakdown.items():
            if isinstance(v, float):
                lines.append(f"  {k}: ${v:.2f}")
            elif isinstance(v, int):
                lines.append(f"  {k}: {v}")
            else:
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)


# =================================================================
# ТОЧКА ВХОДА
# =================================================================
def main():
    if len(sys.argv) < 2:
        log.info(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    # Второй аргумент (task или job_id) собираем из оставшихся аргументов
    args = sys.argv[2:]

    cli = ROMA_CLI()

    if cmd == "run":
        if not args:
            log.info("Использование: roma run 'описание задачи'")
            sys.exit(1)
        task = " ".join(args)
        sys.exit(cli.cmd_run(task))

    elif cmd == "explain":
        if not args:
            log.info("Использование: roma explain 'описание задачи'")
            sys.exit(1)
        task = " ".join(args)
        sys.exit(cli.cmd_explain(task))

    elif cmd == "cost":
        if not args:
            log.info("Использование: roma cost 'описание задачи'")
            sys.exit(1)
        task = " ".join(args)
        sys.exit(cli.cmd_cost(task))

    elif cmd == "status":
        job_id = args[0] if args else None
        sys.exit(cli.cmd_status(job_id))

    elif cmd == "health":
        sys.exit(cli.cmd_health())

    elif cmd == "list":
        sys.exit(cli.cmd_list())

    elif cmd == "logs":
        if not args:
            log.info("Использование: roma logs <job_id> [-n число]")
            sys.exit(1)
        job_id = args[0]
        lines = 20
        if "-n" in args:
            idx = args.index("-n")
            if idx + 1 < len(args):
                lines = int(args[idx + 1])
        sys.exit(cli.cmd_logs(job_id, lines))

    elif cmd == "dashboard":
        log.info("🚀 Дашборд: roma-dashboard.service на порту 8051")
        sys.exit(0)

    else:
        log.info(f"Неизвестная команда: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
loopcraft_demo.py
=================

Минимально жизнеспособная реализация автономного цикла в духе loopcraft.

Сценарий:
    Агент автономно улучшает гиперпараметр learning_rate для простой
    задачи «обучения». Реальный вызов LLM заменён детерминированной
    имитацией: агент предлагает новое значение lr с учётом истории.
    Внешняя среда запускает «обучение» (заглушка) и возвращает
    валидационную метрику val_loss. Цель — минимизировать val_loss.

Как код отражает принципы loopcraft (см. main()):
    1. ТРИГГЕР        — явный вызов main() (точка входа)
    2. НАВЫК          — класс Agent с generate_action(state)
    3. СРЕДА          — Environment.evaluate(lr) — детерминированный
                        ландшафт с шумом и известным минимумом
    4. ШЛЮЗ           — функция gate() — принимает только если новая
                        loss СТРОГО меньше лучшей известной
    5. STATE-ФАЙЛ     — JSON между запусками: принятые/отклонённые
                        попытки, лучший результат
    6. МЕТРИКА        — cost per accepted change (CPA)
    7. БЕЗОПАСНОСТЬ    — max_iterations, обработка исключений,
                        защита от бесконечного цикла

Запуск:
    python loopcraft_demo.py            # обычный режим
    python loopcraft_demo.py --verbose  # подробный лог
    python loopcraft_demo.py --reset    # сбросить state-файл
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------- #
# Конфигурация                                                                #
# --------------------------------------------------------------------------- #

STATE_FILE = Path(__file__).parent / "loopcraft_state.json"

# Ландшафт «обучения»: гладкая функция с минимумом в lr ≈ 0.01
# Добавлен гауссов шум — имитация нестабильности реального обучения
LANDSCAPE_OPTIMAL_LR = 0.01
LANDSCAPE_NOISE_STD = 0.05

# Границы поиска
LR_MIN, LR_MAX = 1e-5, 1.0

# Параметры цикла
DEFAULT_MAX_ITERATIONS = 60
TARGET_LOSS = 0.10  # порог «идеального» результата
GATE_TOLERANCE = 1e-4  # новая loss должна быть < best - tolerance

# Агент
AGENT_STEP_LOG_MEAN = 0.3  # средне-логарифмический шаг изменения lr
AGENT_EXPLORATION_RATE = 0.2  # вероятность случайного «прыжка»


# --------------------------------------------------------------------------- #
# Модели данных                                                               #
# --------------------------------------------------------------------------- #


@dataclass
class Attempt:
    """Одна попытка агента: какое lr он предложил, какой loss получил,
    было ли это принято шлюзом, и по какой причине."""

    iteration: int
    lr: float
    loss: float
    accepted: bool
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CycleState:
    """Полное состояние цикла, сериализуемое в JSON."""

    best_lr: float = 0.1
    best_loss: float = float("inf")
    attempts: list[dict[str, Any]] = field(default_factory=list)
    accepted_count: int = 0
    rejected_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# --------------------------------------------------------------------------- #
# Среда: «обучение»                                                           #
# --------------------------------------------------------------------------- #


class Environment:
    """Заглушка обучения. val_loss = f(lr) + шум.

    Ландшафт: чем дальше lr от оптимума (0.01), тем хуже loss.
    Используется лог-пространство, потому что lr — мультипликативный параметр.
    """

    def __init__(
        self, optimal_lr: float = LANDSCAPE_OPTIMAL_LR, noise_std: float = LANDSCAPE_NOISE_STD, seed: int | None = None
    ) -> None:
        self.optimal_lr = optimal_lr
        self.noise_std = noise_std
        self._rng = random.Random(seed)

    def evaluate(self, lr: float) -> float:
        """Запустить «обучение» и вернуть val_loss."""
        if lr <= 0:
            return float("inf")
        # Гладкая U-образная функция в лог-пространстве
        log_distance = math.log(lr / self.optimal_lr)
        loss = log_distance**2 + 0.05
        # Добавим гауссов шум (Box-Muller)
        noise = self._rng.gauss(0, self.noise_std)
        return max(0.0, loss + noise)


# --------------------------------------------------------------------------- #
# Агент: «предлагает» новое lr                                                #
# --------------------------------------------------------------------------- #


class Agent:
    """Имитация LLM-агента. Вместо реальной модели — детерминированная
    стратегия: случайный лог-нормальный сдвиг относительно лучшего lr,
    с эпизодической «эксплорацией» (большой прыжок в неизвестную область)."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def generate_action(self, state: CycleState) -> float:
        """Сгенерировать новое значение lr на основе истории."""
        # С вероятностью EXPLORATION_RATE — случайный «прыжок» в новую область
        if self._rng.random() < AGENT_EXPLORATION_RATE:
            return self._rng.uniform(LR_MIN, LR_MAX)

        # Иначе — локальная мутация вокруг лучшего известного lr
        log_best = math.log(state.best_lr)
        shift = self._rng.gauss(0, AGENT_STEP_LOG_MEAN)
        new_log = log_best + shift
        new_lr = math.exp(new_log)
        return max(LR_MIN, min(LR_MAX, new_lr))


# --------------------------------------------------------------------------- #
# Шлюз верификации                                                            #
# --------------------------------------------------------------------------- #


def gate(lr: float, loss: float, state: CycleState, verbose: bool = False) -> tuple[bool, str]:
    """Решение о принятии/отклонении попытки.

    Правила:
        1. loss должна быть КОНЕЧНОЙ (защита от NaN/inf)
        2. loss должна быть СТРОГО меньше best_loss - tolerance
        3. lr должна быть в допустимом диапазоне
    """
    if not math.isfinite(loss):
        reason = "rejected: non-finite loss"
        return False, reason

    if not (LR_MIN <= lr <= LR_MAX):
        reason = f"rejected: lr={lr:.6f} out of bounds [{LR_MIN}, {LR_MAX}]"
        return False, reason

    threshold = state.best_loss - GATE_TOLERANCE
    if loss < threshold:
        reason = f"accepted: loss {loss:.6f} < best {state.best_loss:.6f}"
        return True, reason
    else:
        reason = f"rejected: loss {loss:.6f} >= best {state.best_loss:.6f}"
        return False, reason


# --------------------------------------------------------------------------- #
# State-файл                                                                  #
# --------------------------------------------------------------------------- #


def save_state(state: CycleState) -> None:
    """Атомарная запись state-файла: write to .tmp → rename."""
    state.updated_at = datetime.now(timezone.utc).isoformat()
    tmp = STATE_FILE.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, indent=2, ensure_ascii=False)
        os.replace(tmp, STATE_FILE)
    except OSError as e:
        print(f"[WARN] failed to save state: {e}", file=sys.stderr)


def load_state() -> CycleState:
    """Загрузить состояние из файла, или создать новое."""
    if not STATE_FILE.exists():
        return CycleState()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # best_loss может быть inf — JSON не любит, обработаем отдельно
        if data.get("best_loss") in (None, "Infinity"):
            data["best_loss"] = float("inf")
        return CycleState(**data)
    except (OSError, json.JSONDecodeError, TypeError) as e:
        print(f"[WARN] state file corrupt, starting fresh: {e}", file=sys.stderr)
        return CycleState()


# --------------------------------------------------------------------------- #
# Главный цикл                                                                #
# --------------------------------------------------------------------------- #


def run_cycle(verbose: bool = False, max_iterations: int = DEFAULT_MAX_ITERATIONS) -> CycleState:
    """Один прогон loopcraft-цикла.

    Возвращает финальное состояние. Прерывания:
        - достигнут TARGET_LOSS  → ранняя остановка (успех)
        - исчерпан max_iterations → защита от бесконечного цикла
        - KeyboardInterrupt      → пользовательский отказ
        - исключение в Environment/Agent → ловим, логируем, продолжаем
    """
    state = load_state()
    env = Environment(seed=42)
    agent = Agent(seed=42)

    if verbose:
        print(f"[INIT] state loaded: best_lr={state.best_lr:.6f}, " f"best_loss={state.best_loss:.6f}")
        print(f"[INIT] target_loss={TARGET_LOSS}, max_iterations={max_iterations}")
        print("-" * 70)

    start_iter = len(state.attempts)
    converged = False

    try:
        for i in range(start_iter, start_iter + max_iterations):
            # ---- 1. Агент предлагает действие ----
            proposed_lr = agent.generate_action(state)

            # ---- 2. Среда исполняет и возвращает метрику ----
            try:
                loss = env.evaluate(proposed_lr)
            except Exception as e:
                if verbose:
                    print(f"[ITER {i:03d}] environment error: {e}")
                state.attempts.append(
                    Attempt(
                        iteration=i,
                        lr=proposed_lr,
                        loss=float("inf"),
                        accepted=False,
                        reason=f"rejected: env error: {e}",
                    ).__dict__
                )
                state.rejected_count += 1
                save_state(state)
                continue

            # ---- 3. Шлюз решает: принять или отклонить ----
            accepted, reason = gate(proposed_lr, loss, state, verbose=verbose)

            # ---- 4. Обновить state ----
            if accepted:
                state.best_lr = proposed_lr
                state.best_loss = loss
                state.accepted_count += 1
            else:
                state.rejected_count += 1

            state.attempts.append(
                Attempt(iteration=i, lr=proposed_lr, loss=loss, accepted=accepted, reason=reason).__dict__
            )

            # ---- 5. Сохранить state после КАЖДОЙ попытки (атомарно) ----
            save_state(state)

            # ---- 6. Лог ----
            if verbose:
                tag = "ACCEPT" if accepted else "REJECT"
                print(
                    f"[ITER {i:03d}] {tag} | lr={proposed_lr:.6f} "
                    f"loss={loss:.6f} | best_lr={state.best_lr:.6f} "
                    f"best_loss={state.best_loss:.6f}"
                )
                if accepted:
                    print(f"         reason: {reason}")

            # ---- 7. Проверка условия остановки ----
            if state.best_loss <= TARGET_LOSS:
                if verbose:
                    print("-" * 70)
                    print(f"[STOP] target loss {TARGET_LOSS} достигнут " f"(best_loss={state.best_loss:.6f})")
                converged = True
                break

    except KeyboardInterrupt:
        print("\n[INTERRUPT] пользователь прервал цикл, state сохранён")

    if verbose and not converged:
        print("-" * 70)
        print(f"[STOP] исчерпан лимит итераций ({max_iterations})")

    return state


# --------------------------------------------------------------------------- #
# Отчёт                                                                       #
# --------------------------------------------------------------------------- #


def print_report(state: CycleState) -> dict[str, Any]:
    """Вывести финальный отчёт и вернуть машинно-читаемую статистику."""
    total = state.accepted_count + state.rejected_count
    cpa = (total / state.accepted_count) if state.accepted_count else float("inf")
    acceptance_rate = state.accepted_count / total if total else 0.0
    accepted_attempts = [a for a in state.attempts if a.get("accepted")]
    first_loss = state.attempts[0]["loss"] if state.attempts else float("inf")
    improvement = (first_loss - state.best_loss) if first_loss != float("inf") else 0.0

    print()
    print("=" * 70)
    print("LOOPCRAFT CYCLE REPORT")
    print("=" * 70)
    print(f"State file:           {STATE_FILE}")
    print(f"Total attempts:       {total}")
    print(f"  accepted:           {state.accepted_count}")
    print(f"  rejected:           {state.rejected_count}")
    print(f"Acceptance rate:      {acceptance_rate:.1%}")
    print(f"Best lr:              {state.best_lr:.6f}")
    print(f"Best loss:            {state.best_loss:.6f}")
    print(f"Initial loss:         {first_loss:.6f}")
    print(f"Improvement:          {improvement:.6f}  ({improvement/first_loss*100:.1f}%)" if first_loss > 0 else "")
    print(f"Target loss:          {TARGET_LOSS}")
    print(f"Converged:            {'YES' if state.best_loss <= TARGET_LOSS else 'NO'}")
    print()
    print(f"Cost per accepted change (CPA):  {cpa:.2f} attempts per accepted")
    print(f"  (interpretation: каждая принятая правка стоила {cpa:.1f} попыток,")
    print(f"   из них {cpa-1:.1f} были отклонены шлюзом как не-улучшения)")
    print("=" * 70)

    if accepted_attempts:
        print()
        print("Accepted improvements (history of convergence):")
        for a in accepted_attempts:
            print(f"  iter {a['iteration']:3d}  " f"lr={a['lr']:.6f}  loss={a['loss']:.6f}  " f"-> {a['reason']}")

    return {
        "total_attempts": total,
        "accepted": state.accepted_count,
        "rejected": state.rejected_count,
        "acceptance_rate": acceptance_rate,
        "best_lr": state.best_lr,
        "best_loss": state.best_loss,
        "improvement": improvement,
        "cpa": cpa,
        "converged": state.best_loss <= TARGET_LOSS,
    }


# --------------------------------------------------------------------------- #
# Точка входа                                                                 #
# --------------------------------------------------------------------------- #


def main() -> int:
    """Точка входа. Демонстрирует все 7 принципов loopcraft:

    1. ТРИГГЕР        — argparse / явный вызов
    2. НАВЫК          — Agent.generate_action (изолированный)
    3. СРЕДА          — Environment.evaluate (детерминированный ландшафт)
    4. ШЛЮЗ           — gate() (единственный арбитр «принять/отклонить»)
    5. STATE-ФАЙЛ     — loopcraft_state.json (переживает рестарт)
    6. МЕТРИКА        — CPA в финальном отчёте
    7. БЕЗОПАСНОСТЬ    — max_iterations, try/except, KeyboardInterrupt
    """
    parser = argparse.ArgumentParser(description="Loopcraft demo: автономный цикл оптимизации learning_rate")
    parser.add_argument("--verbose", "-v", action="store_true", help="подробный лог каждой итерации")
    parser.add_argument("--reset", action="store_true", help="сбросить state-файл перед запуском")
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"макс. итераций (по умолчанию {DEFAULT_MAX_ITERATIONS})",
    )
    args = parser.parse_args()

    if args.reset and STATE_FILE.exists():
        STATE_FILE.unlink()
        print(f"[RESET] state file удалён: {STATE_FILE}")

    t0 = time.time()
    final_state = run_cycle(verbose=args.verbose, max_iterations=args.iterations)
    elapsed = time.time() - t0

    stats = print_report(final_state)
    print(f"\nElapsed: {elapsed:.2f}s")

    # Код возврата: 0 если сошлись, 1 если нет
    return 0 if stats["converged"] else 1


if __name__ == "__main__":
    sys.exit(main())

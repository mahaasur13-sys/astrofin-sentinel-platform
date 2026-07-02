import datetime
import os
import re
import subprocess
import sys

from openai import OpenAI

# ---------- Конфигурация ----------
MAX_RETRIES = 3
PROTECTED_FILES = {"docker-compose.yml", ".env", "core/tracing.py"}
AUDIT_LOG = "ralph_audit.log"
TICKETS_FILE = "docs/tickets.md"
PROGRESS_FILE = "progress.md"
INSTRUCTIONS_FILE = "RALPH_INSTRUCTIONS.md"


# ---------- Функции помощники ----------
def read_file(path):
    with open(path) as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def run(cmd, capture=True):
    return subprocess.run(cmd, shell=True, capture_output=capture, text=True)


def is_protected_file(filepath):
    """Проверяет, относится ли файл к защищённым.

    Поддерживает оба формата git diff --name-only:
    - basename для файлов в корне репо (`docker-compose.yml`)
    - относительный путь для вложенных (`core/tracing.py`)
    """
    return os.path.basename(filepath) in PROTECTED_FILES or filepath in PROTECTED_FILES


def check_protected_files_in_diff():
    """Возвращает True, если в рабочем дереве нет изменений защищённых файлов."""
    res = run("git diff --name-only")
    changed = res.stdout.strip().split("\n")
    for f in changed:
        if is_protected_file(f):
            return False
    return True


def log_audit(log_path, task, llm_response, status, error=None):
    """Дозаписывает запись в аудит-лог."""
    timestamp = datetime.datetime.now().isoformat()
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] ЗАДАЧА: {task}\n")
        f.write(f"СТАТУС: {status}\n")
        f.write(f"ОТВЕТ LLM: {llm_response[:500]}...\n")
        if error:
            f.write(f"ОШИБКА: {error}\n")
        f.write("---\n")


def run_checks():
    """Выполняет обязательные проверки: ruff, pytest с coverage, docker ps."""
    print("🔍 Ruff check...")
    ruff = run("ruff check orchestration/ agents/ core/ meta_rl/ trading/ web/")
    if ruff.returncode != 0:
        return False, ruff.stdout + "\n" + ruff.stderr
    print("✅ Ruff ok")

    print("🧪 Pytest + coverage...")
    test = run("pytest tests/ -v --cov=. --cov-fail-under=60")
    if test.returncode != 0:
        return False, test.stdout + "\n" + test.stderr
    print("✅ Tests ok")

    print("🐳 Docker health...")
    ps = run("docker compose ps --filter status=running")
    if "unhealthy" in ps.stdout.lower():
        return False, "Unhealthy containers detected:\n" + ps.stdout
    print("✅ All containers healthy")
    return True, "All checks passed"


# ---------- Основная логика агента ----------
def main():
    api_key = os.getenv("VSELM_API_KEY")
    if not api_key:
        print("❌ Переменная VSELM_API_KEY не установлена")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://api.vsellm.ru/v1")

    tickets = read_file(TICKETS_FILE)
    progress = read_file(PROGRESS_FILE)
    instructions = read_file(INSTRUCTIONS_FILE) if os.path.exists(INSTRUCTIONS_FILE) else ""

    # Ищем первую невыполненную задачу
    match = re.search(r"^- \[ \] (.+?)$", tickets, re.MULTILINE)
    if not match:
        print("✅ Все задачи выполнены!")
        sys.exit(0)
    task = match.group(1)
    print(f"🎯 Задача: {task}")

    # Проверяем, не трогает ли агент уже сейчас защищённые файлы (хотя до коммита ещё далеко)
    # Эта проверка будет также после выполнения LLM.
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n🔄 Попытка {attempt}/{MAX_RETRIES}")
        # Stash несохранённых изменений (создаём точку отката)
        stash_cmd = f"git stash push -m 'ralph-attempt-{attempt}'"
        stash_res = run(stash_cmd)
        if stash_res.returncode != 0:
            log_audit(AUDIT_LOG, task, "N/A", "STASH_FAILED", error=stash_res.stderr)
            print("❌ Не удалось создать stash, прерываем.")
            sys.exit(1)

        # Формируем запрос к LLM
        prompt = f"""{instructions}

Сейчас ты выполняешь задачу:
"{task}"

Содержимое docs/tickets.md:
{tickets}

Содержимое progress.md:
{progress}

Выполни эту задачу: напиши код, тесты, обнови документацию.
После завершения выведи краткий отчёт и список изменённых файлов.
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            log_audit(AUDIT_LOG, task, "LLM_ERROR", "ERROR", error=str(e))
            print(f"❌ Ошибка LLM: {e}")
            sys.exit(1)

        print(f"🤖 Ответ модели:\n{answer}")
        log_audit(AUDIT_LOG, task, answer, "LLM_DONE")

        # Проверяем, не трогает ли агент защищённые файлы
        if not check_protected_files_in_diff():
            print("🛑 Обнаружены изменения в защищённых файлах! Откатываем.")
            run("git checkout -- .")  # откат изменений
            run("git stash pop")  # возвращаем исходное состояние
            print("Задача не выполнена из-за нарушения защиты.")
            sys.exit(1)

        # Запускаем проверки
        ok, msg = run_checks()
        if ok:
            print("✅ Все проверки пройдены, коммитим.")
            run("git add -A")
            run(f'git commit -m "feat: {task}"')
            # Обновляем tickets и progress
            tickets_updated = tickets.replace(f"- [ ] {task}", f"- [x] {task} ✅")
            write_file(TICKETS_FILE, tickets_updated)
            entry = f"\n## {task}\n- Статус: выполнено\n- Коммит: последний\n"
            with open(PROGRESS_FILE, "a") as pf:
                pf.write(entry)
            # Сливаем stash (он больше не нужен)
            run("git stash pop")
            print("📌 Прогресс обновлён.")
            log_audit(AUDIT_LOG, task, answer, "SUCCESS")
            break
        else:
            # Откатываем изменения и пробуем снова
            print(f"❌ Проверки не пройдены:\n{msg}")
            run("git checkout -- .")
            run("git stash pop")
            log_audit(AUDIT_LOG, task, answer, "CHECK_FAILED", error=msg)
            if attempt == MAX_RETRIES:
                print("⛔ Исчерпаны все попытки.")
                with open(PROGRESS_FILE, "a") as pf:
                    pf.write(
                        f"\n## {task}\n- Статус: BLOCKED\n- Причина: не прошла проверки после {MAX_RETRIES} попыток\n"
                    )
                sys.exit(1)
    else:
        print("Задача не выполнена.")


if __name__ == "__main__":
    main()

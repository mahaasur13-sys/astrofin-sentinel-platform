# Руководство по установке ATOM Federation OS

> Для новичков. Установка с нуля за 5 минут.

---

## Шаг 1 — Проверка системы

Открой терминал и выполни:

```bash
python3 --version
git --version
```

**Ожидаемый результат:**
```
Python 3.10+ (например, 3.12.3)
git version 2.XX.X
```

Если Python младше 3.10 — [установи Python 3.12](https://www.python.org/downloads/).

---

## Шаг 2 — Клонирование репозитория

```bash
cd ~                          # переходим в домашнюю папку
git clone https://github.com/mahaasur13-sys/atom-federation-os.git
cd atom-federation-os
```

---

## Шаг 3 — Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Важно:** `.venv` — локальное окружение проекта. Не используй `sudo` и не устанавливай пакеты глобально.

После активации в начале строки терминала появится `(.venv)`.

---

## Шаг 4 — Установка проекта

```bash
pip install -e .
```

Это установит:
- Все зависимости проекта (Python-библиотеки)
- CLI-команду `sbs` ( Typer + Rich)
- Все найденные пакеты: `sbs`, `alignment`, `core`, `federation` и другие

---

## Шаг 5 — Проверка установки

```bash
sbs doctor
```

**Ожидаемый результат:**
```
┌─────────────────────────────────┬──────┬────...
│ ✅ Python version               │ pass │ 3.12.3
│ ✅ SBS core                     │ pass │
│ ✅ CLI (Typer)                  │ pass │
│ ...
└─────────────────────────────────┴──────┴────...
Overall: PASS
```

Если видишь `ModuleNotFoundError: No module named 'typer'` — обнови pip и переустанови:

```bash
pip install --upgrade pip
pip install -e .
```

---

## Шаг 6 — Запуск тестов (опционально)

```bash
pip install -e ".[dev]"
pytest alignment/ -v
```

---

## Команды SBS

| Команда | Что делает |
|---------|------------|
| `sbs doctor` | Проверить окружение |
| `sbs verify` | Верифицировать инварианты |
| `sbs status` | Статус运行时 |
| `sbs replay --list` | Список сценариев отказа |
| `sbs replay <id>` | Воспроизвести сценарий |

---

## Если что-то пошло не так

### Ошибка: `command not found: sbs`
```bash
source .venv/bin/activate
sbs doctor
```

### Ошибка: `No module named 'typer'`
```bash
pip install --upgrade pip
pip install -e .
```

### Запутался в окружениях
```bash
deactivate                    # выйти из venv
rm -rf .venv                 # удалить всё
python3 -m venv .venv       # создать заново
source .venv/bin/activate
pip install -e .
```

---

## Структура проекта

```
atom-federation-os/
├── sbs/               # SBS Runtime (CLI, верификация)
├── alignment/         # Failure Replay, инварианты
├── core/              # DRL, CCL, F2/F3/F8
├── federation/       # Federation sync
├── orchestration/     # Планировщик, DAG
├── chaos/             # Хаос-движок
├── kubernetes/        # K8s operator, ROMA bridge
└── pyproject.toml     # Зависимости
```

---

## Быстрый старт (итог)

```bash
git clone https://github.com/mahaasur13-sys/atom-federation-os.git
cd atom-federation-os
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
sbs doctor
```

**Готово.** `sbs doctor` → `Overall: PASS`.

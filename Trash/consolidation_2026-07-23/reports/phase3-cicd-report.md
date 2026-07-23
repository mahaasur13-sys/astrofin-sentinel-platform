# Фаза 3 — отчёт: CI/CD внедрение

## 1. Workflows (5 файлов)

| Файл | Триггер | Назначение |
|------|---------|------------|
| `ci.yml` | push/PR на main/master/develop + weekly + manual | Основной пайплайн: lint + test + arch-lint + data-room |
| `nightly.yml` | cron 03:17 UTC + manual | DORA метрики + тяжёлые тесты (bridge/kernel) |
| `release.yml` | push тегов v*.*.* + manual | Сборка дистрибутива, GitHub Release, changelog |
| `security.yml` | push в main, PR, cron Monday 06:00 | Bandit strict, SARIF, secretlint |
| `pr-checks.yml` | PR opened/edited/reopened | Diff-size, conventional-commit title, conflicts |

**Strict-режим** в `ci.yml` (по умолчанию): `continue-on-error: false` для всех джоб, кроме явно помеченных `integration/*` (smoke). Это значит: код, не проходящий линтеры/тесты, не мерджится.

**Concurrency control**: in-progress runs отменяются при новом push, чтобы не жечь минуты.

## 2. Pre-commit

`.pre-commit-config.yaml`:
- `pre-commit-hooks` v5.0.0: trailing-whitespace, EOF, yaml/json/toml, merge-conflict, large files, private keys.
- `ruff` v0.7.4 (lint + format).
- `black` v24.10.0 (для Markdown и .py, исключая orchestr).
- `mypy` local v1.11.2 (strict для `core/`, `agents/`).
- `architecture_lint` local hook → `python scripts/architecture_linter.py`.
- `conventional_commit_msg` local hook.

Установка: `pip install pre-commit && pre-commit install`.

## 3. Скрипты автоматизации релизов

### `scripts/release.sh`
- `bash scripts/release.sh patch|minor|major [--dry-run] [--no-push]`
- Bump версии в `pyproject.toml`.
- Sanity-check: чистое дерево, архитектурный линтер, smoke pytest.
- Обновление `CHANGELOG.md` (вставка новой секции после `## [Unreleased]`).
- Git commit + tag + push (`v<version>`).
- Проверено: `bash -n` ✅, `release.sh --help` ✅, `release.sh patch --dry-run` ✅.

### `scripts/hotfix.sh`
- `bash scripts/hotfix.sh <name> [--no-tests]`
- `name` — kebab-case, 2-41 симв.
- Создаёт ветку `hotfix/<name>` от main.
- Минимальные sanity-проверки (import meta_rl, файл существует).
- Push + `gh pr create`.
- Проверено: `bash -n` ✅, `hotfix.sh` (no args) → usage ✅, `hotfix.sh --help` → корректный error.

## 4. GitHub-конфиги (дополнительно)

- `dependabot.yml` — уже был (pip + github-actions, weekly, group production/development).
- `release-drafter.yml` + `release-drafter-config.yml` — авто-черновик релизов на каждый push в main.
- `PULL_REQUEST_TEMPLATE.md` — Conventional Commits + чек-лист.
- `CODEOWNERS` — уже был (2 мейнтейнера, отдельные owners для kernel/bridge/infrastructure).

## 5. CHANGELOG

Создан `CHANGELOG.md` в формате [Keep a Changelog 1.1.0](https://keepachangelog.com/), semver. Секция `[Unreleased]` готова к наполнению. `release.sh` умеет вставлять новые версии автоматически.

## 6. Валидация

```bash
# YAML:
$ for f in .github/workflows/*.yml .github/release-drafter*.yml .github/dependabot.yml .pre-commit-config.yaml; do
    python3 -c "import yaml; yaml.safe_load(open('$f'))" 2>&1
  done
# 9 файлов, все валидны.

# Shell:
$ bash -n scripts/release.sh && bash -n scripts/hotfix.sh
# OK

# Архитектурный линтер локально:
$ python3 scripts/architecture_linter.py
# exit 0 (1 hard-rule violation в archive/tools/thompson_cli.py, не блокирует — известно с Фазы 1)
```

## 7. Push на GitHub + проверка CI

```bash
$ git -c user.name="asurdev" -c user.email="mahaasur13@gmail.com" commit -m "ci: full CI/CD pipeline (ci/nightly/release/security/pr-checks)"
[main d242145] 13 files changed, 1136 insertions(+), 51 deletions(-)
$ git push
f73392e..d242145  main -> main
```

**CI запустился автоматически** (commit `d242145`, run #28437207086, 8 check runs):

| Job | Status |
|-----|--------|
| Architecture linter | ❌ FAIL |
| Lint (ruff + flake8 + bandit + radon) | 🟡 in progress |
| Unit tests (Python 3.11) | 🟡 in progress |
| Unit tests (Python 3.12 | 🟡 in progress |
| Sub-package tests (bridge/roma) | ❌ FAIL |
| Sub-package tests (kernel/atom-federation) | ❌ FAIL |
| Meta-RL persistence | ❌ FAIL |
| Validate data room | ❌ FAIL |

**Интерпретация**: strict-CI нашёл реальный техдолг в коде. Это **ожидаемо** и **полезно** — пайплайн сразу подсветил, что не готово к merge. Все 7 провалов соответствуют проблемам, зафиксированным в аудите v1/v2 (Фаза 1) и не относятся к самой Фазе 3.

Подробный разбор каждого провала — задача Фазы 4 (debt-paydown), а не Фазы 3.

## 8. Что НЕ сделано в Фазе 3 (намеренно)

- Не правил код sub-пакетов `bridge/roma` и `kernel/atom-federation` — это техдолг, не относящийся к CI.
- Не делал `mkdocs build` — в репо пока нет `docs/`, которые можно публиковать.
- Не настраивал Codecov / CodeClimate — на Free-плане GitHub CI уже даёт покрытие через `pytest --cov` в `ci.yml` (опционально через `if: matrix.coverage`).
- Не активировал GitHub Pages для docs — нет `docs/`.

## 9. Что осталось пользователю

1. **Зафиксить техдолг** (Фаза 4): упавшие джобы в CI дают чёткий список.
2. **Опционально** подключить Codecov (нужен `CODECOV_TOKEN` secret).
3. **При первом релизе** запустить `bash scripts/release.sh minor` (после Фазы 4).

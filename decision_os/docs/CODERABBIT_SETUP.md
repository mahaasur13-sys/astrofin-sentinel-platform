# CodeRabbit.ai — Настройка авто-ревью для DecisionOS и ROMA Execution Bridge

## Что такое CodeRabbit

CodeRabbit — AI-инструмент автоматического code review. Работает как **нативный GitHub App** (не GitHub Actions). Ревьюит каждый Pull Request: inline-комментарии, high-level summary, sequence diagrams. Может предлагать и генерировать исправления.

**Бесплатно** для публичных репозиториев. Вход через GitHub — никаких карт.

---

## Шаг 1: Установка GitHub App

1. Зайди на [https://app.coderabbit.ai](https://app.coderabbit.ai)
2. Нажми **«Sign in with GitHub»**
3. Авторизуй приложение
4. Нажми **«Add Repositories»** → **«Install GitHub App»**
5. Выбери организацию или личный аккаунт (`mahaasur13-sys`)
6. Выбери доступ:
   - **All repositories** — если хочешь авто-ревью на все текущие и будущие репозитории
   - **Only select repositories** — выбери конкретные:
     - `mahaasur13-sys/astrofin-sentinel-platform` (AstroFin + DecisionOS)
     - `mahaasur13-sys/roma-execution-bridge` (ROMA Execution Bridge)
7. Нажми **«Install & Authorize»**

### Права, которые запрашивает App

| Право | Уровень | Зачем |
|-------|---------|-------|
| Contents | Read/Write | Чтение кода, предложение исправлений |
| Pull requests | Read/Write | Комментирование в PR |
| Issues | Read/Write | Создание issue при обнаружении багов |
| Checks | Read | Интеграция с Check Runs |
| Metadata | Read | Доступ к метаданным репозитория |

---

## Шаг 2: Проверка работы

1. Создай **тестовый Pull Request** (любой небольшой фикс — например, добавить комментарий в README)
2. Через **1–3 минуты** `@coderabbitai` должен оставить:
   - **High-level summary** — обзор изменений «на человеческом языке»
   - **Detailed review** — построчный разбор
   - **Inline-комментарии** — прямо в коде
3. Проверь вкладку **«Files changed»** в PR — комментарии CodeRabbit будут видны там же

### Что проверять после установки

- [ ] PR открыт → появился комментарий от `@coderabbitai`
- [ ] Summary релевантен содержанию PR
- [ ] Inline-комментарии указывают на реальные проблемы (а не ложные срабатывания)
- [ ] Последовательные диаграммы (`sequence_diagrams: true`) генерируются для изменений в плагинах

---

## Шаг 3: Конфигурация через `.coderabbit.yaml`

### DecisionOS (в `astrofin-sentinel-platform`)

Конфиг: **[`.coderabbit.yaml`](../../.coderabbit.yaml)** (корень репозитория)

```yaml
language: ru-RU
reviews:
  profile: ASSERTIVE
  request_changes_workflow: true
  collapse_walkthrough: false
  sequence_diagrams: true
  changed_files_summary: true

path_instructions:
  - path: "decision_os/core/**"
    instructions: "КРИТИЧНО: PluginManager, HookSystem, Sandbox. SPEND_KEY блокировка."
  - path: "decision_os/plugins/dashbeam_transfer/**"
    instructions: "КРИТИЧНО: DashBeam P2P. Spend keys Monero НИКОГДА в коде."
  - path: "decision_os/tests/**"
    instructions: "58/58 должны проходить. Граничные случаи: unload, re-install."
```

### ROMA Execution Bridge

Конфиг: **[`.coderabbit.yaml`](https://github.com/mahaasur13-sys/roma-execution-bridge/blob/feature/api-docs-improvements/.coderabbit.yaml)**

```yaml
language: ru-RU
reviews:
  profile: assertive
  request_changes_workflow: false

path_instructions:
  - path: "plugins/core/**"
    instructions: "Потокобезопасность (asyncio.Lock), lifecycle, dependency resolution."
  - path: "plugins/dashbeam/**"
    instructions: "MoneroSharingValidator, IrohAdapter, ticket lifecycle."
  - path: "billing/**"
    instructions: "Stripe + CloudPayments. Идемпотентность webhook, без CVV/PAN."
  - path: "ha/**"
    instructions: "Raft consensus. Корректность term/log индексов."
```

---

## Шаг 4: Профили ревью

| Профиль | Поведение |
|---------|-----------|
| `chill` | Мягкие рекомендации, без блокировки merge |
| `assertive` | **Рекомендовано для DecisionOS/ROMA.** Уверенные замечания, флагит потенциальные баги |
| `assertive+` | Максимально строгий — блокирует merge при критических проблемах |

**Для production-кода используй `assertive` или `assertive+`.**

---

## Шаг 5: Что проверяет CodeRabbit в DecisionOS/ROMA

### 🔒 Безопасность (критично)

- **Spend keys Monero** — никогда в коде, логах, тестовых данных
- **API keys / secrets** — отсутствие хардкода
- **Crypto private keys** — валидация `MoneroSharingValidator.FORBIDDEN_KEYS`

### 🧩 Плагинная архитектура

- **Lifecycle**: register → load → enable → disable → unload — все 8 состояний
- **Sandbox**: whitelist permissions, tier-gating (Start/Pro/Enterprise)
- **Manifest**: PluginManifest соответствует реализации, semver валидация
- **Hooks**: корректность register/fire/unregister

### 📡 DashBeam Transfer

- Ticket lifecycle: CREATED → PENDING → ACCEPTED → TRANSFERRING → COMPLETED
- IrohAdapter: QUIC + TLS 1.3 handshake
- Enterprise relay: токены не логируются
- Wallet sharing: только view-only данные Monero

### 🧪 Тесты

- DecisionOS: **58/58 должны проходить** (18 unit + 40 integration)
- ROMA: all plugin tests green
- Граничные случаи: None, пустые списки, таймауты, re-install

---

## Шаг 6: Интерактивное общение с CodeRabbit

CodeRabbit понимает команды прямо в PR-комментариях:

```
@coderabbitai generate unit tests for this function
@coderabbitai generate docstrings
@coderabbitai resolve this thread
@coderabbitai explain this code
@coderabbitai ignore this issue
```

---

## Часто задаваемые вопросы

### Q: CodeRabbit заменяет human review?

**Нет.** CodeRabbit — дополнительный слой, не замена. Он ловит баги паттернов (пропущенные проверки spend_key, нарушение sandbox), но архитектурные решения должен принимать человек.

### Q: Сколько стоит?

**Бесплатно** для публичных репозиториев (Open Source). Для приватных — бесплатный trial 14 дней, затем Pro план.

### Q: Что если CodeRabbit даёт ложные срабатывания?

Добавь `@coderabbitai ignore` в комментарий. Для систематических проблем — настрой `path_filters` в `.coderabbit.yaml` (исключи определённые пути).

### Q: Как обновить конфиг?

1. Отредактируй `.coderabbit.yaml` в корне репозитория
2. Сделай commit и push
3. CodeRabbit перечитает конфиг при следующем PR

### Q: CodeRabbit работает на feature-ветках?

Да. По умолчанию ревьюит все PR независимо от целевой ветки. Настрой `auto_review.base_branches` чтобы ограничить.

---

## Ссылки

- [CodeRabbit Dashboard](https://app.coderabbit.ai)
- [Документация CodeRabbit](https://docs.coderabbit.ai)
- [`.coderabbit.yaml` референс](https://docs.coderabbit.ai/guides/configure-coderabbit)
- [CodeRabbit Pro](https://coderabbit.ai/pricing)

---

> **Последнее обновление:** 2026-08-20
> **Автор:** DecisionOS Team
> **Статус:** ✅ Конфиги актуальны для DecisionOS v1.0.0 и ROMA Execution Bridge v1.1.0

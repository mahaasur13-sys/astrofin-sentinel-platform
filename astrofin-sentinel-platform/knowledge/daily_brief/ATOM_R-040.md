# ATOM-R-040: Интеграция ежедневного агента в рабочий процесс

**Тип:** Enhancement (R-серия)
**Приоритет:** P1
**Статус:** ✅ Implemented
**Дата:** 2026-03-29
**Sprint:** R-04x

---

## Цель

Сделать внешний email-агент (ежедневная сводка multi-agent новостей) частью внутренней петли улучшения AstroFinSentinelV5 через автоматический парсинг и генерацию ATOM-идей.

---

## Реализация

### 1. Папка `knowledge/daily_brief/`

```
knowledge/daily_brief/
├── README.md           ← документация
├── ATOM_R-040.md      ← эта карточка
├── daily_brief.py      ← CLI-парсер + генератор идей
└── brief_YYYY-MM-DD.md ← сводки (одна на день)
```

### 2. CLI-команда `python tools/thompson_cli.py daily-brief`

Добавлена как subcommand в `thompson_cli.py`:

```bash
# Показать последнюю сводку
python tools/thompson_cli.py daily-brief

# Список всех сводок
python tools/thompson_cli.py daily-brief --list

# Сгенерировать ATOM-идеи
python tools/thompson_cli.py daily-brief --ideas

# Сохранить новую сводку (для webhook/email integration)
python tools/thompson_cli.py daily-brief --save "content"

# Garbage collection старых сводок
python tools/thompson_cli.py daily-brief --gc
```

### 3. Генерация ATOM-идей

При парсинге сводки автоматически:

| Паттерн в сводке | Категория идеи | Действие |
|-----------------|----------------|----------|
| GitHub/tool release | `TOOL_ADOPTION` | Проверить совместимость с архитектурой |
| arXiv/research | `RESEARCH_INTEGRATION` | Оценить для reward function / новых фичей |
| Community discussion | `COMMUNITY_SENTIMENT` | Найти проблемы пользователей для новых ATOM |

---

## Будущие расширения (R-040-FUTURE)

- [ ] **Email webhook**: принимать сводки напрямую на email → сохранять без ручного --save
- [ ] **RSS integration**: парсить RSS ленты GitHub/arxiv
- [ ] **Автоматический ATOM creation**: генерация ATOM-карточек из идей одним кликом
- [ ] **Telegram integration**: отправлять краткую выжимку в Telegram после обработки сводки

---

## Зависимости

- R-039 (ежедневный email-агент) — создаёт исходные сводки
- ATOM-KARL back-end — куда добавляются сгенерированные идеи

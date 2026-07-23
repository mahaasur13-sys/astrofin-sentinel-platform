# ATOM-R-041: Idea → Outcome Tracking

**Статус:** ✅ Реализовано
**Приоритет:** P0 — Критически важно
**Дата:** 2026-03-29

---

## Цель

Превратить генерацию идей в измеримую систему с полным жизненным циклом и обратной связью.

## Жизненный цикл

```
proposed → scored → injected → tested → accepted/rejected
     ↓
   rejected (low score)
```

## Структура данных

```python
Idea {
    id: str              # "IDEA-XXXXXXXX"
    source: str          # "daily_brief", "manual", "telegram"
    text: str            # Описание идеи
    category: str        # "TOOL_ADOPTION", "RESEARCH_INTEGRATION", etc.
    status: str          # proposed|scored|injected|tested|accepted|rejected
    score: float         # Quality filter score
    linked_trajectories: list  # Связанные траектории KARL
    impact_score: float  # Средний reward из траекторий
    created_at: str      # ISO timestamp
    tested_at: str       # Когда запущен тест
    evaluated_at: str    # Когда получена оценка
}
```

## Scoring Formula

```python
def score_idea(text):
    score = 0.0

    # Positive signals
    +1.5  model, architecture, algorithm
    +1.2  performance, optimization, efficiency
    +1.0  API, integration, reward, policy
    +0.8  tool, framework, library, agent, trajectory

    # Negative signals
    -1.0  marketing, social media
    -0.5  community, reddit, hacker news
    -0.5  vague, generic
```

Threshold: **0.5** — ниже отфильтровываются

## KPI

| Metric | Description |
|--------|-------------|
| `ideas_total` | Всего идей |
| `ideas_scored` | Прошли quality filter |
| `ideas_injected` | Добавлены в KARL buffer |
| `ideas_tested` | Проверены траекториями |
| `ideas_accepted` | Положительный impact |
| `ideas_rejected` | Отрицательный/нулевой impact |
| `impact_mean` | Средний reward по принятым |
| `acceptance_rate` | Доля принятых от проверенных |

## Интеграция в KARL

### inject_idea()
```python
def inject_idea(idea_id, trajectory_id=None):
    idea.status = "injected"
    if trajectory_id:
        idea.linked_trajectories.append(trajectory_id)
    # buffer.add_trajectory(traj) — траектория создаётся
    mark_tested(idea_id, [trajectory_id])
```

### evaluate_idea()
```python
def evaluate_idea(idea_id, reward):
    idea.impact_score = reward
    idea.status = "accepted" if reward > 0 else "rejected"
```

## Self-Questioning Integration

```python
def generate_questions():
    internal = self_questioning_templates()
    external = load_daily_brief_ideas()

    return internal + [
        f"Can this improve system performance? {idea['text']}"
        for idea in external if idea['score'] > 0.5
    ]
```

## Файлы

- `knowledge/daily_brief/idea_tracker.py` — основной модуль
- `knowledge/daily_brief/ideas.jsonl` — хранилище идей
- `knowledge/daily_brief/ATOM_R-041.md` — эта карточка

## CLI

```bash
# Список идей
python tools/thompson_cli.py daily-brief --ideas

# Добавить идею
python knowledge/daily_brief/idea_tracker.py --add "Test new volatility model" --source manual

# Показать KPI
python knowledge/daily_brief/idea_tracker.py --kpi

# Внедрить в KARL
python knowledge/daily_brief/idea_tracker.py --inject IDEA-XXXXXXXX

# Оценить после backtest
python knowledge/daily_brief/idea_tracker.py --eval IDEA-XXXXXXXX --reward 0.15
```

## Следующие шаги

- [ ] **RAG Integration**: FAISS/Chroma для semantic search по идеям
- [ ] **Policy Shaping**: accepted ideas → bias в policy
- [ ] **Telegram Decision Surface**: human-in-the-loop feedback
- [ ] **Автоматический ATOM creation**: high-score ideas → ATOM cards

# 🚀 Sprint Kickoff Template

> **Копировать в новый файл `SPRINT_X_KICKOFF_<date>.md` в начале каждого спринта.**
> **Использовать как checklist для синхронизации команды в первый день (Пн 09:00).**

---

## 📋 Sprint Metadata

- **Sprint Number:** _\_ (например, Sprint 6)
- **Sprint Window:** <YYYY-MM-DD> (Mon) → <YYYY-MM-DD> (Sun)
- **Sprint Goal:** _\_ (1-2 предложения)
- **Capacity:** _\_ ч (1 FTE = 80 ч, 1.5 FTE = 120 ч)
- **Sprint Plan Reference:** `docs/sprints/SPRINT_X.md`
- **Predecessor Sprint:** Sprint _\_ (что закрыли, что carry-over)

---

## ✅ Pre-flight Checklist (Пн 09:00, перед standup)

### Окружение
- [ ] `gh auth status` — logged in
- [ ] `git status` — clean, on правильной ветке (`release/1.0.0` или `main`)
- [ ] `git pull origin <branch>` — последние изменения
- [ ] `workon astrofin` (или `source venv/bin/activate`) — venv активирован
- [ ] `pytest -q tests/ | tail -1` — pass rate из предыдущего спринта зафиксирован
- [ ] `ruff check` — 0 errors
- [ ] `bandit -r core/ orchestration/ web/ | tail -1` — без новых high

### Документация
- [ ] Прочитан `SPRINT_X.md` целиком
- [ ] Прочитан `MOSCOW_PRIORITIZATION.md` (если были изменения)
- [ ] Прочитан предыдущий `SPRINT_X-1_RETRO.md` (если есть)
- [ ] Carry-over из предыдущего спринта — добавлен в новый milestone

### GitHub
- [ ] `gh issue list --milestone "Sprint X-1" --state closed | wc -l` — velocity предыдущего
- [ ] `gh api repos/<owner>/<repo>/milestones` — новый milestone создан
- [ ] Issues для нового спринта созданы (по `SPRINT_X_ISSUES.md` если есть)
- [ ] Labels проставлены (`priority:critical`, `sprint:X`, `owner:<name>`)
- [ ] Assignees назначены

### Коммуникация
- [ ] Slack/email уведомление команде: "Sprint X starts"
- [ ] Calendar invite для Sprint Planning (если не было)
- [ ] Calendar invites для daily standup (Пн–Пт 09:30, 15 мин)

---

## 📊 Carry-over из предыдущего спринта

> Скопировать из `SPRINT_X-1_RETRO.md`. Если carry-over = 0 — написать "None".

```
Sprint X-1 Carry-over
═══════════════════════════════════════════════
□ <TASK-ID>: <Task title> (Owner: <name>, Original estimate: <h>, Why carry-over: <reason>)
□ <TASK-ID>: <Task title> (Owner: <name>, Original estimate: <h>, Why carry-over: <reason>)
□ ...
═══════════════════════════════════════════════
Total carry-over: __/__
Total carry-over hours: __/__
```

**Decision по carry-over:**
- [ ] Все carry-over добавлены в Sprint X milestone
- [ ] Если carry-over > 2 critical задач — уменьшить Sprint X scope
- [ ] Если carry-over = 0 — добавить X+1 preview задач в Sprint X

---

## 🎯 Sprint Goal в 3 измеримых результатах

> Скопировать из `SPRINT_X.md` раздел "Sprint Goal".

1. **_<Result 1>_:**
2. **_<Result 2>_:**
3. **_<Result 3>_:_

**Метрика успеха #1 (измеримая):** _\_
**Метрика успеха #2 (измеримая):** _\_
**Метрика успеха #3 (измеримая):** _\_

---

## 📅 Дневной план (1 FTE baseline)

> Скопировать из `SPRINT_X.md` раздел "Дневной план". Кратко — по 1 строке на день.

| День | Фокус | Часы запланировано |
|------|-------|------------------:|
| Пн | _\ | _\ |
| Вт | _\ | _\ |
| Ср | _\ | _\ |
| Чт | _\ | _\ |
| Пт | _\ | _\ |
| **Итого** | | **_\** |

---

## 👥 Распределение задач (assignees)

| Task ID | Title | Owner | Estimate (h) | Priority | Status |
|---------|-------|-------|-------------:|----------|--------|
| _\_ | _\ | _\ | _\ | 🟥/🟧/🟨/🟦 | 📋 Todo |
| _\ | _\ | _\ | _\ | 🟥/🟧/🟨/🟦 | 📋 Todo |
| _\ | _\ | _\ | _\ | 🟥/🟧/🟨/🟦 | 📋 Todo |
| ... | ... | ... | ... | ... | ... |

**Total tasks:** _\_
**Total hours:** _\_ / _\_ (capacity)
**Utilization:** _\_%

---

## ⚠️ Top-3 риска спринта

> Скопировать из `SPRINT_X.md` раздел "Риски", топ-3.

| # | Риск | Вероятность | Импакт | Mitigation | Owner |
|---|------|------------:|-------:|------------|-------|
| 1 | _\ | 🟧 Средняя | 🟥 High | _\ | _\ |
| 2 | _\ | 🟧 Средняя | 🟧 High | _\ | _\ |
| 3 | _\ | 🟨 Низкая | 🟧 Medium | _\ | _\ |

**Monitoring frequency:** daily standup (Пн–Пт 09:30)

---

## 🤝 Ceremonies (расписание)

| Событие | Дата/время | Участники | Длительность | Notes |
|---------|------------|-----------|-------------:|-------|
| **Sprint Planning** | _\ | Вся команда | 1 ч | _\ |
| **Daily Standup** | Пн–Пт 09:30 | Backend + DevOps | 15 мин | Zoom/Slack huddle |
| **Mid-sprint Check** | Ср 14:00 | Backend + DevOps | 30 мин | Burndown review |
| **Sprint Review** | Пт _\ 16:00 | + Stakeholders | 1 ч | Demo |
| **Sprint Retro** | Пт _\ 17:00 | Вся команда | 1 ч | Что улучшить |
| **Sprint X+1 Planning** | Пт _\ 18:00 | Вся команда | 1 ч | Следующий sprint |

---

## 📊 Метрики успеха (KPI)

> Скопировать из `SPRINT_X.md` раздел "Метрики успеха".

| Метрика | Цель | Baseline (пред. спринт) | Как измерить |
|---------|------|------------------------:|--------------|
| Sprint commit | _\_% | _\_% | `gh issue list --milestone "Sprint X" --state closed` |
| Carry-over | _\_ | _\_ | Standup Пн |
| New critical bugs | 0 | _\_ | `gh issue list --label critical --state open` |
| `pytest` pass rate | _\_% | _\_% | `pytest -q tests/ \| tail -1` |
| Coverage | _\_% | _\_% | `coverage report` |
| Security scan | _\_ | _\_ | CI artifacts |
| _\ | _\ | _\ | _\ |

---

## 🔗 Связанные документы

- **Sprint plan:** `docs/sprints/SPRINT_X.md`
- **Sprint issues (готовые):** `docs/sprints/SPRINT_X_ISSUES.md` (если есть)
- **Predecessor sprint:** `docs/sprints/SPRINT_X-1.md`
- **Predecessor retro:** `docs/sprints/SPRINT_X-1_RETRO.md`
- **Backlog:** `PRODUCTION_BACKLOG.md`
- **MoSCoW:** `MOSCOW_PRIORITIZATION.md`
- **Release plan:** `RELEASE_PLAN_v1.0.0.md`

---

## 📝 Заметки первого дня

> Заполнять во время standup и в течение дня.

```
Sprint X — Day 1 Notes (Mon <date>)
═══════════════════════════════════════════════
□ Standup attended: Y/N
□ All team members have dev environment working: Y/N
□ Blocker discovered: <описание> (Owner: <name>, ETA: <date>)
□ Scope change needed: Y/N (если Y — обсудить на mid-sprint check)
□ Carry-over addition needed: Y/N
═══════════════════════════════════════════════
```

---

## 🚀 Готовность к старту (финальная)

- [ ] Pre-flight checklist complete
- [ ] Carry-over добавлен
- [ ] Sprint Goal понятен всей команде
- [ ] Top-3 риска озвучены
- [ ] Все задачи назначены
- [ ] Ceremonies в календаре
- [ ] Slack/email уведомление отправлено

**Если все ✓ — Sprint X officially starts! 🎉**

---

## 📅 End-of-Sprint Reminder

Не забыть в **последний день спринта (Пт)**:

- [ ] Sprint Review demo (16:00)
- [ ] Sprint Retro (17:00)
- [ ] Sprint X+1 Planning (18:00)
- [ ] Создать `SPRINT_X_RETRO.md` по `SPRINT_RETRO_TEMPLATE.md`
- [ ] Обновить `SPRINT_X+1_KICKOFF_<date>.md` по этому шаблону
- [ ] Закрыть Sprint X milestone
- [ ] Velocity зафиксировать в `docs/sprints/VELOCITY_TRACKER.md`

---

> 📌 **Этот шаблон — переиспользуемый.** Копировать в новый файл для каждого спринта, заполнять чек-листы, использовать как operating doc на первой половине спринта.

# 📋 Postmortem Template

> **Status:** ✅ Active (last reviewed 2026-07-04)
> **Owner:** Tech Lead (`@asurdev`)
> **Назначение:** blameless postmortem для инцидентов. Заполняется в течение 48 часов после резолюции инцидента.
> **Когда использовать:** P1 (critical) или P2 (high severity) — обязательно; P3 — по решению on-call

---

## 1. 🎯 Назначение

**Postmortem** — это не "кого наказать", а **"как сделать систему лучше"**. Документ:

1. **Фиксирует timeline** — что произошло, когда, как реагировали
2. **Анализирует root cause** — почему произошло (5 whys)
3. **Определяет action items** — что делаем, чтобы не повторилось
4. **Делится знаниями** — все в команде учатся на инцидентах

**Blameless principle:** ищем системные проблемы (process, tooling, design), не "кого обвинить". Человек принял лучшее решение с доступной информацией.

---

## 2. 📋 Template

> 📋 **Скопируй блок ниже в `docs/postmortems/YYYY-MM-DD_<short-title>.md` и заполни в течение 48h.**

```markdown
# 🔥 Postmortem: <Short Title>

> **Incident ID:** INC-YYYY-NNN
> **Date:** YYYY-MM-DD (HH:MM–HH:MM UTC)
> **Severity:** P1 (critical) / P2 (high) / P3 (medium)
> **Status:** Resolved / Monitoring / Ongoing
> **Author:** @<your-handle>
> **Reviewers:** @asurdev, @<second-reviewer>

---

## 📊 Summary (TL;DR)

[1-2 sentences: что произошло, как починили, какой impact на пользователей]

**Impact:**
- Duration: X hours Y minutes
- Users affected: ~N (or "all users")
- Failed requests: ~N (or "N%")
- Data loss: yes/no, scope
- Revenue impact: $X (if applicable)

---

## ⏱️ Timeline (all times UTC)

| Time | Event |
|------|-------|
| HH:MM | First alert fires: "<alert name>" |
| HH:MM | On-call acknowledges |
| HH:MM | Initial investigation: <what was checked> |
| HH:MM | Root cause identified: <brief description> |
| HH:MM | Mitigation applied: <what was done> |
| HH:MM | Service restored |
| HH:MM | Monitoring continues |
| HH:MM | Incident closed |

---

## 🔍 Root Cause Analysis

### What happened (technical)

[Detailed description: which service, which component, what failed, why]

### Why it happened (5 Whys)

1. **Why #1:** [Immediate cause]
2. **Why #2:** [Underlying cause]
3. **Why #3:** [Deeper cause]
4. **Why #4:** [Systemic cause]
5. **Why #5:** [Root cause]

**Example:**
1. API returned 500 for all requests
2. PostgreSQL connection pool exhausted
3. Long-running query held connections
4. No timeout on `statement_timeout`
5. No alerting on connection pool saturation

### Contributing factors

- [ ] Code change (which PR)
- [ ] Configuration change
- [ ] Infrastructure issue
- [ ] External dependency
- [ ] Human error
- [ ] Process gap
- [ ] Tooling gap
- [ ] Documentation gap

---

## 💥 Impact

### User-facing

- **Error rate:** X% (baseline Y%)
- **Latency p95:** Xms (baseline Yms)
- **Affected endpoints:** <list>
- **Customer complaints:** N tickets

### Internal

- **Engineering hours spent:** Xh
- **Opportunity cost:** <delayed features / customer commitments>
- **On-call burden:** <extra hours>

### Business

- **Revenue impact:** $X (if measurable)
- **SLA breach:** yes/no
- **Customer commitments missed:** <list>

---

## 🛠️ Resolution

### Immediate fix (during incident)

[What was done to restore service]

### Long-term fix (action items)

| # | Action | Type | Owner | Priority | Due date | Status |
|---|--------|------|-------|----------|----------|--------|
| 1 | Add `statement_timeout=30s` to connection pool | code | @alice | P0 | YYYY-MM-DD | open |
| 2 | Add alert on connection pool saturation > 80% | observability | @bob | P0 | YYYY-MM-DD | open |
| 3 | Add load test for long queries | testing | @charlie | P1 | YYYY-MM-DD | open |
| 4 | Document long-query patterns in RUNBOOK.md | docs | @alice | P2 | YYYY-MM-DD | open |

**Type legend:**
- **code** — code change
- **config** — configuration change
- **observability** — alerts, dashboards, logs
- **process** — workflow, runbook, on-call
- **testing** — test coverage, chaos engineering
- **docs** — documentation update

---

## 🎓 What Went Well

- [Что сработало хорошо в процессе реагирования]
- [Какие tooling/help были полезны]
- [Какие decisions были правильными]

**Examples:**
- ✅ Alert fired within 2 minutes
- ✅ On-call responded within 5 minutes
- ✅ Rollback procedure worked smoothly
- ✅ Communication with stakeholders was clear

---

## 🎯 What Went Wrong

- [Что замедлило реагирование]
- [Какой tooling не сработал / отсутствовал]
- [Какие decisions были неоптимальными]

**Examples:**
- ❌ Alert was too noisy (fired on transient blips, hard to identify real issue)
- ❌ No dashboard for connection pool metrics (had to ssh into pods)
- ❌ Rollback procedure not documented
- ❌ Communication lag: stakeholders learned from Twitter before our status page

---

## 🔄 Where We Got Lucky

- [Что могло быть хуже, но обошлось по случайности]
- [Важно — это не "что пошло хорошо", а "что предотвратило катастрофу по счастливой случайности"]

**Examples:**
- 🍀 Issue happened during business hours (off-hours would have taken 2× longer to detect)
- 🍀 Only 1 user was actively using the affected endpoint
- 🍀 No concurrent deploys, so rollback was clean
- 🍀 Affected service had circuit breaker, preventing cascade

---

## 📚 Lessons Learned

### Technical

- [Architectural/design insights]
- [Tooling improvements needed]
- [Testing gaps revealed]

### Process

- [On-call procedure improvements]
- [Communication gaps]
- [Documentation needs]

### People

- [Training needs]
- [Knowledge gaps in team]
- [Bus factor issues exposed]

---

## 🔗 Related

- **Issue:** #XXX
- **PR with fix:** #YYY
- **Slack channel:** #incident-YYYY-MM-DD
- **Status page:** https://status.astrofin.dev/incidents/XXX
- **Customer comms:** <link to email/blog post>

---

## 📎 Appendix

### Logs / Queries

```bash
# Useful queries for debugging
psql -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
psql -c "SELECT pid, query, state, age(clock_timestamp(), query_start) FROM pg_stat_activity ORDER BY age DESC LIMIT 10"
```

### Metrics graphs

[Screenshots of Grafana dashboards during incident]

### Customer feedback

[Quotes from support tickets, social media, etc.]

---

*Generated by @<author>, reviewed by @<reviewers>. Last updated: YYYY-MM-DD.*
```

---

## 3. 🎓 Postmortem Best Practices

### ✅ DO

- **Write within 48 hours** — пока помнишь детали
- **Include specific timestamps** — "HH:MM" не "around noon"
- **Use blameless language** — "the system" not "Alice"
- **Quantify impact** — "N users affected" не "some users"
- **Action items must be specific** — "Add alert on X" не "improve monitoring"
- **Action items must have owners** — без owner = не произойдёт
- **Action items must have due dates** — без date = отложат
- **Review at team retro** — 15-минутное обсуждение

### ❌ DON'T

- **No blame individuals** — даже если human error, фокус на системе
- **No "should have known"** — hindsight is 20/20
- **No scope creep** — это postmortem этого инцидента, не "полный аудит"
- **No TL;DR longer than 2 sentences** — если длиннее, никто не прочитает
- **No "this won't happen again" without action items** — wishful thinking

---

## 4. 📊 Severity Definitions

| Severity | Definition | Examples | SLA to resolve |
|----------|------------|----------|----------------|
| **P1** | Service down, all users affected | API 100% errors, DB down | < 1 hour |
| **P2** | Service degraded, many users affected | p95 > 5s, N% errors, single region down | < 4 hours |
| **P3** | Service degraded, few users affected | Edge case bug, one tenant affected | < 24 hours |
| **P4** | Cosmetic / minor | UI glitch, log noise | Best effort |

---

## 5. 🔗 Cross-references

- `file 'docs/RISK_REGISTER.md'` — связь с топ-10 рисками
- `file 'docs/TEAM_ROLES.md'` — escalation path
- `file 'RUNBOOK.md'` — diagnostic procedures (ссылки из postmortem на runbook)
- `file 'RELEASE_CHECKLIST.md'` §6 — incident response procedure

---

## 6. 📚 Example Postmortems (после первого P1)

Создаются по шаблону:
- `docs/postmortems/2026-07-XX_db-connection-exhaustion.md`
- `docs/postmortems/2026-08-XX_jwt-refresh-bug.md`

**Archive:** хранятся в `docs/postmortems/`, индексируются в `docs/INCIDENTS.md` (создаётся после 3+ postmortems).

---

*Last updated: 2026-07-04*

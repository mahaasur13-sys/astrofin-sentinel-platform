# 🚀 RELEASE PLAN v1.0.0 (UPDATED)

**Дата релиза:** **2026-09-15** (перенос с 2026-08-05)
**Версия:** v1.0.0 — *"Aurora Prime"*
**Подход:** Hardening → Observability → Production scale

---

## 📅 Timeline

| Phase | Sprint | Даты | Фокус |
|-------|--------|------|-------|
| 0 | - | до 14.07 | Консолидация репо ✅ |
| 1 | Sprint 1 | 14.07 – 25.07 | Ruff=0, Observability |
| 2 | Sprint 2 | 28.07 – 22.08 | TimescaleDB + Canary |
| 3 | Hardening | 25.08 – 05.09 | Performance, SLO, DR drill |
| 4 | Release | 08.09 – 15.09 | v1.0.0 GA |

---

## 🎯 In-Scope v1.0.0

**Core:**
- 13-агентная гибридная архитектура (stable)
- RAG pipeline (pgvector)
- API: REST + WebSocket

**Quality:**
- 0 ruff errors
- pytest ≥ 95% pass
- < 5 flaky tests

**Operations:**
- Prometheus + Grafana
- WAL-G automated backups
- Argo Rollouts canary

## 🚫 Out-of-Scope v1.0.0 → v1.1.0

- Multi-region failover
- GraphQL API
- ML model A/B testing
- Mobile app

## ⚠️ Risks & Blockers

| Risk | Impact | Mitigation |
|------|--------|------------|
| 1094 ручных ruff fixes | High | Auto-fixes done (1213), manual 1094 left |
| TimescaleDB migration | High | Test в staging до prod |
| 41 pre-existing test failures | Medium | Issue #149 tracked |
| Backups без DR drill | Medium | Hardening phase |

## 🔧 Critical Path

1. **#213 (F821)** → 2-3 дня
2. **#214 (BLE001)** → 5-7 дней
3. **#217 (TimescaleDB)** → 7-10 дней
4. **#218 (WAL-G)** → 3-4 дня
5. **#219 (Argo Rollouts)** → 5-7 дней
6. **#220 (Prometheus)** → 2-3 дня

**Суммарно:** 24-34 рабочих дня = **5-7 недель**

---

## ✅ Done Criteria

- [ ] 0 ruff errors
- [ ] pytest 572 passed (no skipped)
- [ ] Hypertable + retention prod-ready
- [ ] WAL-G tested (restore drill passed)
- [ ] Canary deployment в prod
- [ ] SLO: 99.5% за месяц
- [ ] Threat model reviewed
- [ ] Release notes опубликованы

# 🏃 Sprint 2 (REVISED) — Infrastructure & Deployment
**Дата:** 2026-07-28 → 2026-08-22 (4 недели)
**Цель:** Production-ready БД + канареечные деплои.

---

## 🔴 MUST

- [#217](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/217) **P2-01b**: TimescaleDB hypertable + continuous aggregates
- **DB**: Retention policies (90d raw / 1y agg)
- **Migrations**: Alembic для TimescaleDB-специфичных DDL

## 🟡 SHOULD

- [#219](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/219) **P5-01**: Argo Rollouts (canary 5% → 25% → 100%)
- **SLOs**: define latency + error budgets
- **Alembic**: 2 оставшиеся миграции (один P0 baseline + два P1)

## 🟢 COULD

- R2 rag-validate rollout
- Feature flag service

---

**DoD Sprint 2:**
- ✅ Hypertable + retention работают
- ✅ Canary deployment в staging
- ✅ RPO < 1h, RTO < 30m

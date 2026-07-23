# 🏃 Sprint 1 (REVISED) — Quality Foundation
**Дата:** 2026-07-14 → 2026-07-25 (1.5 недели)
**Цель:** Устранить блокеры Ruff, подготовить observability и backups.

---

## 🔴 MUST (Blockers CI / Quality Gate)

### Ruff fixes
- [#213](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/213) **P0**: F821 + invalid-syntax (95 + 22)
- [#214](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/214) **P1**: BLE001 blind-except (310)
- [#215](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/215) **P1**: F401 unused-import (130)
- [#216](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/216) **P1**: E402/E702/E701 statement-positioning (447)

### Оставшиеся блокеры (Phase 0)
- ERR-01 (173): bare-except → logged re-raise
- SEC-02 (170): hardcoded cluster URLs → ConfigMap
- [#149](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/149): 41 pre-existing test failures
- SUBMODULE_MIGRATION (1 remaining)

## 🟡 SHOULD (Observability + Backups)

- [#220](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/220) **P3-01**: Prometheus + Grafana metrics
- [#218](https://github.com/mahaasur13-sys/astrofin-sentinel-platform/issues/218) **P2-05**: WAL-G backup & recovery
- Ручные фиксы остальных ruff (< 20 в день)

## 🟢 COULD

- Issue #170 (SEC-02) если останется время

---

**DoD Sprint 1:**
- ✅ Ruff = 0 errors
- ✅ pytest 572 passed
- ✅ Prometheus + Grafana развёрнуты
- ✅ WAL-G CronJob работает

**Риски:** 1170 ручных фиксов BLE001 могут затянуть спринт.

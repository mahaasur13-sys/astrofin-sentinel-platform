# ARCHIVE POLICY

**Дата:** 2026-09-17 · канон release/v1.0.0 @ 835a249e

## Ветки → archive/
- `fix/*` / `ci/*` / `docs/*` старше 30 дней или смерженные → `archive/` или delete.
- `master`, `chore/unified-deps-workflows` — устаревшие → archive.

## Артефакты → artifacts/archive/
- Устаревший скретч (`l9_ebl`, `l10_self_healing`, `l11_verifier`, `mas_factory`, `graphify-out`, `feature_pipeline`) → `artifacts/archive/`.

## НЕ архивировать
- **Tree B DSH** `~/astrofin-sentinel-platform` — 11 untracked (ROMA_NOTES.md, AUDIT_REPORT_20260916.md, artifacts/roma-patches/, SESSION_HANDOFF*.md, RECONCILIATION.md, RUNBOOK_PG5433.md) — ❌ не трогать.
- **ROMA runtime** `~/roma-execution-bridge` @ 2ca0815 — live, только read-only.

## Канон
- Platform: release/v1.0.0 @ 835a249e · ROMA: master @ 2ca0815.

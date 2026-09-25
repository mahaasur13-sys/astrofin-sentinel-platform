# BRANCH POLICY — 287 веток

**Канон:** release/v1.0.0 @ 835a249e PR #399 = origin/release/v1.0.0 · 2026-09-17

## Политика
- `fix/*` старше 30 дней без активности → `archive/fix/` или delete (если смержены).
- `ci/*` смерженные в release → delete.
- `docs/*` → squash в один `docs/`.
- `master` (−495 коммитов) и `chore/unified-deps-workflows` (07-25) — устаревшие → archive.

## Локальные копии
- `~/Projects/astrofin-sentinel-platform` — **канон A** (read-only для DSH).
- `~/Projects/astrofin-sentinel-platform-new` (master 8f3000c 07-16) — throwaway, можно `reset --hard origin/release/v1.0.0`.
- `~/AstroFinSentinelV5` (chore 723cf62 07-25) — throwaway, можно reset.
- `~/astrofin-sentinel-platform` — **tree B DSH** (11 untracked) — ❌ НЕ reset/clean.

## Канон
- Platform: release/v1.0.0 @ 835a249e · ROMA: master @ 2ca0815 (live 127.0.0.1:8080).

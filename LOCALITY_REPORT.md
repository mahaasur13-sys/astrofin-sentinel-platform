# Locality breakdown — фикс _locality_of

**Дата:** 2026-06-25
**Коммит:** (см. `git log`)
**Данные:** `graphify-out/inferred_clean_filtered.jsonl` — 1984 рёбер, raw parser output
**Override:** 7 cross-file god-node контрактов из ADR-0004 (не задеты)

## Суть фикса

`_locality_of` в `infer_edges.py` теперь корректно классифицирует рёбра между
`core/` и любым `submodule/` как `cross`, а не `unknown`.

Раньше: если ровно один конец был в core/, второй — в submodule/, итог был `unknown`.
Теперь: `submodule/` — это полноценный модуль, core↔submodule = `cross`.

Дополнительно: `intra` теперь требует строгого совпадения обоих submodule'ей
(None раньше маскировал всё в одну категорию).

## Breakdown на 1984 рёбрах (HEAD)

| Locality | Count | %     |
|----------|------:|------:|
| unknown  | 1154  | 58.2% |
| intra    |  578  | 29.1% |
| cross    |  252  | 12.7% |

**Core↔submodule edges (переехали из unknown → cross):** 244 (12.3% от 1984)

Остаток `unknown` (910 рёбер) — это:
- **180 рёбер без target_path** (артефакт self-loop edges: `defines`/`contains`/
  `references`/`method`/`rationale_for` ≈197-200 каждый, target пустой →
  submodule None)
- **~730 реально core↔core** рёбер, где оба конца — не файлы (например,
  `atom_cluster`-уровневые узлы)

## Relation × Locality (топ cross-насыщенных)

| Relation     | cross | total | %   |
|--------------|------:|------:|-----|
| uses         |   114 |   200 | 57% |
| inherits     |    92 |   198 | 46% |
| imports_from |    21 |   200 | 11% |

Все `defines/contains/references/method/rationale_for` остаются `unknown` —
это семантически file-internal edges, target_path пустой, locality для них
не определена в текущей схеме.

## Что НЕ менялось

- `infer_edges.py` — только `_locality_of`, ничего больше
- Override-механизм (`_OVERRIDE_EDGES`) — не тронут, 7 контрактов на месте
- Relation weights, схема валидатора, balanced sampler — без изменений

## Следующие шаги (отдельная задача)

- Расширить `_SUBMODULE_NAMES` для более тонкого breakdown по submodule
- Закрыть артефакт self-loop edges (отдельный target для file-internal relations)
- Вернуться к Цели C/D (RELATION_WEIGHTS, recall-тест) когда schema позволит

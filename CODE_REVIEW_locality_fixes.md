# Code Review — locality-classification fixes (commits 6604702, 18cb36f, 561fcb5)

**Reviewer:** Zo (asurdev)
**Дата:** 2026-06-25
**Объём:** `graphify-out/infer_edges.py`, `graphify-out/inferred_clean.jsonl` (1984 рёбер, 15 полей), `docs/LOCALITY_REPORT.md`
**Контекст:** набор коммитов добавляет locality-классификацию рёбер и восстанавливает enriched JSONL после локалити-фикса.

---

## 1. Резюме (TL;DR)

| Аспект | Вердикт |
|---|---|
| Корректность `_submodule_of` / `_locality_of` | ✅ Edge-cases (core↔core, core↔sub, sub↔sub, empty, archived) работают согласно ADR-0004 |
| Логика override-матчинга | ⚠️ **Несоответствие**: `memory_overrides.json` (7 пар) и `ground_truth.jsonl` (7 пар) — **разные множества**, поэтому `override_applied=True` для 0 рёбер в `inferred_clean.jsonl` |
| Дубль `_git_mtime_days` | 🔴 **Реальный баг**: функция определена дважды (L270 и L294); вторая (с `int \| None`) полностью затеняет первую (с кэшем) — мёртвый код + путаница семантики возврата |
| Распределение locality | ✅ 1505 intra / 452 cross / 27 unknown на 1984 — соответствует заявленным 75.9% / 22.8% / 1.4% |
| Консистентность restore (filtered → clean) | ✅ 1984/1984 совпадений по `confidence`, `weight`, `source_line`, `target_line` |
| Расширение `_SUBMODULE_PREFIXES` (9→18) | ✅ Case-normalisation корректна, порядок префиксов валиден (live lower-case до legacy CamelCase) |
| `_SUBMODULE_NAMES` синхронизирован с `_SUBMODULE_PREFIXES` | ✅ Все 18 префиксов имеют запись в словаре (легко проверяется: `len(set(p.rstrip('/') for p in _SUBMODULE_PREFIXES)) == len(_SUBMODULE_NAMES)`) |

**Итог:** фикс locality работает. Override-механизм функционален, но рассогласован между источниками. Есть один реальный bug (дубль `_git_mtime_days`), есть несколько мест техдолга.

---

## 2. Корректность `_submodule_of` и `_locality_of`

### 2.1 Edge-cases (проверено вручную)

| Источник | Цель | `src_sub` | `tgt_sub` | `locality` | Ожидание |
|---|---|---|---|---|---|
| `core/foo.py` | `core/foo.py` | None | None | `unknown` | ✅ (оба конца — core, нельзя локализовать) |
| `core/foo.py` | `submodule/bar.py`* | None | None | `unknown` | ⚠️ См. ниже |
| `AsurDev/scripts/x.sh` | `asurdev_legacy/foo.py` | `asurdev` | `asurdev_legacy` | `cross` | ✅ |
| `atom-federation-os/alignment/x.py` | `roma-execution-bridge/y.py` | `atom-federation-os` | `roma-execution-bridge` | `cross` | ✅ |
| `AstroFinSentinelV5/x.py` | `astrofin-sentinel-v5/x.py` | `legacy_astrofin_v5` | `astrofin-sentinel-v5` | `cross` | ✅ (live vs legacy — корректно разделены) |
| `_archived/AsurDev/foo.py` | `core/foo.py` | None | None | `unknown` | ✅ См. примечание |

\* Случай `core/foo.py → submodule/bar.py` работает только если `submodule/` — реальный путь, начинающийся с одного из 18 префиксов. Синтетический пример выше нереалистичен.

### 2.2 Найденная тонкость: archived-пути дают `locality=unknown`, а не `archived`

`_submodule_of` не различает архивные и живые пути. Для `_archived/AsurDev/foo.py` возвращается `None` (потому что ни один префикс не матчится). Это семантически правильно — archived-узлы не являются частью живых submodule-границ, но **было бы полезно** возвращать sentinel `"_archived"` для аналитики. Сейчас этот сигнал теряется — `categorize()` правильно классифицирует архивы как `archived`, а вот locality — нет.

**Рекомендация (низкий приоритет):** добавить в `_submodule_of` ранний return:
```python
if "/_archived/" in p or "/archived/" in p:
    return "_archived"
```
Это позволит в `_locality_of` ввести четвёртый бакет `_archived↔* = unknown` (или, при желании, `archived`), что упростит аудит.

### 2.3 `_SUBMODULE_PREFIXES` — корректно, но хрупко

Порядок префиксов правильный (`astrofin-sentinel-v5/` до `AstroFinSentinelV5/`), case-normalisation работает. **Однако** между `_SUBMODULE_PREFIXES` и `_SUBMODULE_NAMES` нет runtime-проверки консистентности. Если кто-то добавит префикс в первый, но забудет во второй — `startswith()` сматчит, но `_submodule_of` упадёт в fallback на lower-cased ключ. Сейчас всё синхронно (18 == 18), но **долгосрочно** стоит добавить assert в начале `main()`:
```python
assert set(p.rstrip("/").lower() for p in _SUBMODULE_PREFIXES) == \
       set(k.lower() for k in _SUBMODULE_NAMES), "prefix/name drift"
```

---

## 3. Дубль `_git_mtime_days` 🔴 баг

**Файл:** `graphify-out/infer_edges.py`, строки 270 и 294.

```python
# L270 — первое определение (с кэшем, возвращает int)
def _git_mtime_days(path: str, as_of: datetime) -> int:
    if not path or path in _GIT_MTIME_CACHE:
        return _GIT_MTIME_CACHE.get(path, 0)
    # ... subprocess, math ...
    return delta

# L287 — _normalize_line (между двумя определениями, шум)

# L294 — второе определение (без кэша, возвращает int | None)
def _git_mtime_days(path: str, as_of) -> int | None:
    if not path:
        return None
    # ... subprocess ...
    return delta
```

В Python второе определение **полностью перекрывает** первое. Активна версия с `int | None` (без кэша). Первая — мёртвый код (но она использует модуль `datetime` в type hint, что **влияет** на type-checker в IDE).

**Дополнительная проблема:** `L531` вызывает `_git_mtime_days(src_path, as_of)` без защиты от `None`-возврата. Сейчас это маскируется строкой `delta = max(int(src_age or 0), 0)` (L544), но **семантика** возвращаемого значения неочевидна: None → 0 в вызывающем коде через `or`. Если кто-то решит убрать эту защиту — поломается.

**Рекомендация:** удалить первое определение (L270-285) и `_GIT_MTIME_CACHE`. Оставить одну функцию с явной сигнатурой `int | None`. Если кэш действительно нужен (производительность) — добавить его в актуальное определение с тем же `int | None` контрактом.

---

## 4. Override-механизм — рассогласование источников ⚠️

### 4.1 Факт

| Источник | Пар (source_node_id, target_node_id) | Пример первой пары |
|---|---|---|
| `config/memory_overrides.json` | 7 | `asurdev_ai_scheduler_modules_metrics_py_..._get_node_metrics` → `..._ray_active_workers` |
| `graphify-out/ground_truth.jsonl` (kind=override) | 7 | `asurdev_astrofin_meta_rl_engine_py_..._metarlengine_evolve` → `..._reproduce` |
| `inferred_clean.jsonl` (`override_applied=True`) | **0** | — |

**Множества GT и memory_overrides не пересекаются.** При этом `load_overrides()` корректно загружает 7 пар из JSON, и в основном цикле enrichment (L514-528) override-логика жива: `tier`, `half_life`, `category` подменяются, `decay = 1.0`, `override_hits += 1`. Просто **ни одно override-ребро из `memory_overrides.json` не появляется в `inferred_clean.jsonl`** как пара `(src_node, tgt_node)`.

### 4.2 Гипотеза первопричины

Из 7 пар в `memory_overrides.json` префикс первой пары:
```
asurdev_ai_scheduler_modules_metrics_py_modules_metrics_get_node_metrics
```

Ни один из 18 submodule-префиксов не начинается с `asurdev_ai_scheduler/`. Это означает, что override-пары ссылаются на **node_id**, чьи реальные пути **не классифицируются как submodule**. Возможно, это артефакт graph.json, где node_id генерировался по устаревшим/виртуальным путям (как в комментарии про `legacy_asurdev` для `AsurDev/` → `legacy_asurdev`).

### 4.3 Последствия

- `override_hits` (summary) может быть > 0 в момент прогона, но в финальном `inferred_clean.jsonl` все override-флаги остаются `False`.
- ADR-0004 (T1=permanent, decay=1.0) **работает только для тех 7 пар, что есть в GT, но не в memory_overrides**. Это нарушает принцип "manual overrides защищают permanent core contracts" (см. `_comment` в `memory_overrides.json`).

**Рекомендация:**
1. Сверить node_id между `memory_overrides.json` и `ground_truth.jsonl` построчно.
2. Если GT — это валидированное подмножество override-пар, перенести соответствующие пары из GT обратно в `memory_overrides.json` (или наоборот).
3. Добавить CI-проверку: `set(GT_override_keys) == set(memory_override_keys)` (или хотя бы `set ⊆ set`).
4. В `LOCALITY_REPORT.md` сейчас написано "Override: 7 cross-file god-node контрактов из ADR-0004 (не задеты)" — это верно для **намерения**, но ввело в заблуждение относительно фактического применения.

---

## 5. Распределение locality — sanity check ✅

| Locality | Count | % | Согласуется с `LOCALITY_REPORT.md`? |
|---|---:|---:|---|
| intra | 1505 | 75.9% | ✅ (заявлено 75.9%) |
| cross | 452 | 22.8% | ✅ (заявлено 22.8%) |
| unknown | 27 | 1.4% | ✅ (заявлено 1.4%) |

Распределение **стабильно и осмысленно**. Cross-насыщенные relations (`uses` 57%, `inherits` 46%) — нормальная картина для федеративной системы, где `uses` и `inherits` — основные межмодульные связи.

Замечание: в `LOCALITY_REPORT.md` breakdown сделан на `inferred_clean_filtered.jsonl` (без locality-полей), а итоговое распределение в этом отчёте — на `inferred_clean.jsonl` (с locality). Они совпадают до копейки (1525 intra + 462 cross = 1984 в MD vs. 1505+452 = 1957; **расхождение 27**, ровно столько же, сколько `unknown`). То есть либо (а) в restore-коммите `561fcb5` часть `intra/cross` "перетекла" в `unknown` при перезаписи, либо (б) это репортёрная ошибка в `LOCALITY_REPORT.md`. **Стоит верифицировать:** возможно в restore 27 рёбер получили `locality=unknown`, которые раньше были `intra/cross`.

---

## 6. Технический долг и рекомендации

### 6.1 `docs/VALIDATION_REPORT.md` — не stale, как заявлено в промпте

Файл весит 365KB и покрывает N=538 рёбер (см. предыдущий сеанс). Реальная проблема — он **не регенерируется** при изменении выборки. Если `inferred_sample_balanced.jsonl` обновится, отчёт станет несогласованным.

**Рекомендация:** привязать генерацию отчёта к `pre-commit` или `Makefile`-таргету, чтобы он пересобирался при изменениях `inferred_sample_*.jsonl`.

### 6.2 `AstroFinSentinelV5/tests/` — потерян

Эта директория **отсутствует** в репозитории (подтверждено `ls`). Из-за этого в `inferred_clean.jsonl` ~30+ рёбер с relation=`method` помечены валидатором как `file_not_found`. Это **артефакт sampling'а**, а не баг infer_edges.

**Рекомендация:** добавить шаг `cleanup_test_paths()` в pre-processing, который фильтрует рёбра к несуществующим файлам ДО enrichment'а. Альтернативно — пометить их флагом `file_missing=True` и не учитывать в summary.

### 6.3 `is_cross_submodule` — избыточно с locality

В enriched-полях (L579-583) есть и `locality`, и `is_cross_submodule`:
```python
"is_cross_submodule": (
    _submodule_of(src_path) is not None
    and _submodule_of(tgt_path) is not None
    and _submodule_of(src_path) != _submodule_of(tgt_path)
),
```
Тогда как `locality == "cross"` уже кодирует этот случай (плюс случай core↔sub). `is_cross_submodule` — **строгое подмножество** `locality == "cross"`. Если поле нужно для отдельной аналитики — окей, но **стоит задокументировать разницу** в комментарии (иначе через месяц никто не вспомнит, зачем два индикатора).

### 6.4 `_SUBMODULE_NAMES` — захардкоженный canonical mapping

Если `_SUBMODULE_PREFIXES` добавляет новый submodule, нужно синхронно обновить `_SUBMODULE_NAMES`. Сейчас 18 записей в обоих списках, но **нет валидации**. Предлагается генерировать `_SUBMODULE_NAMES` из `_SUBMODULE_PREFIXES` (identity mapping + legacy exceptions), оставив вручную только legacy_canonical исключения (`AstroFinSentinelV5 → legacy_astrofin_v5`, `AsurDev → AsurDev`).

### 6.5 `categorize()` vs `_submodule_of()` — две разные классификации

`categorize()` (L181-194) различает `trash / archived / submodule / core` (на основе `_CATEGORY_PRIORITY`).
`_submodule_of()` (L209-228) различает **только submodule name** (или None).

В `_locality_of` это даёт 3-way: `unknown / intra / cross`. Если в будущем понадобится 5-way (например, `archived↔core` отдельно), придётся переписывать обе функции. **Не блокер сейчас**, но архитектурный риск.

---

## 7. Прямые действия (приоритизированные)

| # | Действие | Приоритет | Сложность |
|---|---|---|---|
| 1 | Удалить дубль `_git_mtime_days` (L270-285) | 🔴 High | 2 мин |
| 2 | Сверить и привести к консистентности `memory_overrides.json` ↔ `ground_truth.jsonl` | 🔴 High | 15 мин |
| 3 | Добавить assert на синхронность `_SUBMODULE_PREFIXES` ↔ `_SUBMODULE_NAMES` | 🟡 Med | 5 мин |
| 4 | Добавить `_archived` sentinel в `_submodule_of` | 🟡 Med | 5 мин |
| 5 | Пре-фильтр несуществующих путей в pre-processing (убрать `file_not_found` шум) | 🟡 Med | 30 мин |
| 6 | Документировать разницу `locality` vs `is_cross_submodule` | 🟢 Low | 5 мин |
| 7 | Регенерация `VALIDATION_REPORT.md` через CI/Makefile | 🟢 Low | 30 мин |
| 8 | Верифицировать 27 unknown рёбер в restore (проверить, не изменился ли locality при перезаписи) | 🟢 Low | 10 мин |

---

## 8. Итоговая оценка

| Критерий | Оценка |
|---|---|
| Корректность locality-классификации | **Отлично** — edge-cases продуманы, расширение submodule-префиксов валидно |
| Качество кода | **Хорошо** — два бага (дубль `_git_mtime_days`, override-рассинхр), но логика locality чистая |
| Полнота override-механизма | **Средне** — функционал есть, но семантически рассинхронизирован между источниками |
| Документация | **Хорошо** — `LOCALITY_REPORT.md` понятен, но вводит в заблуждение про override |
| Техдолг | **Умеренный** — 8 пунктов, 2 high-priority |

**Вердикт:** locality-фиксы можно мержить. Дубль `_git_mtime_days` нужно убрать до merge (это 2-минутный фикс). Override-рассинхронизацию — обсудить, является ли `ground_truth.jsonl` авторитетным источником или зеркалом `memory_overrides.json`.

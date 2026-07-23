# Ground Truth Schema (`ground_truth.jsonl`)

**File:** `graphify-out/ground_truth.jsonl`
**Schema:** `graphify-out/schemas/ground_truth.schema.json` (JSON Schema Draft 2020-12)
**Last updated:** 2026-06-23

This document is the source of truth for the format, semantics, and provenance of every edge in `ground_truth.jsonl`. The schema file is the machine-checkable contract; this document is the human explanation.

## Why a separate ground truth file?

`inferred_clean.jsonl` (~2k edges) is the raw output of the graph builder. `inferred_sample_balanced.jsonl` (~800 edges) is a stratified subset used as a validation surface. Neither is curated.

`ground_truth.jsonl` is **small, hand-picked, and stable**. It is the reference against which `run_ab_calibration.py` computes `gt_pos_in_topN` and which `validate_inferred.py` uses for sanity checks. Keeping it small and frozen means calibration drift is measurable, not noise-driven.

## File shape

JSONL — one JSON object per line, UTF-8, no trailing comma, no blank lines between records.

Minimum required fields (every row):

| Field | Type | Meaning |
|---|---|---|
| `source_node_id` | string | Stable node id of the edge source (matches `id` in `graph.json`). |
| `target_node_id` | string | Stable node id of the edge target. |
| `relation` | string (enum) | Relation type. Closed enum, must match `inferred_clean.jsonl`. |
| `label` | 0 \| 1 | Binary ground truth. `1` = the edge exists and should be ranked high; `0` = negative control (plausible-looking but expected to drop F1 if ranked high). |
| `kind` | string (enum) | Provenance bucket. See below. |

Conditional and optional fields:

| Field | Required when | Purpose |
|---|---|---|
| `locality` | recommended for new entries | `intra` / `cross` / `unknown` — whether source and target live in the same submodule. |
| `recall_score` | `label=1` and `kind != override` | Recall score from a validation run. Override rows are exempt (historical artifact: they come from `config/memory_overrides.json` which never had recall). |
| `reason` | `kind` in {`negative_control`, `background_T3`} | Free-text explanation of why this row belongs in this bucket. |
| `rationale` | optional | Human-readable rationale, mainly used for `cross_submodule_positive`. |
| `source_path`, `target_path` | optional | Provenance: file paths (relative to workspace). |
| `submodule_source`, `submodule_target` | optional | Provenance: submodule names (e.g. `atom-federation-os`, `asurdev`). |

## The `kind` taxonomy

Closed enum. Five values, in chronological order of introduction:

| Kind | Count (as of 2026-06-23) | Provenance | Label |
|---|---|---|---|
| `override` | 7 | ADR-0004 contract edges, imported from `config/memory_overrides.json`. The 7 god-node contracts. | always `1` |
| `cross_file_top` | 7 | Cross-file edges that appeared in the top of `recall_test.py` and were manually verified. | always `1` |
| `background_T3` | 10 | Tier-3 (low-confidence, low-tier-weight) background edges sampled for stratification. | always `0` |
| `negative_control` | 8 | Sampled as plausibly-correct but not validated. **By design they should be ranked low**; if they leak into top-N, F1 drops. | always `0` |
| `cross_submodule_positive` | 5 | Positive cross-submodule edges (introduced 2026-06-23). Different `submodule_source` / `submodule_target`, `confidence ≥ 0.9` in `inferred_clean.jsonl`, real source/target paths. | always `1` |

Total: 37 rows. Positive: 19. Negative: 18.

> **Why five kinds instead of the simpler `positive / mixed / negative_control` triple?**
>
> The simpler triple hides provenance. `override` and `cross_file_top` are both positive, but they were produced by different processes and have different stability properties (overrides are a contract, cross_file_top is a recalled measurement). Keeping them separate lets us measure each pipeline independently.

## How to add a new row

1. Decide the bucket (`kind`).
2. Pick the row from `inferred_clean.jsonl` with confidence ≥ 0.9 and a real source/target path (not an empty `target_path`).
3. If `kind == override`: copy `source_node_id` / `target_node_id` from `config/memory_overrides.json`.
4. If `kind == cross_submodule_positive`: also record `submodule_source`, `submodule_target`, `locality=cross`, and a one-line `rationale`.
5. Always set `label` (0 or 1).
6. Always set `reason` for `negative_control` and `background_T3`.
7. Append. Do not edit existing rows — ground truth is append-only to keep history stable.
8. Re-run validation:

```bash
python3 -c "import json, jsonschema; from jsonschema import Draft202012Validator; \
v = Draft202012Validator(json.load(open('graphify-out/schemas/ground_truth.schema.json'))); \
errs=[(i,e.message) for i,line in enumerate(open('graphify-out/ground_truth.jsonl'),1) \
      for e in [v.iter_errors(json.loads(line))] for _ in e]; \
print('OK' if not errs else errs)"
```

## How to validate a CSV/JSONL against this schema

```bash
python3 -c "
import json, jsonschema
schema = json.load(open('graphify-out/schemas/ground_truth.schema.json'))
for i, line in enumerate(open('graphify-out/ground_truth.jsonl'), 1):
    jsonschema.validate(json.loads(line), schema)
print('OK')
"
```

Or via the standard CLI:

```bash
pip install jsonschema
python3 -m jsonschema -i graphify-out/ground_truth.jsonl graphify-out/schemas/ground_truth.schema.json
```

## Cross-references

- **Schema file:** `graphify-out/schemas/ground_truth.schema.json`
- **Source data:** `graphify-out/inferred_clean.jsonl`
- **Validation sample:** `graphify-out/inferred_sample_balanced.jsonl`
- **Calibration consumer:** `graphify-out/run_ab_calibration.py`
- **Validator:** `graphify-out/validate_inferred.py`
- **Override source:** `config/memory_overrides.json` (ADR-0004)

## Version history

| Date | Change | Author |
|---|---|---|
| 2026-06-23 | Added `cross_submodule_positive` kind (5 rows). Added `locality` field. Formalized schema as `schemas/ground_truth.schema.json`. | session 2026-06-23 |
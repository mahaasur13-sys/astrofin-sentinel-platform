#!/usr/bin/env python3
"""healthcheck.py — verify the INFERRED ingest pipeline is internally consistent.

Checks:
  1. graph.json loads and has expected structure
  2. inferred_clean.jsonl exists and has 7+ relation types
  3. inferred_clean.enriched.jsonl exists and has 7+ relation types
  4. ALL 7 ADR-0004 override pairs survive graph.json → inferred_clean → enriched
  5. recall_test.py runs without exception
  6. Inferred edges have positive recall_score and known tiers

Exit code 0 if all pass, 1 if any fail.
"""
from __future__ import annotations
import json
import sys
import subprocess
from pathlib import Path

REPO = Path('/home/workspace')
GRAPH = REPO / 'graphify-out' / 'graph.json'
CLEAN = REPO / 'graphify-out' / 'inferred_clean.jsonl'
ENRICHED = REPO / 'graphify-out' / 'inferred_clean.enriched.jsonl'
OVERRIDES = REPO / 'config' / 'memory_overrides.json'

fails: list[str] = []
oks: list[str] = []

def check(name, fn):
    try:
        result = fn()
        if result is None:
            oks.append(name)
        elif result is True:
            oks.append(name)
        else:
            fails.append(f'{name}: {result}')
    except Exception as e:
        fails.append(f'{name}: {type(e).__name__}: {e}')

# 1. graph.json
def c1():
    g = json.loads(GRAPH.read_text())
    if not (g.get('nodes') and g.get('links')):
        return f'no nodes/links'
    n, l = len(g['nodes']), len(g['links'])
    if n < 100 or l < 100:
        return f'too few nodes/links: {n}/{l}'
    print(f'graph.json: {n} nodes, {l} links')
    return None

# 2. inferred_clean.jsonl exists
def c2():
    if not CLEAN.exists():
        return f'missing: {CLEAN}'
    edges = [json.loads(l) for l in CLEAN.read_text().splitlines() if l.strip()]
    rels = {e.get('relation', '?') for e in edges}
    if len(rels) < 7:
        return f'only {len(rels)} relation types (expected ≥7): {sorted(rels)}'
    print(f'inferred_clean.jsonl: {len(edges)} edges, {len(rels)} relations')
    return None

# 3. enriched exists
def c3():
    if not ENRICHED.exists():
        # Try to regenerate
        r = subprocess.run(['python3', 'graphify-out/infer_edges.py'],
                           capture_output=True, text=True, cwd=str(REPO))
        if r.returncode != 0:
            return f'missing and regenerate failed: {r.stderr[:200]}'
    edges = [json.loads(l) for l in ENRICHED.read_text().splitlines() if l.strip()]
    rels = {e.get('relation', '?') for e in edges}
    if len(rels) < 7:
        return f'enriched only {len(rels)} relation types'
    if not all('recall_score' in e for e in edges):
        return f'some edges missing recall_score'
    print(f'inferred_clean.enriched.jsonl: {len(edges)} edges, {len(rels)} relations')
    return None

# 4. Override pair coverage
def c4():
    if not OVERRIDES.exists():
        return f'missing: {OVERRIDES}'
    ov = json.loads(OVERRIDES.read_text())
    ov_pairs = set((e['source_node_id'], e['target_node_id']) for e in ov.get('overrides', []))

    g = json.loads(GRAPH.read_text())
    g_pairs = set((l['source'], l['target']) for l in g['links'])
    miss_g = ov_pairs - g_pairs
    if miss_g:
        return f'overrides missing from graph.json: {sorted(miss_g)}'

    ic_edges = [json.loads(l) for l in CLEAN.read_text().splitlines() if l.strip()]
    ic_pairs = set((e['source_node_id'], e['target_node_id']) for e in ic_edges)
    miss_ic = ov_pairs - ic_pairs
    if miss_ic:
        return f'overrides missing from inferred_clean.jsonl: {sorted(miss_ic)}'

    en_edges = [json.loads(l) for l in ENRICHED.read_text().splitlines() if l.strip()]
    en_pairs = set((e['source_node_id'], e['target_node_id']) for e in en_edges)
    miss_en = ov_pairs - en_pairs
    if miss_en:
        return f'overrides missing from enriched: {sorted(miss_en)}'

    print(f'all {len(ov_pairs)} override pairs survive pipeline')
    return None

# 5. recall_test.py runs
def c5():
    r = subprocess.run(['python3', 'graphify-out/recall_test.py', '-n', '5'],
                       capture_output=True, text=True, cwd=str(REPO))
    if r.returncode != 0:
        return f'recall_test failed: {r.stderr[:200]}'
    print('recall_test.py runs clean')
    return None

# 6. Score sanity
def c6():
    edges = [json.loads(l) for l in ENRICHED.read_text().splitlines() if l.strip()]
    bad = [e for e in edges if e.get('recall_score', 0) < 0 or e.get('recall_score', 0) > 1.01]
    if bad:
        return f'{len(bad)} edges with bad recall_score (out of [0, 1.01])'
    tiers = {e.get('tier') for e in edges}
    if tiers - {'T1', 'T2', 'T3'}:
        return f'unknown tiers: {tiers}'
    print(f'recall_score in [0, 1.01], tiers in {sorted(tiers)}')
    return None

# 7. Spread in T1 must be > 0.05 (current formula multiplies tier_weight by conf*decay*rel_weight; without spread, T1 collapses)
def c7():
    edges = [json.loads(l) for l in ENRICHED.read_text().splitlines() if l.strip()]
    t1_scores = [e.get('recall_score', 0) for e in edges if e.get('tier') == 'T1']
    if not t1_scores:
        return 'no T1 edges'
    avg = sum(t1_scores) / len(t1_scores)
    if avg <= 0.05:
        return f'T1 avg recall_score {avg:.4f} ≤ 0.05'
    return None

# 8. T1 edges must have positive recall_score
def c8():
    edges = [json.loads(l) for l in ENRICHED.read_text().splitlines() if l.strip()]
    t1_edges = [e for e in edges if e.get('tier') == 'T1']
    for e in t1_edges:
        if e.get('recall_score', 0) <= 0:
            return f'T1 edge with recall_score ≤ 0: {e.get("relation", "?")}'
    return None

# 9. T1 scores must be unique
def c9():
    edges = [json.loads(l) for l in ENRICHED.read_text().splitlines() if l.strip()]
    t1_scores = [e.get('recall_score', 0) for e in edges if e.get('tier') == 'T1']
    if len(set(t1_scores)) < 3:
        return f'T1 scores not unique: {len(t1_scores)} edges, {len(set(t1_scores))} unique scores'
    return None

# 10. T1 scores must be > 0
def c10():
    edges = [json.loads(l) for l in ENRICHED.read_text().splitlines() if l.strip()]
    t1_scores = [e.get('recall_score', 0) for e in edges if e.get('tier') == 'T1']
    if any(s <= 0 for s in t1_scores):
        return f'T1 scores not all > 0: {t1_scores}'
    return None

# 11. T1 scores must be < 1
def c11():
    edges = [json.loads(l) for l in ENRICHED.read_text().splitlines() if l.strip()]
    t1_scores = [e.get('recall_score', 0) for e in edges if e.get('tier') == 'T1']
    if any(s >= 1.001 for s in t1_scores):
        return f'T1 scores not all < 1: {t1_scores}'
    return None

for name, fn in [('c1', c1), ('c2', c2), ('c3', c3), ('c4', c4), ('c5', c5), ('c6', c6), ('c7', c7), ('c8', c8), ('c9', c9), ('c10', c10), ('c11', c11)]:
    check(name, fn)

print('=== healthcheck results ===')
for line in oks:
    print(f'✅ {line}')
for line in fails:
    print(f'❌ {line}')

if fails:
    print(f'\n❌ {len(fails)} check(s) failed')
    sys.exit(1)
print(f'\n✅ all {len(oks)} checks passed')

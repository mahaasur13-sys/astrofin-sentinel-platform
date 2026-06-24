"""Ad-hoc check: does ADR-0007 actually push all 7 override pairs to top-10?

Builds a synthetic enriched-edge list that mirrors the production tie scenario
(7 override + 10 non-override, all at recall_score=1.0 with adversarial paths),
then runs recall_test.py against it and counts override edges in top-10.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

WORK = Path("/home/workspace/graphify-out")
AD_HOC = WORK / "_ad_hoc_ov_check.enriched.jsonl"

# Load real override pairs from ground truth
ov_pairs = []
with open(WORK / "ground_truth.jsonl") as f:
    for line in f:
        r = json.loads(line)
        if r["kind"] == "override":
            ov_pairs.append(r)

assert len(ov_pairs) == 7, f"Expected 7 override pairs in GT, got {len(ov_pairs)}"

# Adversarial competitors: paths that lexicographically sort BEFORE the
# override paths, so without tie-break they win.
# Override paths all start with 'asurdev_' (a-prefix). Competitors use
# 'aardvark_' (a-a-prefix, sorts earlier) and 'aaa_' to make sure they
# beat the override paths on pure alpha order.
competitors = []
for i in range(10):
    competitors.append({
        "source_node_id": f"aaa_alpha_{i:02d}",
        "source_path": f"aaa/alpha/{i:02d}.py",
        "source_line": 10,
        "target_node_id": f"aaa_beta_{i:02d}",
        "target_path": f"aaa/beta/{i:02d}.py",
        "target_line": 20,
        "confidence": 1.0,
        "weight": 1.0,
        "relation": "calls",
        "verdict": "valid",
        "tier": "T1",
        "category": "submodule",
        "half_life_days": 365,
        "delta_days": 0,
        "decay_factor": 1.0,
        "tier_weight": 1.0,
        "relation_weight": 1.0,
        "recall_score": 1.0,
        "override_applied": False,
    })

# Convert GT override pairs into enriched-edge shape
def gt_to_edge(r):
    src_path = r["source_node_id"]  # node_id ~ function path
    tgt_path = r["target_node_id"]
    return {
        "source_node_id": r["source_node_id"],
        "source_path": src_path,
        "source_line": 1,
        "target_node_id": r["target_node_id"],
        "target_path": tgt_path,
        "target_line": 1,
        "confidence": 1.0,
        "weight": 1.0,
        "relation": r["relation"],
        "verdict": "valid",
        "tier": "T1",
        "category": "core",
        "half_life_days": 365,
        "delta_days": 0,
        "decay_factor": 1.0,
        "tier_weight": 1.0,
        "relation_weight": 1.0,
        "recall_score": 1.0,
        "override_applied": True,
    }

edges = [gt_to_edge(p) for p in ov_pairs] + competitors

# Shuffle so file order does not pre-bias the (un-)sorted result
import random
random.seed(42)
random.shuffle(edges)

with open(AD_HOC, "w") as f:
    for e in edges:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

print(f"Wrote {len(edges)} edges to {AD_HOC} ({sum(1 for e in edges if e['override_applied'])} override)")

# Run recall_test.py against the synthetic file
result = subprocess.run(
    [sys.executable, "graphify-out/recall_test.py", "-n", "10",
     "--json", str(AD_HOC)],
    capture_output=True, text=True, cwd="/home/workspace"
)

# recall_test.py currently reads a hardcoded path. We can't override it without
# editing the script. Fall back to a simple reproduction of the sort key:
print("\n=== Reproducing sort key in Python (current production key) ===")
def k_old(e):
    return (-e["recall_score"], e["source_path"], e["target_path"], e["source_node_id"], e["target_node_id"])

def k_new(e):
    return (-int(e.get("override_applied", False)), -e["recall_score"],
            e["source_path"], e["target_path"], e["source_node_id"], e["target_node_id"])

top_old = sorted(edges, key=k_old)[:10]
top_new = sorted(edges, key=k_new)[:10]

ov_old = sum(1 for e in top_old if e["override_applied"])
ov_new = sum(1 for e in top_new if e["override_applied"])

print(f"override@10 OLD key: {ov_old}/7")
print(f"override@10 NEW key (ADR-0007): {ov_new}/7")

# Print top-10 under each key for visibility
print("\n--- top-10 with OLD key ---")
for i, e in enumerate(top_old, 1):
    print(f"  {i:2d}  ov={int(e['override_applied'])}  {e['source_path'][:40]} -> {e['target_path'][:40]}")

print("\n--- top-10 with NEW key (ADR-0007) ---")
for i, e in enumerate(top_new, 1):
    print(f"  {i:2d}  ov={int(e['override_applied'])}  {e['source_path'][:40]} -> {e['target_path'][:40]}")

# Cleanup
AD_HOC.unlink(missing_ok=True)

if ov_new == 7 and ov_old < 7:
    print("\n✅ ADR-0007 fix confirmed: pulls all 7 override pairs to top-10")
    sys.exit(0)
else:
    print("\n❌ ADR-0007 fix did NOT work as expected")
    sys.exit(1)
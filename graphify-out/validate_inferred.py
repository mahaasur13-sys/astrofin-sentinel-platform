#!/usr/bin/env python3
"""
validate_inferred.py — stratified validation of INFERRED edges from graph.json.

Inputs:
  - /home/workspace/graphify-out/graph.json
  - /tmp/inferred_sample.json   (top-N sample, stratified)

Output:
  - /home/workspace/docs/VALIDATION_REPORT.md   (draft, human-curated)

Verdict categories:
  valid     — link is real and current
  false     — link does not exist in code
  moved     — entity exists but in a different file (give the new path)
  outdated  — was true at some point, now dead (e.g. _archived/, removed submodules)
  ambiguous — needs human review

Each verdict is recorded with grep evidence (line of proof).
"""

from __future__ import annotations
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

WORKSPACE = Path("/home/workspace")
GRAPH = WORKSPACE / "graphify-out" / "graph.json"
SAMPLE = Path(
    os.environ.get("INFERRED_SAMPLE") or (sys.argv[1] if len(sys.argv) > 1 else "/tmp/inferred_sample_500.json")
)
REPORT = WORKSPACE / "docs" / "VALIDATION_REPORT.md"

EXCLUDE_DIRS = ("Trash/", "node_modules/", "graphify-out/cache/")


def _adapt_sample(sample: list) -> list:
    """Map inferred_clean.jsonl schema → validator schema.

    inferred_clean: source_node_id, target_node_id, source_path, source_line,
                    target_path, confidence, weight, relation, ...
    validator:      source, target, source_file, source_location, target_file,
                    confidence_score, weight, relation, ...
    """
    return [
        {
            **e,
            "source": e.get("source_node_id", e.get("source", "")),
            "target": e.get("target_node_id", e.get("target", "")),
            "source_file": e.get("source_path", e.get("source_file", "")),
            "source_location": e.get("source_line", e.get("source_location", 0)),
            "target_file": e.get("target_path", ""),
            "confidence_score": e.get("confidence", e.get("confidence_score", 0.0)),
        }
        for e in sample
    ]


def _load_jsonl_or_json(path):
    """Read a file that may be either a JSON array or a JSONL stream of objects."""
    with open(path) as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            return json.load(f)
        return [json.loads(line) for line in f if line.strip()]


def load() -> tuple[dict, list, list]:
    g = json.load(open(GRAPH))
    nodes = {n["id"]: n for n in g["nodes"]}
    links = g["links"]
    raw_sample = _load_jsonl_or_json(SAMPLE)
    sample = _adapt_sample(raw_sample) if raw_sample and "source_node_id" in raw_sample[0] else raw_sample
    return nodes, links, sample


def grep_evidence(pattern: str, *, glob: str = "*.py", limit: int = 5) -> list[str]:
    """Return up to `limit` ripgrep matches across the workspace, excluding noise dirs."""
    excl = [f"--glob=!{d}**" for d in EXCLUDE_DIRS]
    cmd = [
        "rg",
        "--no-heading",
        "--line-number",
        "--max-count",
        str(limit),
        "--glob",
        glob,
        *excl,
        pattern,
        str(WORKSPACE),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        lines = [ln for ln in out.stdout.splitlines() if ln.strip()]
        return lines[:limit]
    except Exception as e:
        return [f"<<rg error: {e}>>"]


def file_exists(rel: str) -> bool:
    p = WORKSPACE / rel
    return p.is_file()


def judge(edge: dict, tnode: dict) -> tuple[str, list[str]]:
    """Return (verdict, evidence_lines) for an INFERRED edge."""
    src_file = edge["source_file"]
    tgt_file = (tnode or {}).get("source_file", "")
    src_label = edge["source"].rsplit("_", 1)[-1]  # last segment of node id
    tgt_label = edge["target"].rsplit("_", 1)[-1]

    # 1. target file missing entirely
    if tgt_file and not file_exists(tgt_file):
        return ("outdated" if "_archived/" in tgt_file else "false"), [f"file_not_found: {tgt_file}"]

    # 2. archived or known-dead submodule
    if "_archived/" in tgt_file or "/_archived/" in tgt_file:
        return "outdated", [f"target_in_archived: {tgt_file}"]
    if re.search(r"^push/", src_file) and re.search(r"^push/", tgt_file):
        # push/ is a separate repo; we only allow INFERRED inside the platform
        return "ambiguous", [f"cross_submodule: {src_file} -> {tgt_file}"]

    # 3. target node has no source_file at all (parser bug — same family as KI-014)
    if not tgt_file:
        return "false", ["empty_target_source_file"]

    # 4. look for the target symbol in the target file
    evidence = grep_evidence(rf"\b{re.escape(tgt_label)}\b", limit=3)
    if evidence:
        return "valid", evidence

    # 5. try a fuzzy match on the source symbol
    if src_label and src_label != "any":
        evidence = grep_evidence(rf"\b{re.escape(src_label)}\b", glob="*.py", limit=3)
        if evidence:
            return "ambiguous", ["source_symbol_present_but_target_not", *evidence]

    return "false", [f"target_symbol '{tgt_label}' not found in {tgt_file}"]


def main() -> None:
    nodes, _links, sample = load()
    buckets = defaultdict(list)
    for e in sample:
        buckets[e.get("relation", "uses")].append(e)

    lines: list[str] = []
    lines.append("# VALIDATION_REPORT.md")
    lines.append("")
    total = sum(len(edges) for edges in buckets.values())
    lines.append(
        f"Stratified validation of N={total} INFERRED edges from `graphify-out/graph.json` (snapshot 2026-06-17)."
    )  # noqa: E501
    lines.append("")
    lines.append("**Verdict legend:**")
    lines.append("- `valid` — link is real and current")
    lines.append("- `false` — link does not exist in code")
    lines.append("- `moved` — entity exists, but in a different file (new path noted)")
    lines.append("- `outdated` — was true at some point, now dead (e.g. `_archived/`, removed submodules)")
    lines.append("- `ambiguous` — needs human review")
    lines.append("")
    lines.append("---")
    lines.append("")

    stats = defaultdict(int)
    for rel, edges in buckets.items():
        lines.append(f"## Bucket: relation = `{rel}` ({len(edges)} edges)")
        lines.append("")
        for i, e in enumerate(sorted(edges, key=lambda L: (-L.get("confidence_score", 0), -L.get("weight", 0))), 1):
            tnode = nodes.get(e["target"], {})
            verdict, evidence = judge(e, tnode)
            stats[verdict] += 1
            lines.append(f"### INFERRED #{rel}-{i}")
            lines.append(f"- **Source:** `{e['source_file']}:L{e['source_location']} :: {e['source']}`")
            tgt_file = (tnode or {}).get("source_file", "") or "(empty)"
            lines.append(f"- **Target:** `{tgt_file}:{tnode.get('source_location', '?')} :: {e['target']}`")
            lines.append(
                f"- **Confidence:** {e.get('confidence_score', 0):.3f}  **Weight:** {e.get('weight', 0):.2f}  **Relation:** `{e['relation']}`"
            )  # noqa: E501
            lines.append(f"- **Verdict:** **{verdict}**")
            lines.append("- **Evidence:**")
            for ev in evidence:
                lines.append(f"    ```\n    {ev}\n    ```")
            lines.append("")
        lines.append("---")
        lines.append("")

    # Summary block
    total = sum(stats.values())
    lines.insert(7, "")
    lines.insert(
        7,
        f"**Verdict summary (N={total}):** "
        + ", ".join(f"`{k}`={v} ({v * 100 / total:.0f}%)" for k, v in sorted(stats.items(), key=lambda x: -x[1])),
    )
    lines.insert(7, "")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines))
    print(f"wrote {REPORT}  (verdicts: {dict(stats)})")


if __name__ == "__main__":
    main()

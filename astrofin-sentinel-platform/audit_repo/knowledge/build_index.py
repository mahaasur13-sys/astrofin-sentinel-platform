#!/usr/bin/env python3
"""
Build FAISS index from knowledge chunks.
Usage:
    python build_index.py              # build all domains
    python build_index.py --domain astrology
    python build_index.py --domain all --rebuild
    python build_index.py --stats
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import faiss
import numpy as np

# ─── Ollama embeddings ────────────────────────────────────────────────────────

DIM = 768  # nomic-embed-text output dimension


def get_embedding(text: str, model: str = "nomic-embed-text") -> list[float]:
    import urllib.request

    payload = json.dumps({"model": model, "prompt": text}).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["embedding"]


# ─── Chunk loading ─────────────────────────────────────────────────────────────


def load_chunks(chunks_dir: Path) -> list[dict]:
    """Load all markdown files, split into semantic chunks."""
    chunks = []
    for md_file in sorted(chunks_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        domain = md_file.parent.name
        sections = re.split(r"\n(?=##\s)", content)
        current_title = md_file.stem
        for section in sections:
            lines = section.strip().split("\n")
            if lines[0].startswith("#"):
                current_title = lines[0].lstrip("# ").strip()
                body = "\n".join(lines[1:]).strip()
            else:
                body = section.strip()
            if not body or len(body) < 20:
                continue
            chunk_id = hashlib.md5(f"{md_file.name}#{current_title}".encode()).hexdigest()[:12]
            chunks.append(
                {
                    "id": chunk_id,
                    "content": body,
                    "source": str(md_file.relative_to(chunks_dir.parent)),
                    "title": current_title,
                    "domain": domain,
                }
            )
    return chunks


# ─── FAISS index building ─────────────────────────────────────────────────────


def build_index(chunks: list[dict], domain: str) -> tuple[faiss.Index, list[dict]]:
    """Build FAISS IndexFlatIP (cosine sim via normalized vectors)."""
    index = faiss.IndexFlatIP(DIM)
    vectors = []

    for chunk in chunks:
        emb = get_embedding(chunk["content"])
        vec = np.array(emb, dtype="float32")
        vec = vec / (np.linalg.norm(vec) + 1e-8)  # L2-normalize
        vectors.append(vec)

    vectors = np.vstack(vectors).astype("float32")
    index.add(vectors)
    return index, chunks


def save_index(index: faiss.Index, chunks: list[dict], index_path: Path, meta_path: Path):
    faiss.write_index(index, str(index_path))
    meta_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")


def load_index(index_path: Path, meta_path: Path) -> tuple[faiss.Index, list[dict]]:
    index = faiss.read_index(str(index_path))
    chunks = json.loads(meta_path.read_text(encoding="utf-8"))
    return index, chunks


# ─── CLI ───────────────────────────────────────────────────────────────────────


def cmd_build(args):
    kb_dir = Path(__file__).parent
    chunks_dir = kb_dir / "chunks"
    indexes_dir = kb_dir / "indexes"
    indexes_dir.mkdir(exist_ok=True)

    domain = args.domain
    if domain == "all":
        domains = ["astrology", "technical", "trading"]
    else:
        domains = [domain] if domain else ["astrology", "technical", "trading"]

    for d in domains:
        domain_chunks_dir = chunks_dir / d
        if not domain_chunks_dir.exists():
            print(f"⚠️  {domain_chunks_dir} does not exist, skipping {d}")
            continue

        index_path = indexes_dir / f"{d}.index"
        meta_path = indexes_dir / f"{d}.meta.json"

        if index_path.exists() and not args.rebuild:
            print(f"  {d}: index exists (use --rebuild to overwrite)")
            continue

        print(f"  {d}: loading chunks…")
        chunks = load_chunks(domain_chunks_dir)
        if not chunks:
            print(f"  ⚠️  {d}: no chunks found, skipping")
            continue
        print(f"  {d}: {len(chunks)} chunks, building index…")

        index, _ = build_index(chunks, d)
        save_index(index, chunks, index_path, meta_path)
        print(f"  ✅ {d}: {index.ntotal} vectors → {index_path}")


def cmd_stats(args):
    kb_dir = Path(__file__).parent
    indexes_dir = kb_dir / "indexes"

    print("\n📊 RAG Index Statistics")
    print("─" * 45)

    domains = ["astrology", "technical", "trading"]
    total = 0
    for d in domains:
        index_path = indexes_dir / f"{d}.index"
        meta_path = indexes_dir / f"{d}.meta.json"
        if not index_path.exists():
            print(f"  {d:12s}: ❌ no index")
            continue
        index = faiss.read_index(str(index_path))
        chunks = json.loads(meta_path.read_text(encoding="utf-8"))
        print(f"  {d:12s}: ✅ {index.ntotal:3d} chunks  ({', '.join(c['title'][:25] for c in chunks[:3])}…)")
        total += index.ntotal

    all_path = indexes_dir / "all.index"
    indexes_dir / "all.meta.json"
    if all_path.exists():
        index = faiss.read_index(str(all_path))
        print(f"  {'all':12s}: ✅ {index.ntotal:3d} chunks (combined)")

    print(f"\n  Total: {total} chunks indexed")
    if total == 0:
        print("  Run: python build_index.py --rebuild")


def cmd_search(args):
    kb_dir = Path(__file__).parent
    indexes_dir = kb_dir / "indexes"

    domain = args.domain or "astrology"
    index_path = indexes_dir / f"{domain}.index"
    meta_path = indexes_dir / f"{domain}.meta.json"

    if not index_path.exists():
        print(f"❌ No index for domain '{domain}'. Run: python build_index.py --domain {domain}")
        sys.exit(1)

    index, chunks = load_index(index_path, meta_path)
    query_vec = get_embedding(args.query)
    q = np.array([query_vec], dtype="float32")
    q = q / (np.linalg.norm(q) + 1e-8)

    k = min(args.top_k, index.ntotal)
    scores, indices = index.search(q, k)

    print(f"\n🔍 Top-{k} results for: «{args.query}» [{domain}]\n")
    for score, idx in zip(scores[0], indices[0], strict=False):
        if idx < 0:
            continue
        c = chunks[idx]
        print(f"  [{score:.3f}] {c['source']} → {c['title']}")
        print(f"         {c['content'][:150]}…")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AstroFin Sentinel RAG Index Builder")
    sub = parser.add_subparsers(dest="cmd")

    p_build = sub.add_parser("build", help="Build FAISS index")
    p_build.add_argument("--domain", default="all", choices=["astrology", "technical", "trading", "all"])
    p_build.add_argument("--rebuild", action="store_true", help="Force rebuild even if index exists")

    p_stats = sub.add_parser("stats", help="Show index statistics")

    p_search = sub.add_parser("search", help="Test search")
    p_search.add_argument("query")
    p_search.add_argument("--domain", default="astrology")
    p_search.add_argument("--top-k", type=int, default=3)

    args = parser.parse_args(sys.argv[1:] if len(sys.argv) > 1 else ["build"])

    cmd = args.cmd or "build"
    if cmd == "build":
        cmd_build(args)
    elif cmd == "stats":
        cmd_stats(args)
    elif cmd == "search":
        cmd_search(args)

"""
tools/migrate_faiss_to_pgvector.py — Migrate FAISS knowledge base to pgvector.

Reads existing knowledge/indexes/<domain>.index + <domain>.meta.json,
re-embeds every chunk at 1536-dim via OpenAI text-embedding-3-small,
inserts rows into Postgres `documents` table.

Usage:
    export AFS_PG_DSN="postgresql://astrofin:<pass>@localhost:5432/astrofin"
    export OPENAI_API_KEY="sk-..."
    python tools/migrate_faiss_to_pgvector.py --domain all
    python tools/migrate_faiss_to_pgvector.py --domain astrology
    python tools/migrate_faiss_to_pgvector.py --dry-run

Notes:
    - This script is the W3A deliverable (SPRINT_3.md, P2-02, days 1-2).
    - Original FAISS indexes are NOT deleted; they remain the read-only
      fallback until P3-04 cutover (Sprint W5).
    - Re-embedding is mandatory: 768-dim nomic → 1536-dim OpenAI is not a
      linear transform, so we must call the embedder on each chunk's text.
    - Cost: ~$0.02 per 1M tokens. 6 chunks × ~500 tokens = ~$0.00006 (free).
    - Idempotency: ON CONFLICT (chunk_id) DO NOTHING.

Sprint: W3 / P2-02 (2026-07-04)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import AsyncIterator

import asyncpg
import faiss
import numpy as np
import urllib.request


# ─── Config ───────────────────────────────────────────────────────────────────

PG_DSN_ENV = "AFS_PG_DSN"
OPENAI_KEY_ENV = "OPENAI_API_KEY"
OPENAI_URL = "https://api.openai.com/v1/embeddings"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
BATCH_SIZE = 32  # chunks per OpenAI call (max 2048 inputs but keep small for latency)


def _embed_openai(texts: list[str], api_key: str) -> list[list[float]]:
    """Call OpenAI embeddings API in batch. Returns list of 1536-dim vectors."""
    payload = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
    req = urllib.request.Request(
        OPENAI_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return [d["embedding"] for d in data["data"]]


def _embed_query(text: str) -> list[float]:
    """Single-text embedder for verification / smoke tests."""
    return _embed_openai([text], os.environ[OPENAI_KEY_ENV])[0]


# ─── FAISS reading ────────────────────────────────────────────────────────────


def load_faiss_index(domain: str, kb_dir: Path) -> tuple[faiss.Index | None, list[dict]]:
    """Read <domain>.index + <domain>.meta.json. Returns (None, []) if absent."""
    index_path = kb_dir / "indexes" / f"{domain}.index"
    meta_path = kb_dir / "indexes" / f"{domain}.meta.json"
    if not index_path.exists() or not meta_path.exists():
        return None, []
    index = faiss.read_index(str(index_path))
    chunks = json.loads(meta_path.read_text(encoding="utf-8"))
    return index, chunks


# ─── Postgres writing ────────────────────────────────────────────────────────


INSERT_SQL = """
INSERT INTO documents (chunk_id, domain, source, title, content, embedding, indexed_at)
VALUES ($1, $2, $3, $4, $5, $6::vector, $7)
ON CONFLICT (chunk_id) DO NOTHING
"""


async def _connect_pg(dsn: str) -> asyncpg.Connection:
    return await asyncpg.connect(dsn)


async def _migrate_domain(
    conn: asyncpg.Connection,
    domain: str,
    chunks: list[dict],
    api_key: str,
    dry_run: bool,
) -> int:
    """Migrate one domain. Returns number of rows inserted."""
    if not chunks:
        return 0

    indexed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    inserted = 0

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["content"] for c in batch]
        if dry_run:
            # Skip API call in dry-run; pretend it would succeed.
            vectors = [[0.0] * EMBED_DIM for _ in batch]
        else:
            vectors = _embed_openai(texts, api_key)

        for chunk, vec in zip(batch, vectors, strict=True):
            if dry_run:
                inserted += 1
                continue
            # pgvector accepts a string "[v1,v2,...,vN]" cast to ::vector.
            vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
            result = await conn.execute(
                INSERT_SQL,
                chunk["id"],
                domain,
                chunk["source"],
                chunk["title"],
                chunk["content"],
                vec_str,
                indexed_at,
            )
            # asyncpg returns "INSERT 0 1" on insert, "INSERT 0 0" on conflict.
            if result.endswith(" 1"):
                inserted += 1

        sys.stdout.write(
            f"\r  [{domain}] {i + len(batch)}/{len(chunks)} chunks processed ({inserted} inserted)"
        )
        sys.stdout.flush()
    print()
    return inserted


# ─── CLI ─────────────────────────────────────────────────────────────────────


async def main(args: argparse.Namespace) -> int:
    dsn = os.environ.get(PG_DSN_ENV)
    if not dsn and not args.dry_run:
        print(f"❌ {PG_DSN_ENV} env var is required (or use --dry-run)", file=sys.stderr)
        return 2

    api_key = os.environ.get(OPENAI_KEY_ENV)
    if not api_key and not args.dry_run:
        print(f"❌ {OPENAI_KEY_ENV} env var is required (or use --dry-run)", file=sys.stderr)
        return 2

    kb_dir = Path(__file__).resolve().parent.parent / "knowledge"
    if not kb_dir.exists():
        print(f"❌ knowledge/ dir not found at {kb_dir}", file=sys.stderr)
        return 1

    domains = ["astrology", "technical", "trading"] if args.domain == "all" else [args.domain]
    total_inserted = 0

    if args.dry_run:
        print("🟡 DRY-RUN: skipping Postgres writes and OpenAI calls\n")

    conn = None if args.dry_run else await _connect_pg(dsn)
    try:
        for domain in domains:
            index, chunks = load_faiss_index(domain, kb_dir)
            if index is None:
                print(f"  ⚠️  {domain}: no FAISS index, skipping")
                continue
            assert index.ntotal == len(chunks), (
                f"FAISS/JSON mismatch in {domain}: index.ntotal={index.ntotal} vs {len(chunks)} chunks"
            )
            print(f"  → {domain}: {len(chunks)} chunks (FAISS dim={index.d})")
            inserted = await _migrate_domain(conn, domain, chunks, api_key or "", args.dry_run)
            total_inserted += inserted
            print(f"  ✅ {domain}: {inserted} new rows in pgvector")
    finally:
        if conn is not None:
            await conn.close()

    print(f"\n🏁 Total: {total_inserted} chunks {'(dry-run)' if args.dry_run else 'inserted'}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate FAISS KB → pgvector")
    parser.add_argument(
        "--domain",
        default="all",
        choices=["all", "astrology", "technical", "trading"],
        help="Domain to migrate (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip OpenAI + Postgres; print what would be done",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sys.exit(asyncio.run(main(args)))

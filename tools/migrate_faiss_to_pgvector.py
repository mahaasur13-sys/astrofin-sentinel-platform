"""
tools/migrate_faiss_to_pgvector.py — Migrate FAISS knowledge base to pgvector.

Reads existing knowledge/indexes/<domain>.index + <domain>.meta.json,
embeds every chunk at 1536-dim (default: deterministic stub; OpenAI optional),
inserts rows into Postgres `documents` table.

Usage:
   export AFS_PG_DSN="postgresql://astrofin:<pass>@localhost:5432/astrofin"
   python tools/migrate_faiss_to_pgvector.py --domain all                # stub embedder (default)
   python tools/migrate_faiss_to_pgvector.py --use-openai --domain astrology
   python tools/migrate_faiss_to_pgvector.py --dry-run

Notes:
   - This script is the W3A deliverable (SPRINT_3.md, P2-02, days 1-2).
   - Original FAISS indexes are NOT deleted; they remain the read-only
     fallback until P3-04 cutover (Sprint W5).
   - --use-stub-embeddings (default ON) uses the deterministic local stub.
   - --use-openai switches to OpenAI text-embedding-3-small (needs OPENAI_API_KEY).
   - Idempotency: ON CONFLICT (chunk_id) DO NOTHING.

Sprint: W3 / P2-02 (2026-07-04)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.request
from pathlib import Path

import asyncpg
import faiss

import logging
log = logging.getLogger(__name__)


# Lazy import of EmbeddingClient — keep it after Path is available
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from tools.embedding_client import EmbeddingClient, EmbeddingConfig  # noqa: E402

# ─── Config ───────────────────────────────────────────────────────────────────

PG_DSN_ENV = "AFS_PG_DSN"
OPENAI_KEY_ENV = "OPENAI_API_KEY"
OPENAI_URL = "https://api.openai.com/v1/embeddings"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
BATCH_SIZE = 32


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
    # nosec B310: hard-coded ollama localhost health check

    # nosec B310: hard-coded embedding API endpoint from config

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return [d["embedding"] for d in data["data"]]


# ─── FAISS reading ────────────────────────────────────────────────────────────


def load_faiss_index(
    domain: str, kb_dir: Path
) -> tuple[faiss.Index | None, list[dict]]:
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
INSERT INTO documents
    (doc_id, source, source_type, title, body, tokens, lang, domain, metadata, embedding)
VALUES
    (COALESCE($1, gen_random_uuid()), $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::vector)
ON CONFLICT (doc_id) DO NOTHING
"""


async def _connect_pg(dsn: str) -> asyncpg.Connection:
    return await asyncpg.connect(dsn)


async def _migrate_domain(
    conn: asyncpg.Connection,
    domain: str,
    chunks: list[dict],
    api_key: str,
    dry_run: bool,
    use_stub: bool = False,
    embedder: EmbeddingClient | None = None,
) -> int:
    """Migrate one domain. Returns number of rows inserted."""
    if not chunks:
        return 0

    inserted = 0

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["content"] for c in batch]
        if dry_run:
            vectors = [[0.0] * EMBED_DIM for _ in batch]
        elif use_stub:
            assert embedder is not None, "use_stub=True requires embedder"
            vectors = await embedder.embed(texts)
        else:
            vectors = _embed_openai(texts, api_key)

        for chunk, vec in zip(batch, vectors, strict=True):
            if dry_run:
                inserted += 1
                continue
            vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
            metadata = json.dumps(
                {
                    "domain": domain,
                    "chunk_id": chunk.get("id"),
                    "title": chunk.get("title"),
                }
            )
            tokens = max(len(chunk["content"].split()), 1)
            result = await conn.execute(
                INSERT_SQL,
                chunk.get("id"),
                chunk.get("source", "unknown"),
                "report",
                chunk.get("title") or "",
                chunk["content"],
                tokens,
                "en",
                domain,
                metadata,
                vec_str,
            )
            if "INSERT 0 1" in result:
                inserted += 1

        sys.stdout.write(
            f"\r  [{domain}] {i + len(batch)}/{len(chunks)} chunks processed ({inserted} inserted)"
        )
        sys.stdout.flush()
    log.info("")
    return inserted


# ─── CLI ─────────────────────────────────────────────────────────────────────


async def main(args: argparse.Namespace) -> int:
    dsn = os.environ.get(PG_DSN_ENV)
    if not dsn and not args.dry_run:
        log.info(
            f"❌ {PG_DSN_ENV} env var is required (or use --dry-run)", file=sys.stderr
        )
        return 2

    api_key = os.environ.get(OPENAI_KEY_ENV)
    if not api_key and not args.dry_run and not args.use_stub_embeddings:
        log.info(
            f"❌ {OPENAI_KEY_ENV} env var is required "
            "(or use --dry-run / --use-stub-embeddings)",
            file=sys.stderr,
        )
        return 2

    kb_dir = _REPO_ROOT / "knowledge"
    if not kb_dir.exists():
        log.info(f"❌ knowledge/ dir not found at {kb_dir}", file=sys.stderr)
        return 1

    domains = (
        ["astrology", "technical", "trading"] if args.domain == "all" else [args.domain]
    )
    total_inserted = 0

    if args.dry_run:
        log.info("🟡 DRY-RUN: skipping Postgres writes and embedder calls\n")

    embedder: EmbeddingClient | None = None
    if args.use_stub_embeddings and not args.dry_run:
        embedder = EmbeddingClient(EmbeddingConfig(provider="stub", dimension=1536))

    conn = None if args.dry_run else await _connect_pg(dsn)
    try:
        for domain in domains:
            index, chunks = load_faiss_index(domain, kb_dir)
            if index is None:
                log.info(f"  ⚠  {domain}: no FAISS index, skipping")
                continue
            assert index.ntotal == len(chunks), (
                f"FAISS/JSON mismatch in {domain}: "
                f"index.ntotal={index.ntotal} vs {len(chunks)} chunks"
            )
            log.info(f"  → {domain}: {len(chunks)} chunks (FAISS dim={index.d})")
            inserted = await _migrate_domain(
                conn,
                domain,
                chunks,
                api_key or "",
                args.dry_run,
                use_stub=args.use_stub_embeddings,
                embedder=embedder,
            )
            total_inserted += inserted
            log.info(f"  ✅ {domain}: {inserted} new rows in pgvector")
    finally:
        if conn is not None:
            await conn.close()

    suffix = "(dry-run)" if args.dry_run else "inserted"
    log.info(f"\n🏁 Total: {total_inserted} chunks {suffix}")
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
        help="Skip embedder + Postgres; print what would be done",
    )
    parser.add_argument(
        "--use-stub-embeddings",
        action="store_true",
        default=True,
        help="Use deterministic stub embedder (default ON; dev/CI; no network).",
    )
    parser.add_argument(
        "--use-openai",
        dest="use_stub_embeddings",
        action="store_false",
        help="Use OpenAI text-embedding-3-small (requires OPENAI_API_KEY).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sys.exit(asyncio.run(main(args)))

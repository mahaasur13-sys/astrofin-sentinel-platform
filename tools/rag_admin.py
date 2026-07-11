"""
tools/rag_admin.py — Admin CLI for the RAG system.

Flat-command structure (no subcommands). Examples:

    python -m tools.rag_admin health
    python -m tools.rag_admin stats
    python -m tools.rag_admin retrieve "BTC volatility" --top-k 5 --min-score 0.3
    python -m tools.rag_admin list-domains
    python -m tools.rag_admin migrate-status
    python -m tools.rag_admin reindex-faiss --domain trading

Dependencies: argparse (stdlib only), project modules.

Exit codes:
    0 = success
    1 = runtime error (RAG not healthy, domain not found, etc.)
    2 = config error (bad args, missing DSN, etc.)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root on sys.path so `core.rag_client` resolves when run as script
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.rag_client import (  # noqa: E402
    Document,
    HealthStatus,
    RAGClient,
    RAGConfig,
    RetrievedChunk,
    StoreResult,
)


# ─── ANSI colors (no external deps) ──────────────────────────────────────────


class C:
    """ANSI color codes. Auto-disabled when stdout is not a TTY."""

    USE = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

    @classmethod
    def wrap(cls, code: str, s: str) -> str:
        return f"\033[{code}m{s}\033[0m" if cls.USE else s

    @classmethod
    def red(cls, s: str) -> str:
        return cls.wrap("31", s)

    @classmethod
    def green(cls, s: str) -> str:
        return cls.wrap("32", s)

    @classmethod
    def yellow(cls, s: str) -> str:
        return cls.wrap("33", s)

    @classmethod
    def blue(cls, s: str) -> str:
        return cls.wrap("34", s)

    @classmethod
    def bold(cls, s: str) -> str:
        return cls.wrap("1", s)

    @classmethod
    def dim(cls, s: str) -> str:
        return cls.wrap("2", s)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Render a simple table. No box-drawing — pipes + dashes only."""
    if not rows:
        print(C.dim("  (no data)"))
        return
    widths = [max(len(h), max((len(r[i]) for r in rows), default=0)) for i, h in enumerate(headers)]
    print("  " + " | ".join(C.bold(h.ljust(w)) for h, w in zip(headers, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in rows:
        print("  " + " | ".join(cell.ljust(w) for cell, w in zip(row, widths)))


def _ok(msg: str) -> None:
    print(f"  {C.green('✓')} {msg}")


def _warn(msg: str) -> None:
    print(f"  {C.yellow('!')} {msg}")


def _err(msg: str) -> None:
    print(f"  {C.red('✗')} {msg}", file=sys.stderr)


def _header(title: str) -> None:
    print()
    print(C.bold(C.blue(title)))
    print(C.dim("  " + "─" * (len(title) + 2)))


async def _get_client(args: argparse.Namespace) -> RAGClient:
    """Build RAGClient from CLI args.

    Always start from from_env() (which handles AFS_PG_DSN→faiss fallback),
    then apply explicit CLI overrides on top.
    """
    config = RAGConfig.from_env()
    if args.backend:
        config.backend = args.backend
    if args.legacy_fallback is not None:
        config.legacy_fallback = args.legacy_fallback
    if args.faiss_dir:
        config.faiss_dir = args.faiss_dir
    if args.min_score is not None:
        config.min_score = args.min_score

    client = RAGClient(config)
    # Force-load embedding client to fail fast if API key missing
    _ = client.embedding
    return client


def _format_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f}TB"


# ─── Commands ────────────────────────────────────────────────────────────────


async def cmd_health(args: argparse.Namespace) -> int:
    """Print RAGClient health status."""
    _header("RAG health")
    try:
        client = await _get_client(args)
    except Exception as e:  # noqa: BLE001
        _err(f"failed to construct client: {e}")
        return 2
    try:
        h: HealthStatus = await client.health()
    except Exception as e:  # noqa: BLE001
        _err(f"health() raised: {e}")
        await client.aclose()
        return 1

    status = C.green("healthy") if h.healthy else C.red("unhealthy")
    legacy = C.green("yes") if h.legacy_available else C.dim("no")
    print(f"  backend            : {C.bold(h.backend)}")
    print(f"  status             : {status}")
    print(f"  legacy fallback    : {legacy}")
    if h.details:
        print("  details:")
        for k, v in sorted(h.details.items()):
            print(f"    {C.dim(k)}: {v}")
    await client.aclose()
    return 0 if h.healthy else 1


async def cmd_stats(args: argparse.Namespace) -> int:
    """Print per-domain chunk counts, index sizes, cache hit rate."""
    _header("RAG stats")
    try:
        client = await _get_client(args)
    except Exception as e:  # noqa: BLE001
        _err(f"failed to construct client: {e}")
        return 2

    try:
        # FAISS: enumerate files in faiss_dir
        from pathlib import Path
        faiss_dir = Path(client.config.faiss_dir)
        if not faiss_dir.exists():
            _warn(f"FAISS dir does not exist: {faiss_dir}")
            domains_faiss = {}
        else:
            domains_faiss: dict[str, dict[str, Any]] = {}
            for idx_path in sorted(faiss_dir.glob("*.index")):
                meta_path = idx_path.with_suffix(".meta.json")
                size = idx_path.stat().st_size
                n = 0
                if meta_path.exists():
                    import json
                    try:
                        n = len(json.loads(meta_path.read_text(encoding="utf-8")))
                    except Exception:  # noqa: BLE001
                        pass
                domains_faiss[idx_path.stem] = {"chunks": n, "size": size}

        # pgvector: best-effort count
        pg_total: int | None = None
        pg_table = "documents"  # match migration 0009
        try:
            await client._get_pg_pool()
        except Exception as e:  # noqa: BLE001
            _warn(f"pgvector pool init failed: {e}")
        if client._pg_pool is not None:
            try:
                async with client._pg_pool.acquire() as conn:
                    pg_total = await conn.fetchval(f"SELECT COUNT(*) FROM {pg_table}")
            except Exception as e:  # noqa: BLE001
                _warn(f"pgvector count failed: {e}")

        # Query rate (P2-04: read from labeled RAG_QUERIES_TOTAL).
        try:
            from tools.metrics_server import RAG_QUERIES_TOTAL
            from prometheus_client import REGISTRY

            hits = 0
            misses = 0
            for metric in REGISTRY.collect():
                if metric.name != "astrofin_rag_queries_total":
                    continue
                for sample in metric.samples:
                    if sample.name != "astrofin_rag_queries_total":
                        continue
                    labels = sample.labels
                    if labels.get("status") == "ok":
                        hits += int(sample.value)
                    elif labels.get("status") == "error":
                        misses += int(sample.value)
            total = hits + misses
            rate = (hits / total * 100) if total > 0 else 0.0
        except Exception:  # noqa: BLE001
            hits = misses = 0
            rate = 0.0

        _header("FAISS (legacy)")
        if domains_faiss:
            rows = [
                [d, str(v["chunks"]), _format_size(v["size"])]
                for d, v in sorted(domains_faiss.items())
            ]
            _print_table(["domain", "chunks", "size"], rows)
        else:
            _warn("no FAISS indexes found")

        _header("pgvector (primary)")
        print(f"  table: {pg_table}")
        if pg_total is not None:
            print(f"  total rows: {C.bold(str(pg_total))}")
        else:
            _warn("not connected (no pool)")

        _header("Query cache")
        print(f"  hits   : {hits}")
        print(f"  misses : {misses}")
        print(f"  hit rate: {C.bold(f'{rate:.1f}%')}")
    finally:
        await client.aclose()
    return 0


async def cmd_retrieve(args: argparse.Namespace) -> int:
    """Manual search — useful for debugging."""
    _header(f"Retrieve: {args.query!r}")
    try:
        client = await _get_client(args)
    except Exception as e:  # noqa: BLE001
        _err(f"failed to construct client: {e}")
        return 2

    try:
        # Force FAISS-only if requested
        if args.backend == "faiss" and not args.legacy_fallback:
            # Bypass pgvector temporarily
            client.config.backend = "faiss"
        t0 = time.perf_counter()
        results: list[RetrievedChunk] = await client.retrieve(
            args.query, top_k=args.top_k, min_score=args.min_score, domain=args.domain
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
    except Exception as e:  # noqa: BLE001
        import traceback
        tb = traceback.format_exc()
        _err(f"retrieve() raised: {e!r}\n{tb}")
        await client.aclose()
        return 1

    print(f"  {len(results)} results in {elapsed_ms:.1f}ms (min_score={args.min_score})")
    if not results:
        _warn("no results")
    else:
        rows = []
        for i, r in enumerate(results, 1):
            content = r.content[:60].replace("\n", " ")
            if len(r.content) > 60:
                content += "…"
            score_color = (
                C.green(f"{r.relevance_score:.3f}")
                if r.relevance_score >= 0.7
                else C.yellow(f"{r.relevance_score:.3f}")
                if r.relevance_score >= 0.4
                else C.red(f"{r.relevance_score:.3f}")
            )
            rows.append([str(i), r.domain, r.source, score_color, content])
        _print_table(["#", "domain", "source", "score", "content"], rows)
    await client.aclose()
    return 0


async def cmd_list_domains(args: argparse.Namespace) -> int:
    """List all known domains (FAISS + pgvector union)."""
    _header("Domains")
    try:
        client = await _get_client(args)
    except Exception as e:  # noqa: BLE001
        _err(f"failed to construct client: {e}")
        return 2
    try:
        domains: set[str] = set()

        # FAISS
        faiss_dir = Path(client.config.faiss_dir)
        if faiss_dir.exists():
            for p in faiss_dir.glob("*.index"):
                domains.add(p.stem)

        # pgvector — _pg_pool is lazy; force-init before checking.
        if client.config.backend == "pgvector":
            try:
                await client._get_pg_pool()
            except Exception as e:  # noqa: BLE001
                _warn(f"pgvector init failed: {e}")
        if client._pg_pool is not None:
            try:
                async with client._pg_pool.acquire() as conn:
                    rows = await conn.fetch("SELECT DISTINCT metadata->>'domain' AS domain FROM documents")
                    for row in rows:
                        domains.add(row["domain"])
            except Exception as e:  # noqa: BLE001
                _warn(f"pgvector list failed: {e}")

        if not domains:
            _warn("no domains found")
            return 0

        for d in sorted(domains):
            print(f"  • {C.bold(d)}")
        print()
        print(C.dim(f"  {len(domains)} domain(s)"))
    finally:
        await client.aclose()
    return 0


async def cmd_migrate_status(args: argparse.Namespace) -> int:
    """Compare FAISS counts vs pgvector counts per domain."""
    _header("Migration status (FAISS ↔ pgvector)")
    try:
        client = await _get_client(args)
    except Exception as e:  # noqa: BLE001
        _err(f"failed to construct client: {e}")
        return 2

    try:
        import json
        from pathlib import Path

        # FAISS side
        faiss_counts: dict[str, int] = {}
        faiss_dir = Path(client.config.faiss_dir)
        if faiss_dir.exists():
            for idx_path in faiss_dir.glob("*.index"):
                meta_path = idx_path.with_suffix(".meta.json")
                if meta_path.exists():
                    try:
                        faiss_counts[idx_path.stem] = len(json.loads(meta_path.read_text(encoding="utf-8")))
                    except Exception:  # noqa: BLE001
                        faiss_counts[idx_path.stem] = -1
                else:
                    faiss_counts[idx_path.stem] = -1

        # pgvector side — _pg_pool is lazy; force-init before checking.
        pg_counts: dict[str, int] = {}
        if client.config.backend == "pgvector":
            try:
                await client._get_pg_pool()
            except Exception as e:  # noqa: BLE001
                _warn(f"pgvector init failed: {e}")
        if client._pg_pool is not None:
            try:
                async with client._pg_pool.acquire() as conn:
                    rows = await conn.fetch(
                        "SELECT metadata->>'domain' AS domain, "
                        "COUNT(*) AS n "
                        "FROM documents GROUP BY metadata->>'domain'"
                    )
                    for row in rows:
                        pg_counts[row["domain"]] = row["n"]
            except Exception as e:  # noqa: BLE001
                _warn(f"pgvector query failed: {e}")

        all_domains = sorted(set(faiss_counts) | set(pg_counts))
        if not all_domains:
            _warn("no data in either backend")
            return 0

        rows = []
        for d in all_domains:
            faiss_n = faiss_counts.get(d, 0)
            pg_n = pg_counts.get(d, 0)
            delta = pg_n - faiss_n
            if faiss_n == 0 and pg_n == 0:
                status = C.dim("—")
            elif faiss_n == 0:
                status = C.blue("pg-only")
            elif pg_n == 0:
                status = C.yellow("faiss-only")
            elif faiss_n == pg_n:
                status = C.green("synced")
            else:
                status = C.yellow(f"Δ {delta:+d}")
            rows.append([d, str(faiss_n), str(pg_n), status])

        _print_table(["domain", "faiss", "pgvector", "status"], rows)
    finally:
        await client.aclose()
    return 0


async def cmd_reindex_faiss(args: argparse.Namespace) -> int:
    """Rebuild a FAISS index for one domain (drop and re-create from pgvector)."""
    _header(f"Reindex FAISS: {args.domain}")
    try:
        client = await _get_client(args)
    except Exception as e:  # noqa: BLE001
        _err(f"failed to construct client: {e}")
        return 2

    if client.config.backend != "faiss":
        # Need to query pgvector
        if client._pg_pool is None:
            _err("rebuild requires pgvector connection (no AFS_PG_DSN set?)")
            return 1
        try:
            client.config.backend = "pgvector"
        except Exception as e:  # noqa: BLE001
            _err(f"backend switch failed: {e}")
            return 2

    try:
        # Fetch all docs for the domain from pgvector
        async with client._pg_pool.acquire() as conn:  # type: ignore[union-attr]
            rows = await conn.fetch(
                "SELECT doc_id, content, source, title, domain "
                "FROM documents WHERE domain = $1",
                args.domain,
            )
        if not rows:
            _warn(f"no rows in pgvector for domain {args.domain!r}")
            return 1
        docs = [
            Document(
                doc_id=row["doc_id"],
                content=row["content"],
                source=row["source"],
                title=row["title"] or "",
                domain=row["domain"],
            )
            for row in rows
        ]
        # Remove old FAISS files
        faiss_dir = Path(client.config.faiss_dir)
        faiss_dir.mkdir(parents=True, exist_ok=True)
        for ext in (".index", ".meta.json"):
            p = faiss_dir / f"{args.domain}{ext}"
            if p.exists():
                p.unlink()
                _ok(f"removed {p.name}")
        # Force FAISS write
        old_backend = client.config.backend
        client.config.backend = "faiss"
        try:
            result: StoreResult = await client.store(docs)
        finally:
            client.config.backend = old_backend
        _ok(f"reindexed {result.inserted} chunks ({result.failed} failed)")
        return 0
    except Exception as e:  # noqa: BLE001
        _err(f"reindex failed: {e}")
        return 1
    finally:
        await client.aclose()


# ─── Argparse wiring ────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rag_admin",
        description="Admin CLI for the RAG system (Sprint W3).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options (added to every subparser below)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--backend", default=None,
        help="override RAG backend (default: from RAG_BACKEND env or pgvector)",
    )
    common.add_argument(
        "--legacy-fallback", type=lambda v: v.lower() in ("1", "true", "yes"),
        default=None, help="enable/disable FAISS fallback when pgvector is down",
    )
    common.add_argument(
        "--faiss-dir", default=None, help="override FAISS index directory",
    )
    common.add_argument(
        "--min-score", type=float, default=None,
        help="minimum relevance score for retrieved chunks",
    )
    common.add_argument(
        "--provider", default=None, choices=["openai", "ollama", "stub"],
        help="override embedding provider",
    )

    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")

    sub.add_parser("health", parents=[common], help="print RAG health status")
    sub.add_parser("stats", parents=[common], help="per-domain counts and cache hit rate")

    p_ret = sub.add_parser("retrieve", parents=[common], help="manual RAG search")
    p_ret.add_argument("query", help="search query")
    p_ret.add_argument("--top-k", type=int, default=5)
    p_ret.add_argument("--domain", default=None)

    sub.add_parser("list-domains", parents=[common], help="list all known domains")
    sub.add_parser(
        "migrate-status", parents=[common],
        help="compare FAISS vs pgvector counts per domain",
    )

    p_reidx = sub.add_parser(
        "reindex-faiss", parents=[common],
        help="rebuild FAISS index for a domain from pgvector",
    )
    p_reidx.add_argument("--domain", required=True)

    return p


COMMANDS = {
    "health": cmd_health,
    "stats": cmd_stats,
    "retrieve": cmd_retrieve,
    "list-domains": cmd_list_domains,
    "migrate-status": cmd_migrate_status,
    "reindex-faiss": cmd_reindex_faiss,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = COMMANDS[args.command]
    try:
        return asyncio.run(handler(args))
    except KeyboardInterrupt:
        _err("interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())

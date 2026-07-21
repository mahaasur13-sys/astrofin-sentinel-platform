#!/usr/bin/env python3
"""CLI utility to rebuild the Production RAG Index for AstroFin Sentinel.

Scans docs/ and knowledge/ directories for Markdown files,
vectorizes them via FAISS+SentenceTransformers, and saves the index.

Usage:
    python tools/rebuild_rag.py
    python tools/rebuild_rag.py --dirs docs knowledge
"""
import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from knowledge.rag_index import RAGIndex

logger = logging.getLogger("rebuild_rag")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def collect_documents(scan_dirs: list[Path]) -> list[tuple[str, dict]]:
    documents: list[tuple[str, dict]] = []
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            logger.warning("Directory does not exist, skipping: %s", scan_dir)
            continue
        for file_path in scan_dir.rglob("*.md"):
            try:
                text = file_path.read_text(encoding="utf-8")
                if text.startswith("---"):
                    end = text.find("---", 3)
                    if end != -1:
                        text = text[end + 3:]
                if text.strip():
                    documents.append((text, {"source": str(file_path.relative_to(PROJECT_ROOT))}))
            except Exception as e:
                logger.error("Failed to read file %s: %s", file_path, e)
    return documents


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild Production RAG Index for AstroFin Sentinel.")
    parser.add_argument(
        "--dirs", nargs="+", default=["docs", "knowledge"],
        help="Directories to scan for .md files (relative to project root)."
    )
    args = parser.parse_args()
    scan_dirs = [PROJECT_ROOT / d for d in args.dirs]
    logger.info("Scanning directories: %s", [str(d) for d in scan_dirs])
    documents = collect_documents(scan_dirs)
    if not documents:
        logger.error("No documents found. Aborting.")
        return 1
    logger.info("Collected %d documents. Initializing RAG Index...", len(documents))
    try:
        rag = RAGIndex()
        rag.rebuild(documents)
        logger.info("RAG Index successfully rebuilt!")
        if rag.chunks:
            test_query = "astrofin sentinel architecture"
            logger.info("Smoke test retrieval: query='%s'", test_query)
            results = rag.retrieve(test_query, top_k=3)
            for i, res in enumerate(results):
                logger.info("  Result %d: rrf=%.4f src=%s snippet=%.80s",
                            i + 1, res.metadata.get('rrf_score', 0),
                            res.metadata.get('source', '?'), res.text)
    except Exception as e:
        logger.error("Failed to rebuild RAG index: %s", e, exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

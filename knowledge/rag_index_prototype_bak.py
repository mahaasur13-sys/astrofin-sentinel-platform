"""
AstroFin Sentinel V5 — RAG Index (FAISS)

Lightweight in-memory knowledge base with financial context.
Uses FAISS for vector similarity and sentence-transformers for embeddings.

Usage:
    from knowledge.rag_index import retrieve_context, init_index

    init_index()  # one-time setup
    ctx = retrieve_context("What was Apple's revenue in 2024?")
"""

import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
import faiss

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_DOCS: list[str] = []
_MODEL: Optional[SentenceTransformer] = None
_INDEX: Optional[faiss.IndexFlatL2] = None

_TEST_DOCUMENTS = [
    "Apple Inc. reported Q4 2024 revenue of $94.9 billion, up 6% year-over-year. "
    "Services revenue reached an all-time high of $25 billion. iPhone revenue was $46.2 billion.",

    "Microsoft Corporation Q2 FY2025 revenue was $69.6 billion, up 12% YoY. "
    "Azure cloud revenue grew 31%. AI services contributed $13 billion annualized run rate.",

    "Tesla Inc. Q4 2024 automotive revenue was $19.8 billion. Energy storage deployments "
    "reached 11 GWh, up 243% YoY. Operating margin improved to 8.2%.",

    "NVIDIA Corporation reported Q3 FY2025 revenue of $35.1 billion, up 94% YoY. "
    "Data center revenue was $30.8 billion. Gaming revenue was $3.3 billion.",

    "The Federal Reserve maintained interest rates at 4.25-4.50% in January 2026. "
    "Inflation remains above the 2% target at 2.9% CPI. The dot plot suggests two cuts in 2026.",

    "Bitcoin ETF inflows reached $35 billion cumulative in 2024. BlackRock IBIT leads with $21 billion AUM. "
    "Spot Ethereum ETFs accumulated $12 billion in assets.",

    "Gold prices reached $2,700/oz in Q4 2024, up 28% year-to-date. Central bank buying "
    "accelerated with China adding 150 tonnes to reserves in 2024.",

    "VIX index averaged 18.2 in 2024, below the 10-year average of 19.5. "
    "S&P 500 realized volatility was 13.8%, suggesting low fear environment.",

    "SEC 10-K filing: JPMorgan Chase reported total assets of $4.1 trillion. "
    "Net income was $58.5 billion for fiscal year 2024. CET1 ratio at 15.1%.",

    "Oil (WTI) traded at $72/bbl in Q4 2024. OPEC+ extended production cuts through Q1 2025. "
    "Global demand forecast revised up by IEA to 103 million bpd.",
]


def init_index(documents: Optional[list[str]] = None) -> bool:
    """Initialize the FAISS index with test documents or provided text chunks.

    Args:
        documents: Optional list of text documents. Uses _TEST_DOCUMENTS if None.

    Returns:
        True on success, False on failure.
    """
    global _MODEL, _INDEX, _DOCS

    docs = documents or _TEST_DOCUMENTS
    _DOCS = list(docs)

    try:
        _MODEL = SentenceTransformer(
            os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )
        embeddings = _MODEL.encode(docs, normalize_embeddings=True)
        dim = embeddings.shape[1]
        _INDEX = faiss.IndexFlatL2(dim)
        _INDEX.add(np.ascontiguousarray(embeddings.astype(np.float32)))
        logger.info("RAG index initialized: %d docs, dim=%d", len(docs), dim)
        return True
    except Exception as exc:
        logger.warning("RAG init failed (degraded mode): %s", exc)
        _MODEL = None
        _INDEX = None
        return False


def retrieve_context(
    query: str,
    top_k: int = 3,
) -> str:
    """Retrieve top-k most relevant text chunks from the FAISS index.

    Args:
        query: User query text.
        top_k: Number of chunks to retrieve.

    Returns:
        Concatenated context string, or empty string if index unavailable.
    """
    global _MODEL, _INDEX, _DOCS

    if _INDEX is None or _MODEL is None or not _DOCS:
        return ""

    try:
        qvec = _MODEL.encode([query], normalize_embeddings=True)
        distances, indices = _INDEX.search(
            np.ascontiguousarray(qvec.astype(np.float32)),
            min(top_k, len(_DOCS)),
        )
        chunks = [_DOCS[i] for i in indices[0] if 0 <= i < len(_DOCS)]
        return "\n\n".join(chunks) if chunks else ""
    except Exception as exc:
        logger.warning("RAG retrieve failed: %s", exc)
        return ""

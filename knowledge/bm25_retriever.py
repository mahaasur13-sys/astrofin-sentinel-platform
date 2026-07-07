"""In-process BM25 retriever (P2-03a).

Pure-Python BM25 implementation that runs over already-loaded chunks
(no Postgres required). Used as the lexical half of the hybrid retriever
in P2-03b. Tokenization is a regex over word characters (handles Latin,
Cyrillic, digits).

The retriever does NOT mutate the input chunks — scored results are
returned as new Chunk objects via dataclasses.replace with a populated
`bm25_score` field.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field, replace
from typing import Iterable, List, Optional

# Matches runs of word characters: letters (incl. Cyrillic + ёЁ) and digits.
_TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]+")


@dataclass
class Chunk:
    """Lightweight chunk structure compatible with what pgvector returns.

    `bm25_score` is populated only on retrieval results; it stays None on
    the original input chunks.
    """

    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    score: Optional[float] = None
    bm25_score: Optional[float] = None


class BM25Retriever:
    """In-process BM25 retriever.

    Args:
        chunks: Source chunks to search over. Not mutated.
        k1: BM25 term-frequency saturation parameter (typical: 1.2–2.0).
        b: BM25 length-normalization parameter (typical: 0.75).
    """

    def __init__(
        self,
        chunks: Iterable[Chunk],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.chunks: List[Chunk] = list(chunks)
        self.k1 = k1
        self.b = b

        self._tokenized: List[List[str]] = [self._tokenize(c.content) for c in self.chunks]
        n = len(self.chunks)
        self._avgdl = sum(len(toks) for toks in self._tokenized) / n if n else 0.0
        self._idf: dict = self._compute_idf()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return _TOKEN_RE.findall(text.lower())

    def _compute_idf(self) -> dict:
        """Robertson IDF with smoothing so log term is always positive."""
        doc_freq: Counter = Counter()
        for toks in self._tokenized:
            for token in set(toks):
                doc_freq[token] += 1
        n = len(self.chunks)
        idf: dict = {}
        for token, df in doc_freq.items():
            # +1.0 inside log guarantees a non-negative score even for very
            # common terms (corpus-wide tokens).
            idf[token] = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
        return idf

    def _score_doc(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_len: int,
    ) -> float:
        if not doc_tokens or doc_len == 0 or self._avgdl == 0:
            return 0.0
        freq = Counter(doc_tokens)
        score = 0.0
        for token in query_tokens:
            idf = self._idf.get(token)
            if idf is None:
                continue
            tf = freq.get(token, 0)
            if tf == 0:
                continue
            num = tf * (self.k1 + 1.0)
            den = tf + self.k1 * (1.0 - self.b + self.b * doc_len / self._avgdl)
            score += idf * (num / den)
        return score

    def retrieve(self, query: str, top_k: int = 10) -> List[Chunk]:
        """Return top-k chunks by BM25 score (descending), as new objects."""
        if top_k <= 0:
            return []
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored: List[tuple] = []
        for idx, chunk in enumerate(self.chunks):
            doc_len = len(self._tokenized[idx])
            s = self._score_doc(query_tokens, self._tokenized[idx], doc_len)
            scored.append((s, idx))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: List[Chunk] = []
        for s, idx in scored[:top_k]:
            results.append(replace(self.chunks[idx], bm25_score=s))
        return results


__all__ = ["Chunk", "BM25Retriever"]

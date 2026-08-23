"""Gold Layer: Embedded Hybrid Search Engine (Deterministic Vector + BM25 Lexical).

Consumes canonical Silver Parquet tables and provides zero-network, local
lexical and semantic retrieval across all New Zealand archival domains.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

# Embedding dimension for deterministic semantic projection
EMBEDDING_DIM = 64
WORD_REGEX = re.compile(r"[A-Za-z0-9]+")


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A scored retrieval outcome from hybrid search."""

    canonical_uri: str
    title: str
    domain: str
    score: float
    body_snippet: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "canonical_uri": self.canonical_uri,
            "title": self.title,
            "domain": self.domain,
            "score": round(self.score, 4),
            "body_snippet": self.body_snippet,
            "metadata": dict(self.metadata),
        }


def compute_deterministic_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Generate normalized deterministic vector embedding without external ML models."""
    vec = [0.0] * dim
    words = WORD_REGEX.findall(text.lower())
    if not words:
        return vec

    for i, word in enumerate(words):
        # Position-weighted deterministic hash projection
        h = int(hashlib.sha256(f"{word}_{i % 4}".encode()).hexdigest()[:8], 16)
        index = h % dim
        sign = 1.0 if (h & 1) == 0 else -1.0
        vec[index] += sign

    # L2 normalize vector
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0.0:
        vec = [x / norm for x in vec]

    return vec


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two unit vectors."""
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    return max(0.0, min(1.0, (dot + 1.0) / 2.0))


class GoldHybridSearchEngine:
    """Local embedded hybrid search engine combining BM25 and vector similarity."""

    def __init__(self) -> None:
        """Initialize empty index stores."""
        self._documents: list[dict[str, Any]] = []
        self._vectors: list[list[float]] = []
        self._doc_lens: list[int] = []
        self._avg_doc_len: float = 0.0
        self._df: dict[str, int] = {}

    def index_parquet_corpus(self, parquet_path: Path) -> int:
        """Read canonical Silver Parquet dataset and populate local search index."""
        if not parquet_path.exists():
            return 0

        table = pq.read_table(parquet_path)
        rows = table.to_pylist()
        indexed_count = 0

        for row in rows:
            uri = str(row.get("canonical_uri", ""))
            title = str(row.get("title", ""))
            domain = str(row.get("domain", ""))
            body = str(row.get("body_text") or "")
            doc_text = f"{title} {body}"

            vec = compute_deterministic_embedding(doc_text)
            words = set(WORD_REGEX.findall(doc_text.lower()))

            for w in words:
                self._df[w] = self._df.get(w, 0) + 1

            self._documents.append(
                {
                    "canonical_uri": uri,
                    "title": title,
                    "domain": domain,
                    "body_snippet": body[:200],
                    "doc_text": doc_text,
                    "metadata": row,
                }
            )
            self._vectors.append(vec)
            self._doc_lens.append(len(words))
            indexed_count += 1

        if self._doc_lens:
            self._avg_doc_len = sum(self._doc_lens) / len(self._doc_lens)

        return indexed_count

    def search(
        self,
        query: str,
        limit: int = 10,
        domain_filter: str | None = None,
        alpha: float = 0.5,  # Weight between lexical (1-alpha) and semantic (alpha)
    ) -> list[SearchResult]:
        """Perform hybrid BM25 + Vector retrieval over indexed documents."""
        if not self._documents:
            return []

        query_vec = compute_deterministic_embedding(query)
        query_words = WORD_REGEX.findall(query.lower())
        total_docs = len(self._documents)

        scored: list[tuple[float, dict[str, Any]]] = []

        for idx, doc in enumerate(self._documents):
            if domain_filter and doc["domain"] != domain_filter:
                continue

            # 1. Semantic Cosine Score
            vector_score = cosine_similarity(query_vec, self._vectors[idx])

            # 2. BM25 Lexical Score
            bm25_score = 0.0
            doc_words = WORD_REGEX.findall(doc["doc_text"].lower())
            doc_len = len(doc_words)

            for qw in query_words:
                df = self._df.get(qw, 0)
                if df > 0:
                    idf = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))
                    tf = doc_words.count(qw)
                    k1 = 1.2
                    b = 0.75
                    denom = tf + k1 * (
                        1.0 - b + b * (doc_len / max(1.0, self._avg_doc_len))
                    )
                    bm25_score += idf * (tf * (k1 + 1.0)) / denom

            # Normalized BM25 score sigmoid
            norm_bm25 = 1.0 / (1.0 + math.exp(-bm25_score)) if bm25_score > 0 else 0.0

            # 3. Hybrid Blend
            hybrid_score = (1.0 - alpha) * norm_bm25 + alpha * vector_score
            scored.append((hybrid_score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            SearchResult(
                canonical_uri=doc["canonical_uri"],
                title=doc["title"],
                domain=doc["domain"],
                score=score,
                body_snippet=doc["body_snippet"],
                metadata=doc["metadata"],
            )
            for score, doc in scored[:limit]
        ]

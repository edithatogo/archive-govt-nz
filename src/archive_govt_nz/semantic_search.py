"""Semantic knowledge graph extraction, DCAT-AP mapping, and hybrid vector search."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, cast

_TOKEN_PATTERN = re.compile(r"\b[a-zA-Z0-9_-]{2,}\b")
_MIN_NORM_THRESHOLD = 1e-9


@dataclass(frozen=True, slots=True)
class SemanticDocument:
    """Indexed metadata representation of one government dataset."""

    dataset_id: str
    title: str
    description: str
    organization: str
    tags: tuple[str, ...]
    formats: tuple[str, ...]
    url: str
    tokens: tuple[str, ...]
    vector: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class SemanticSearchResult:
    """Ranked search result combining BM25 lexical and vector cosine similarity."""

    dataset_id: str
    title: str
    organization: str
    score: float
    lexical_score: float
    vector_score: float
    matched_tags: tuple[str, ...]
    formats: tuple[str, ...]


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text into lowercase terms."""
    return [match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)]


def _generate_dense_vector(tokens: list[str], dim: int = 64) -> tuple[float, ...]:
    """Generate deterministic normalized hash-projection dense vector from tokens."""
    if not tokens:
        return tuple([0.0] * dim)

    vec = [0.0] * dim
    for token in tokens:
        h = 0
        for char in token:
            h = (h * 31 + ord(char)) & 0xFFFFFFFF
        slot = h % dim
        sign = 1.0 if (h >> 16) & 1 else -1.0
        vec[slot] += sign

    norm = math.sqrt(sum(x * x for x in vec))
    if norm < _MIN_NORM_THRESHOLD:
        return tuple([0.0] * dim)
    return tuple(x / norm for x in vec)


def _cosine_similarity(vec_a: tuple[float, ...], vec_b: tuple[float, ...]) -> float:
    """Compute cosine similarity between two unit vectors."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
    return max(0.0, min(1.0, dot))


def extract_semantic_documents(
    scope_manifest: dict[str, Any],
) -> list[SemanticDocument]:
    """Convert a global CKAN scope manifest into indexed semantic documents."""
    datasets = cast("list[dict[str, Any]]", scope_manifest.get("datasets", []))
    documents: list[SemanticDocument] = []

    for item in datasets:
        dataset_id = str(item.get("id") or "")
        title = str(item.get("title") or dataset_id)
        description = str(item.get("notes") or item.get("description") or "")
        org_data = item.get("organization")
        org_title = (
            org_data.get("title") or org_data.get("name") or "New Zealand Government"
            if isinstance(org_data, dict)
            else "New Zealand Government"
        )
        tags_raw = item.get("tags") or []
        tags: list[str] = []
        if isinstance(tags_raw, list):
            for t in tags_raw:
                if isinstance(t, dict) and "name" in t:
                    tags.append(str(t["name"]))
                elif isinstance(t, str):
                    tags.append(t)

        resources = item.get("resources") or []
        formats: list[str] = [
            str(r["format"]).upper()
            for r in resources
            if isinstance(r, dict) and r.get("format")
        ]

        combined_text = f"{title} {description} {org_title} {' '.join(tags)}"
        tokens = _tokenize(combined_text)
        vector = _generate_dense_vector(tokens)

        documents.append(
            SemanticDocument(
                dataset_id=dataset_id,
                title=title,
                description=description,
                organization=str(org_title),
                tags=tuple(tags),
                formats=tuple(sorted(set(formats))),
                url=f"https://catalogue.data.govt.nz/dataset/{dataset_id}",
                tokens=tuple(tokens),
                vector=vector,
            )
        )

    return documents


def build_dcat_ap_knowledge_graph(
    scope_manifest: dict[str, Any],
    catalog_title: str = "New Zealand Government Open Data Archive",
) -> dict[str, Any]:
    """Generate DCAT-AP 3.0 JSON-LD knowledge graph representation of the estate."""
    docs = extract_semantic_documents(scope_manifest)
    dataset_nodes: list[dict[str, Any]] = [
        {
            "@id": f"https://archive.govt.nz/dataset/{doc.dataset_id}",
            "@type": "dcat:Dataset",
            "dct:identifier": doc.dataset_id,
            "dct:title": doc.title,
            "dct:description": doc.description,
            "dct:publisher": {
                "@type": "foaf:Agent",
                "foaf:name": doc.organization,
            },
            "dcat:keyword": list(doc.tags),
            "dct:landingPage": doc.url,
        }
        for doc in docs
    ]

    return {
        "@context": {
            "dcat": "http://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "schema": "http://schema.org/",
        },
        "@id": "https://archive.govt.nz/catalog/global",
        "@type": "dcat:Catalog",
        "dct:title": catalog_title,
        "dct:language": "en",
        "dcat:dataset": dataset_nodes,
    }


class SemanticKnowledgeSearchIndex:
    """Hybrid lexical + vector search engine for the national dataset catalog."""

    def __init__(self, documents: list[SemanticDocument]) -> None:
        """Initialize index and precompute corpus-level document frequencies."""
        self._documents = documents
        self._doc_count = len(documents)
        self._doc_lengths: dict[str, int] = {
            d.dataset_id: len(d.tokens) for d in documents
        }
        self._avg_length = sum(self._doc_lengths.values()) / max(1, self._doc_count)

        self._inverted_index: dict[str, list[tuple[str, int]]] = {}
        for doc in documents:
            counts: dict[str, int] = {}
            for t in doc.tokens:
                counts[t] = counts.get(t, 0) + 1
            for term, count in counts.items():
                if term not in self._inverted_index:
                    self._inverted_index[term] = []
                self._inverted_index[term].append((doc.dataset_id, count))

        self._doc_map = {d.dataset_id: d for d in documents}

    @property
    def document_count(self) -> int:
        """Return total indexed datasets."""
        return self._doc_count

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        lexical_weight: float = 0.5,
        vector_weight: float = 0.5,
        format_filter: str | None = None,
    ) -> list[SemanticSearchResult]:
        """Perform hybrid BM25 + dense cosine similarity query."""
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        query_vector = _generate_dense_vector(query_tokens)

        k1 = 1.2
        b = 0.75
        bm25_scores: dict[str, float] = {}

        for q_term in set(query_tokens):
            postings = self._inverted_index.get(q_term, [])
            df = len(postings)
            if df == 0:
                continue
            idf = math.log(1.0 + (self._doc_count - df + 0.5) / (df + 0.5))
            for doc_id, freq in postings:
                doc_len = self._doc_lengths.get(doc_id, self._avg_length)
                tf_norm = (freq * (k1 + 1.0)) / (
                    freq + k1 * (1.0 - b + b * (doc_len / max(1.0, self._avg_length)))
                )
                bm25_scores[doc_id] = bm25_scores.get(doc_id, 0.0) + (idf * tf_norm)

        max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
        if max_bm25 > 0:
            for d_id in bm25_scores:
                bm25_scores[d_id] /= max_bm25

        results: list[SemanticSearchResult] = []
        fmt_upper = format_filter.upper() if format_filter else None

        for doc in self._documents:
            if fmt_upper and fmt_upper not in doc.formats:
                continue

            lex_score = bm25_scores.get(doc.dataset_id, 0.0)
            vec_score = _cosine_similarity(query_vector, doc.vector)
            total_score = (lexical_weight * lex_score) + (vector_weight * vec_score)

            if total_score <= 0.0:
                continue

            matched_tags = tuple(
                tag for tag in doc.tags if any(qt in tag.lower() for qt in query_tokens)
            )

            results.append(
                SemanticSearchResult(
                    dataset_id=doc.dataset_id,
                    title=doc.title,
                    organization=doc.organization,
                    score=round(total_score, 4),
                    lexical_score=round(lex_score, 4),
                    vector_score=round(vec_score, 4),
                    matched_tags=matched_tags,
                    formats=doc.formats,
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

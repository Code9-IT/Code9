"""
RAG (Retrieval-Augmented Generation) client.
============================================
Uses Ollama embeddings + pgvector (knowledge_docs table).
"""

from dataclasses import dataclass
from typing import List
import os

import httpx

from db import get_pool

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.60"))
EMBED_TIMEOUT = float(os.getenv("RAG_EMBED_TIMEOUT_SECONDS", "30"))


@dataclass
class RAGDocument:
    """One retrieved knowledge chunk."""

    title: str
    content: str
    source: str = "unknown"
    similarity: float = 0.0


@dataclass
class RAGRetrievalResult:
    """Structured retrieval result that distinguishes infra failures from empty results."""

    documents: List[RAGDocument]
    available: bool  # True when RAG infra (embedding model + DB) is reachable
    error: str | None = None  # Human-readable error when available is False
    error_stage: str | None = None  # 'embedding' | 'query' | None


async def retrieve_context(
    event_type: str,
    sensor_name: str,
    vessel_id: str,
    top_k: int | None = None,
    min_similarity: float | None = None,
) -> List[RAGDocument]:
    """
    Retrieve top knowledge chunks for an event.
    Returns an empty list when there are no relevant matches.
    """
    query = f"{event_type} {sensor_name} {vessel_id}"
    return await retrieve_context_for_query(
        query,
        top_k=top_k,
        min_similarity=min_similarity,
    )


async def retrieve_context_for_query(
    query: str,
    top_k: int | None = None,
    min_similarity: float | None = None,
) -> List[RAGDocument]:
    """Retrieve top knowledge chunks for a free-form query.

    Backward-compatible wrapper: returns [] on infra failure (same as before).
    Use retrieve_context_for_query_with_status() for structured error info.
    """
    result = await retrieve_context_for_query_with_status(
        query, top_k=top_k, min_similarity=min_similarity
    )
    return result.documents


async def retrieve_context_for_query_with_status(
    query: str,
    top_k: int | None = None,
    min_similarity: float | None = None,
) -> RAGRetrievalResult:
    """Retrieve top knowledge chunks with explicit availability/error reporting."""
    resolved_top_k = max(int(top_k or RAG_TOP_K), 1)
    resolved_min_similarity = (
        RAG_MIN_SIMILARITY if min_similarity is None else float(min_similarity)
    )

    try:
        embedding = await _embed_text(query)
    except Exception as exc:
        print(f"[rag] Embedding failed: {exc}")
        return RAGRetrievalResult(
            documents=[],
            available=False,
            error=f"Embedding model unavailable: {exc}",
            error_stage="embedding",
        )

    vector_literal = _to_pgvector_literal(embedding)
    pool = get_pool()

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT title,
                       content,
                       source,
                       1 - (embedding <=> $1::vector) AS similarity
                FROM knowledge_docs
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                vector_literal,
                resolved_top_k,
            )
    except Exception as exc:
        print(f"[rag] Retrieval query failed: {exc}")
        return RAGRetrievalResult(
            documents=[],
            available=False,
            error=f"Knowledge DB query failed: {exc}",
            error_stage="query",
        )

    docs: List[RAGDocument] = []
    for row in rows:
        similarity = float(row["similarity"] or 0.0)
        if similarity < resolved_min_similarity:
            continue
        docs.append(
            RAGDocument(
                title=row["title"],
                content=row["content"],
                source=row["source"],
                similarity=similarity,
            )
        )
    return RAGRetrievalResult(documents=docs, available=True)


def format_context_for_prompt(documents: List[RAGDocument]) -> str:
    """Serialize retrieved docs into prompt text."""
    if not documents:
        return ""

    parts = []
    for doc in documents:
        parts.append(f"--- {doc.title} (source: {doc.source}) ---\n{doc.content}")
    return "\n\n".join(parts)


async def _embed_text(text: str) -> list[float]:
    """
    Create one embedding vector using Ollama.
    Tries /api/embed first, then falls back to /api/embeddings.
    """
    async with httpx.AsyncClient(timeout=EMBED_TIMEOUT) as client:
        embed_resp = await client.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": OLLAMA_EMBED_MODEL, "input": text},
        )
        if embed_resp.status_code < 400:
            data = embed_resp.json()
            vectors = data.get("embeddings") or []
            if vectors and isinstance(vectors[0], list):
                return [float(v) for v in vectors[0]]

        legacy_resp = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
        )
        legacy_resp.raise_for_status()
        legacy = legacy_resp.json()
        vector = legacy.get("embedding")
        if not vector:
            raise RuntimeError("Ollama returned no embedding vector")
        return [float(v) for v in vector]


def _to_pgvector_literal(values: list[float]) -> str:
    """Convert float list to pgvector literal format."""
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"

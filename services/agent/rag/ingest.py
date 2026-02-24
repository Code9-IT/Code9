"""
Knowledge ingestion for RAG.
============================
Reads docs from docs/knowledge, chunks them, embeds each chunk with Ollama,
and stores them in knowledge_docs (pgvector).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import asyncpg
import httpx

KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "/app/docs/knowledge")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
EMBED_TIMEOUT = float(os.getenv("RAG_EMBED_TIMEOUT_SECONDS", "30"))
CHUNK_WORDS = int(os.getenv("RAG_CHUNK_WORDS", "280"))
CHUNK_OVERLAP_WORDS = int(os.getenv("RAG_CHUNK_OVERLAP_WORDS", "40"))


async def ingest_if_empty(pool: asyncpg.Pool, knowledge_dir: str = KNOWLEDGE_DIR) -> int:
    """
    Ingest knowledge docs only when the table is currently empty.
    Returns number of chunks written.
    """
    async with pool.acquire() as conn:
        await _ensure_schema(conn)
        count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_docs")
    if int(count or 0) > 0:
        print(f"[rag] knowledge_docs already populated ({count} rows)")
        return 0
    return await ingest_knowledge_documents(pool, knowledge_dir=knowledge_dir)


async def ingest_knowledge_documents(pool: asyncpg.Pool, knowledge_dir: str = KNOWLEDGE_DIR) -> int:
    """
    Read all knowledge files and upsert chunk embeddings.
    Returns total chunks written.
    """
    root = Path(knowledge_dir)
    if not root.exists():
        print(f"[rag] Knowledge directory not found: {root}")
        return 0

    files = sorted(
        p for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".md", ".txt"}
        and p.stem.lower() != "readme"
    )
    if not files:
        print(f"[rag] No .md/.txt files found in {root}")
        return 0

    total_written = 0
    async with pool.acquire() as conn:
        await _ensure_schema(conn)

    for file_path in files:
        raw = file_path.read_text(encoding="utf-8").strip()
        if not raw:
            continue

        title = _extract_title(file_path, raw)
        chunks = _chunk_text(raw, max_words=CHUNK_WORDS, overlap_words=CHUNK_OVERLAP_WORDS)
        source = str(file_path.relative_to(root)).replace("\\", "/")

        async with pool.acquire() as conn:
            for idx, chunk in enumerate(chunks):
                vector = await _embed_text(chunk)
                await conn.execute(
                    """
                    INSERT INTO knowledge_docs (title, content, source, chunk_index, embedding)
                    VALUES ($1, $2, $3, $4, $5::vector)
                    ON CONFLICT (source, chunk_index)
                    DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        created_at = NOW()
                    """,
                    title,
                    chunk,
                    source,
                    idx,
                    _to_pgvector_literal(vector),
                )

            await conn.execute(
                """
                DELETE FROM knowledge_docs
                WHERE source = $1 AND chunk_index >= $2
                """,
                source,
                len(chunks),
            )

        print(f"[rag] Ingested {source} ({len(chunks)} chunks)")
        total_written += len(chunks)

    print(f"[rag] Ingestion complete: {total_written} chunks written")
    return total_written


async def _ensure_schema(conn: asyncpg.Connection) -> None:
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_docs (
            id           SERIAL PRIMARY KEY,
            title        TEXT        NOT NULL,
            content      TEXT        NOT NULL,
            source       TEXT        NOT NULL,
            chunk_index  INTEGER     NOT NULL DEFAULT 0,
            embedding    VECTOR(768) NOT NULL,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    await conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_docs_source_chunk
            ON knowledge_docs (source, chunk_index)
        """
    )
    await conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_knowledge_docs_embedding
            ON knowledge_docs
            USING hnsw (embedding vector_cosine_ops)
        """
    )


def _chunk_text(text: str, max_words: int = 280, overlap_words: int = 40) -> list[str]:
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]

    chunks: list[str] = []
    start = 0
    safe_overlap = max(0, min(overlap_words, max_words - 1))
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - safe_overlap
    return chunks


def _extract_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return path.stem.replace("_", " ").replace("-", " ").title()


async def _embed_text(text: str) -> list[float]:
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
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


async def _run_cli() -> None:
    pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        database=os.getenv("DB_NAME", "maritime_telemetry"),
        min_size=1,
        max_size=4,
    )
    try:
        await ingest_knowledge_documents(pool, knowledge_dir=KNOWLEDGE_DIR)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(_run_cli())

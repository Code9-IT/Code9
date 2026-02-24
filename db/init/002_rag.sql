-- =============================================================
-- Maritime Observability - RAG schema
-- =============================================================
-- Adds pgvector-backed knowledge storage used by the agent.
-- Runs automatically on first DB initialization.
-- =============================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_docs (
    id           SERIAL PRIMARY KEY,
    title        TEXT        NOT NULL,
    content      TEXT        NOT NULL,
    source       TEXT        NOT NULL,
    chunk_index  INTEGER     NOT NULL DEFAULT 0,
    embedding    VECTOR(768) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_docs_source_chunk
    ON knowledge_docs (source, chunk_index);

CREATE INDEX IF NOT EXISTS idx_knowledge_docs_embedding
    ON knowledge_docs
    USING hnsw (embedding vector_cosine_ops);

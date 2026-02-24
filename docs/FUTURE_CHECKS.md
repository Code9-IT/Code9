# Future Checks - Security, Gaps, and Next Build Steps

This document tracks what is still missing, what should be hardened before any real deployment,
and what we should build after RAG content is in place.

Last updated: 2026-02-22

---

## How To Use This File

- Keep this as the single backlog for "not now, but important later".
- When a point is fixed, mark it done and add commit/PR reference.
- Review this file before demo prep and before starting a new development sprint.

---

## Current Snapshot

- Core pipeline: running (`generator -> DB -> agent -> Grafana`).
- Dashboards: major Jonas fixes merged.
- RAG infrastructure: in place (`pgvector`, retrieval, ingest script, knowledge folder).
- RAG content: still pending (curated maritime documents).

---

## P0 - Critical Blockers

- None currently identified for local bachelor-project demo use.

---

## P1 - Important Security / Hardening

### 1) State-changing GET endpoints (demo convenience, not production-safe)

- Status: OPEN
- Files:
  - `services/agent/routes/analyze.py`
  - `services/agent/routes/events.py`
- Why it matters:
  - GET should be idempotent/safe by HTTP semantics.
  - Easy to trigger accidentally (crawler/prefetch/link-preview behavior).
- Recommended future fix:
  - Keep POST as canonical.
  - Either remove GET aliases or protect them with auth + CSRF-safe design.
  - In Grafana: move to secure API path with token/auth proxy.

### 2) No auth + wide-open CORS

- Status: OPEN
- File:
  - `services/agent/main.py`
- Why it matters:
  - `allow_origins=["*"]` and no auth means any reachable origin can call the API.
- Recommended future fix:
  - Add JWT (or reverse-proxy auth) and role checks.
  - Restrict CORS to trusted UI origins only.

### 3) Prompt-injection risk from external text sources

- Status: PARTIALLY MITIGATED
- File:
  - `services/agent/routes/analyze.py`
- Why it matters:
  - Retrieved docs can contain adversarial instructions.
- What is done:
  - System prompt now tells the model to treat retrieved text as reference evidence only.
- Recommended future fix:
  - Add content sanitation and source allowlist policy.
  - Add retrieval-time filtering and optional moderation checks.

### 4) Embedding dimension coupling to current model

- Status: OPEN (known design constraint)
- Files:
  - `db/init/002_rag.sql`
  - `services/agent/rag/client.py`
  - `services/agent/rag/ingest.py`
- Why it matters:
  - Schema uses `VECTOR(768)` (fits `nomic-embed-text`).
  - Changing embedding model dimension will break inserts/retrieval.
- Recommended future fix:
  - Keep model fixed for this project, or add migration path/versioned embedding tables.

---

## P1.5 - Reliability / Ops

### 5) Ensure ANN index exists in old DB volumes

- Status: FIXED
- Files:
  - `db/init/002_rag.sql`
  - `services/agent/rag/ingest.py`
- Note:
  - Runtime schema check now also creates `idx_knowledge_docs_embedding`.

### 6) Do not ingest guidance docs as knowledge

- Status: FIXED (basic)
- File:
  - `services/agent/rag/ingest.py`
- Note:
  - `README` is excluded.
- Better future improvement:
  - Ingest only from a strict subfolder/pattern (e.g. `docs/knowledge/articles/*.md`).

---

## P2 - Complete RAG Content (Next Main Sprint)

### Must do

- [ ] Add 10-12 focused maritime documents to `docs/knowledge/`.
- [ ] Each doc should include:
  - Scope
  - Causes
  - How to diagnose
  - Recommended actions
  - Limits / regulations
  - Sources
- [ ] Ingest after each batch:
  - `docker exec maritime_agent python rag/ingest.py`
- [ ] Validate retrieval quality for representative event types.
- [ ] Tune:
  - `RAG_TOP_K`
  - `RAG_MIN_SIMILARITY`

### Quality target

- For each major sensor/event cluster, at least one relevant source-backed document is retrieved.
- AI analysis should reference concrete domain context, not generic text.

---

## P3 - Next Product Features (After RAG)

### Crew chatbot on main UI (planned)

- Goal:
  - Crew can ask operational questions, for example:
    - "How many events happened in the last week?"
    - "Which sensors triggered most alarms?"
    - "Any unresolved critical alarms right now?"
- Needed pieces:
  - Query-to-tool flow (reuse MCP tools + add aggregated query tool if needed).
  - Guardrails for allowed question types.
  - Simple chat UI and response logging.

### Additional platform improvements

- [ ] Add audit logging for analyze/acknowledge actions.
- [ ] Add rate limiting for API endpoints.
- [ ] Add automated tests for RAG retrieval + ingest.
- [ ] Add "production mode" env profile (auth on, strict CORS, no GET aliases).

---

## Definition Of "Deployment-Ready" (Future)

This prototype is demo-ready, not production-ready. Before any real deployment:

- [ ] Auth and authorization enabled.
- [ ] CORS restricted.
- [ ] State-changing GET aliases removed or protected.
- [ ] Secrets management and secure config reviewed.
- [ ] Incident/audit logging in place.
- [ ] RAG source governance process documented.

"""Maritime Agentic Observability -- Agent Service
================================================
FastAPI entry point.

Responsibilities:
  - Expose HTTP endpoints for event analysis and retrieval.
  - Orchestrate the analysis pipeline: event -> RAG -> LLM -> store.

Start locally (outside Docker):
  uvicorn main:app --reload
"""

import asyncio
from contextlib import asynccontextmanager, suppress
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_pool, close_pool
from routes.analyze import router as analyze_router
from routes.chat import router as chat_router
from routes.dynamic_dashboard import router as dynamic_dashboard_router
from routes.events  import router as events_router
from routes.validation import router as validation_router
from rag.ingest import ingest_if_empty

# Default budget: 120 attempts * 15s = 30 minutes total wait. This is sized
# to survive a cold-start fresh-volume Ollama model pull (llama3.2 ~2 GB +
# nomic-embed-text), which on a slow connection can run well past the
# previous 6-minute (24 * 15s) budget and force a manual agent restart.
RAG_AUTO_INGEST_RETRIES = int(os.getenv("RAG_AUTO_INGEST_RETRIES", "120"))
RAG_AUTO_INGEST_DELAY_SECONDS = float(os.getenv("RAG_AUTO_INGEST_DELAY_SECONDS", "15"))


async def ensure_agent_schema():
    """Apply lightweight runtime schema updates needed by newer routes."""
    from db import get_pool

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            ALTER TABLE ai_analyses
            ADD COLUMN IF NOT EXISTS analysis_mode TEXT NOT NULL DEFAULT 'full'
            """
        )
        await conn.execute(
            """
            ALTER TABLE ai_analyses
            ADD COLUMN IF NOT EXISTS retrieved_documents JSONB NOT NULL DEFAULT '[]'::jsonb
            """
        )
        await conn.execute(
            """
            ALTER TABLE ai_analyses
            ADD COLUMN IF NOT EXISTS tool_calls JSONB NOT NULL DEFAULT '[]'::jsonb
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_analyses_event_mode
            ON ai_analyses(event_id, analysis_mode, timestamp DESC)
            """
        )
        await conn.execute(
            """
            ALTER TABLE ai_analyses
            ADD COLUMN IF NOT EXISTS vessel_imo TEXT
            """
        )
        await conn.execute(
            """
            ALTER TABLE ai_analyses
            ADD COLUMN IF NOT EXISTS app_external_id TEXT
            """
        )
        await conn.execute(
            """
            ALTER TABLE ai_analyses
            ADD COLUMN IF NOT EXISTS alert_name TEXT
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_analyses_uds_context
            ON ai_analyses(vessel_imo, app_external_id, alert_name, timestamp DESC)
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dynamic_dashboard_runs (
                id BIGSERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('UTC', now()),
                trigger_mode TEXT NOT NULL,
                source_alert_fingerprint VARCHAR(255),
                vessel_imo VARCHAR(255) NOT NULL,
                app_external_id VARCHAR(255),
                alert_name VARCHAR(255),
                severity VARCHAR(50),
                scenario_key VARCHAR(100) NOT NULL,
                dashboard_uid VARCHAR(255) NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                used_tools_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                dashboard_json JSONB NOT NULL DEFAULT '{}'::jsonb
            )
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_runs_created_at
            ON dynamic_dashboard_runs(created_at DESC)
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_runs_vessel_app
            ON dynamic_dashboard_runs(vessel_imo, app_external_id, created_at DESC)
            """
        )


async def _run_rag_auto_ingest() -> None:
    """Retry ingest until Ollama models become available or retries are exhausted."""
    from db import get_pool

    for attempt in range(1, RAG_AUTO_INGEST_RETRIES + 1):
        try:
            written = await ingest_if_empty(get_pool())
            if written:
                print(f"[agent] RAG auto-ingest completed ({written} chunks)")
            return
        except Exception as exc:  # pragma: no cover
            if attempt >= RAG_AUTO_INGEST_RETRIES:
                print(f"[agent] RAG auto-ingest skipped after {attempt} attempts: {exc}")
                return
            print(
                f"[agent] RAG auto-ingest retry {attempt}/{RAG_AUTO_INGEST_RETRIES} "
                f"in {RAG_AUTO_INGEST_DELAY_SECONDS:.0f}s: {exc}"
            )
            await asyncio.sleep(RAG_AUTO_INGEST_DELAY_SECONDS)


def _cors_allow_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


# --- Lifecycle ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the async DB connection pool on startup, close on shutdown."""
    rag_task = None
    await init_pool()
    try:
        await ensure_agent_schema()
        rag_task = asyncio.create_task(_run_rag_auto_ingest())
    except Exception as exc:  # pragma: no cover
        print(f"[agent] Startup warning: {exc}")
    try:
        yield
    finally:
        if rag_task is not None and not rag_task.done():
            rag_task.cancel()
            with suppress(asyncio.CancelledError):
                await rag_task
        await close_pool()


# --- App ------------------------------------------------------------------
app = FastAPI(
    title="Maritime Observability Agent",
    description="AI agent that analyses maritime telemetry events.",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow Grafana (and local dev URLs) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers --------------------------------------------------------------
app.include_router(analyze_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(dynamic_dashboard_router, prefix="/api/v1")
app.include_router(events_router,  prefix="/api/v1")
app.include_router(validation_router, prefix="/api/v1")


# --- Health check ---------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "maritime-agent", "version": "0.1.0"}

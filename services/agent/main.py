"""Maritime Agentic Observability -- Agent Service
================================================
FastAPI entry point.

Responsibilities:
  - Expose HTTP endpoints for event analysis and retrieval.
  - Orchestrate the analysis pipeline: event -> RAG -> LLM -> store.

Start locally (outside Docker):
  uvicorn main:app --reload
"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_pool, close_pool
from routes.analyze import router as analyze_router
from routes.events  import router as events_router
from routes.validation import router as validation_router
from rag.ingest import ingest_if_empty


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
    await init_pool()
    try:
        from db import get_pool

        await ingest_if_empty(get_pool())
    except Exception as exc:  # pragma: no cover
        print(f"[agent] RAG auto-ingest skipped: {exc}")
    yield
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
app.include_router(events_router,  prefix="/api/v1")
app.include_router(validation_router, prefix="/api/v1")


# --- Health check ---------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "maritime-agent", "version": "0.1.0"}

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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_pool, close_pool
from routes.analyze import router as analyze_router
from routes.events  import router as events_router


# --- Lifecycle ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the async DB connection pool on startup, close on shutdown."""
    await init_pool()
    yield
    await close_pool()


# --- App ------------------------------------------------------------------
app = FastAPI(
    title="Maritime Observability Agent",
    description="AI agent that analyses maritime telemetry events.",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow Grafana (and a local browser) to call the API.
# TODO: restrict allow_origins to Grafana host in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers --------------------------------------------------------------
app.include_router(analyze_router, prefix="/api/v1")
app.include_router(events_router,  prefix="/api/v1")


# --- Health check ---------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "maritime-agent", "version": "0.1.0"}

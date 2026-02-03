"""
POST /api/v1/analyze   – trigger an AI analysis for one event
GET  /api/v1/analyses  – list the most recent analyses
=====================================================================
Pipeline:
  1. Fetch the event row from the DB.
  2. Retrieve context documents via RAG (stub for now).
  3. Build a prompt and send it to the LLM (stub for now).
  4. Persist the result in ai_analyses.
  5. Return the analysis to the caller.
"""

from fastapi import APIRouter, HTTPException

from db     import get_pool
from models import AnalyzeRequest, AnalyzeResponse
from rag.client      import retrieve_context, format_context_for_prompt
from llm.ollama_client import generate_analysis

router = APIRouter(tags=["analyze"])


# ─── POST /analyze ────────────────────────────────────────
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_event(request: AnalyzeRequest):
    pool = get_pool()

    # 1) Fetch event ──────────────────────────────────────
    async with pool.acquire() as conn:
        event = await conn.fetchrow(
            "SELECT * FROM events WHERE id = $1", request.event_id
        )
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {request.event_id} not found")

    # 2) RAG context ───────────────────────────────────────
    context_docs  = await retrieve_context(
        event_type  = event["event_type"],
        sensor_name = event["sensor_name"],
        vessel_id   = event["vessel_id"],
    )
    context_text = format_context_for_prompt(context_docs)

    # 3) Build prompt + call LLM ──────────────────────────
    prompt     = _build_prompt(dict(event), context_text)
    llm_result = await generate_analysis(prompt)

    # 4) Persist ───────────────────────────────────────────
    analysis_text     = llm_result.get("response", "")
    model_used        = llm_result.get("model", "unknown")
    # TODO: parse suggested_actions from LLM response text
    suggested_actions = ["Investigate further"]   # placeholder
    # TODO: extract or calibrate confidence from LLM output
    confidence        = 0.0

    async with pool.acquire() as conn:
        analysis_id = await conn.fetchval(
            """
            INSERT INTO ai_analyses
                (event_id, analysis_text, suggested_actions, confidence, model_used, status)
            VALUES ($1, $2, $3, $4, $5, 'completed')
            RETURNING id
            """,
            request.event_id, analysis_text, suggested_actions, confidence, model_used,
        )

    # 5) Return ────────────────────────────────────────────
    return AnalyzeResponse(
        id=analysis_id,
        event_id=request.event_id,
        analysis_text=analysis_text,
        suggested_actions=suggested_actions,
        confidence=confidence,
        model_used=model_used,
        status="completed",
    )


# ─── GET /analyses ────────────────────────────────────────
@router.get("/analyses")
async def get_recent_analyses(limit: int = 10):
    """Return the most recent AI analyses (useful for Grafana or direct API use)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT a.id, a.timestamp, a.event_id,
                   e.vessel_id, e.event_type, e.sensor_name,
                   a.analysis_text, a.suggested_actions,
                   a.confidence, a.model_used, a.status
            FROM   ai_analyses a
            JOIN   events e ON a.event_id = e.id
            ORDER  BY a.timestamp DESC
            LIMIT  $1
            """,
            limit,
        )
    # asyncpg Records → plain dicts for JSON serialisation
    return [dict(row) for row in rows]


# ─── helpers ──────────────────────────────────────────────
def _build_prompt(event: dict, context: str) -> str:
    """
    Assemble the prompt that will be sent to the LLM.

    TODO: iterate on prompt engineering here – this is the single
          most impactful place to improve analysis quality.
    """
    return (
        "You are a maritime telemetry analysis agent.\n\n"
        f"An event has been detected on vessel {event['vessel_id']}:\n"
        f"  - Event type : {event['event_type']}\n"
        f"  - Sensor     : {event['sensor_name']}\n"
        f"  - Severity   : {event['severity']}\n"
        f"  - Details    : {event['details']}\n"
        f"  - Timestamp  : {event['timestamp']}\n\n"
        f"Relevant documentation:\n{context}\n\n"
        "Please provide:\n"
        "  1. An explanation of why this event likely occurred.\n"
        "  2. The potential impact on vessel operations.\n"
        "  3. Suggested corrective actions.\n"
        "  4. Your confidence level (0–100 %).\n"
    )

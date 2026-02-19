"""
POST /api/v1/analyze   – trigger an AI analysis for one event
GET  /api/v1/analyses  – list the most recent analyses
=====================================================================
Agentic pipeline:
  1. Fetch the event row from the DB.
  2. Retrieve context documents via RAG.
  3. Fetch tool definitions from the MCP server.
  4. Run the tool-calling loop:
       a. Send event + tools to Ollama.
       b. If Ollama calls a tool, execute it against the MCP server.
       c. Send the result back to Ollama.
       d. Repeat until Ollama produces a final text answer.
  5. Parse structured output (confidence, suggested actions).
  6. Persist the result in ai_analyses.
  7. Return the analysis to the caller.
"""

import os
import re
import json

import httpx
from fastapi import APIRouter, HTTPException

from db     import get_pool
from models import AnalyzeRequest, AnalyzeResponse
from rag.client      import retrieve_context, format_context_for_prompt
from llm.ollama_client import chat

MCP_URL       = os.getenv("MCP_URL", "http://mcp:8001")
MAX_TOOL_CALLS = 5   # safety cap – prevents infinite loops

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
    context_docs = await retrieve_context(
        event_type  = event["event_type"],
        sensor_name = event["sensor_name"],
        vessel_id   = event["vessel_id"],
    )
    context_text = format_context_for_prompt(context_docs)

    # 3) Fetch MCP tool definitions ────────────────────────
    tools = await _fetch_mcp_tools()

    # 4) Agentic tool-calling loop ─────────────────────────
    try:
        analysis_text = await _run_tool_loop(dict(event), context_text, tools)
        status = "completed"
    except Exception as exc:
        analysis_text = f"Analysis failed: {exc}"
        status = "failed"

    # 5) Parse structured output ───────────────────────────
    suggested_actions = _parse_suggested_actions(analysis_text)
    confidence        = _parse_confidence(analysis_text)
    model_used        = os.getenv("OLLAMA_MODEL", "llama3.2")

    # 6) Persist ───────────────────────────────────────────
    async with pool.acquire() as conn:
        analysis_id = await conn.fetchval(
            """
            INSERT INTO ai_analyses
                (event_id, analysis_text, suggested_actions, confidence, model_used, status)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            request.event_id, analysis_text, suggested_actions,
            confidence, model_used, status,
        )

    # 7) Return ────────────────────────────────────────────
    return AnalyzeResponse(
        id=analysis_id,
        event_id=request.event_id,
        analysis_text=analysis_text,
        suggested_actions=suggested_actions,
        confidence=confidence,
        model_used=model_used,
        status=status,
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
    return [dict(row) for row in rows]


# ─── MCP helpers ──────────────────────────────────────────
async def _fetch_mcp_tools() -> list[dict]:
    """
    Fetch tool definitions from the MCP server and convert them to
    Ollama's tool format (type + function wrapper).
    Returns an empty list if the MCP server is unreachable.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MCP_URL}/tools")
            resp.raise_for_status()
            mcp_tools = resp.json().get("tools", [])
        return [
            {
                "type": "function",
                "function": {
                    "name":        t["name"],
                    "description": t["description"],
                    "parameters":  t.get("inputSchema", {}),
                },
            }
            for t in mcp_tools
        ]
    except Exception as exc:
        print(f"[agent] Could not fetch MCP tools: {exc}")
        return []   # degrade gracefully – analysis continues without tools


async def _call_mcp_tool(name: str, arguments: dict) -> str:
    """
    Execute one tool call against the MCP REST server.
    Returns the result as a JSON string (to be sent back to the model).
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{MCP_URL}/tools/call",
                json={"name": name, "arguments": arguments},
            )
            resp.raise_for_status()
            return json.dumps(resp.json())
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ─── agentic loop ─────────────────────────────────────────
async def _run_tool_loop(
    event:   dict,
    context: str,
    tools:   list[dict],
) -> str:
    """
    Core agentic loop – the LLM decides which tools to call.

    Conversation flow:
      user:      "An anomaly was detected on vessel X …"
      assistant: [tool_call: get_telemetry(vessel_001, engine_temp, 30)]
      tool:      {"readings": [...]}
      assistant: [tool_call: get_events(vessel_001)]   ← optional second call
      tool:      {"events": [...]}
      assistant: "**ANALYSIS:** The temperature exceeded …"  ← final answer
    """
    messages: list[dict] = [
        {"role": "system", "content": _system_prompt(context)},
        {"role": "user",   "content": _user_message(event)},
    ]

    for _ in range(MAX_TOOL_CALLS + 1):
        response = await chat(messages, tools=tools or None)

        tool_calls = response.get("tool_calls")
        if not tool_calls:
            # Model produced its final text answer
            return response.get("content", "No analysis generated.")

        # Append the assistant's (tool-calling) turn to the conversation
        messages.append({
            "role":       "assistant",
            "content":    response.get("content", ""),
            "tool_calls": tool_calls,
        })

        # Execute every tool the model requested and add results
        for tc in tool_calls:
            fn   = tc.get("function", {})
            name = fn.get("name", "")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}

            result = await _call_mcp_tool(name, args)
            messages.append({"role": "tool", "name": name, "content": result})

    return "Analysis incomplete: maximum tool calls reached without a final answer."


# ─── prompt builders ──────────────────────────────────────
def _system_prompt(context: str) -> str:
    rag_section = ""
    if context and "not yet implemented" not in context:
        rag_section = f"\nRelevant documentation:\n{context}\n"

    return (
        "You are a maritime telemetry analysis agent.\n"
        "You have access to tools that query live vessel data. "
        "Use them to gather additional context before forming your conclusion "
        "(e.g. fetch recent sensor history or check for related events).\n"
        + rag_section
        + "\nAfter gathering enough information, respond in this exact format:\n\n"
        "**ANALYSIS:**\n"
        "[Explain why this event likely occurred and what it means for vessel operations]\n\n"
        "**CONFIDENCE:** [0-100]%\n\n"
        "**SUGGESTED ACTIONS:**\n"
        "1. [First action]\n"
        "2. [Second action]\n"
        "3. [Third action]\n"
    )


def _user_message(event: dict) -> str:
    return (
        f"An anomaly has been detected on vessel {event['vessel_id']}:\n"
        f"  - Event type : {event['event_type']}\n"
        f"  - Sensor     : {event['sensor_name']}\n"
        f"  - Severity   : {event['severity']}\n"
        f"  - Details    : {event['details']}\n"
        f"  - Timestamp  : {event['timestamp']}\n\n"
        "Please analyse this event and provide your findings."
    )


# ─── output parsers ───────────────────────────────────────
def _parse_confidence(text: str) -> float:
    """
    Extract the confidence percentage from the model's structured output.
    Matches patterns like: **CONFIDENCE:** 75%  or  CONFIDENCE: 80
    Returns a float in the range 0.0–1.0.
    """
    m = re.search(r'\*{0,2}CONFIDENCE\*{0,2}[:\s*]+(\d+)', text, re.IGNORECASE)
    if m:
        return min(float(m.group(1)), 100.0) / 100.0
    return 0.0


def _parse_suggested_actions(text: str) -> list[str]:
    """
    Extract the numbered action items from the SUGGESTED ACTIONS section.
    Falls back to a generic placeholder if none are found.
    """
    section = re.search(
        r'\*{0,2}SUGGESTED ACTIONS\*{0,2}[:\s]+(.*?)(?=\*{0,2}[A-Z]{3}|\Z)',
        text, re.IGNORECASE | re.DOTALL,
    )
    if section:
        actions = re.findall(r'^\d+\.\s+(.+)', section.group(1), re.MULTILINE)
        if actions:
            return [a.strip() for a in actions]
    return ["Investigate further"]

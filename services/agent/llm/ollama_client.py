"""
Ollama LLM client
==================
Calls a locally-running Ollama instance via the /api/chat endpoint.
This endpoint supports tool/function calling, which is required for the
agentic loop in analyze.py.

Configuration (all via environment variables):
  OLLAMA_URL   – base URL of Ollama  (default: http://ollama:11434)
  OLLAMA_MODEL – model to use        (default: llama3.2)
  STUB_MODE    – set to "true" to skip Ollama and return a placeholder
                 response. Useful when Ollama is not running locally.
                 (default: false)

To pull a model after starting the container:
  docker exec -it maritime_ollama ollama pull llama3.2
"""

import os
import httpx

OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
STUB_MODE    = os.getenv("STUB_MODE",    "false").lower() == "true"

# Local LLMs can be slow – give them up to 2 minutes per request.
TIMEOUT = 120.0


# ─── public API ───────────────────────────────────────────
async def chat(
    messages: list[dict],
    tools:    list[dict] | None = None,
) -> dict:
    """
    Send a conversation to Ollama and return the assistant's message dict.

    Args:
        messages: OpenAI-style list of {"role": ..., "content": ...} dicts.
        tools:    Optional list of Ollama-format tool definitions. When
                  provided the model may respond with tool_calls instead
                  of plain text.

    Returns:
        The 'message' object from Ollama, e.g.:
            {"role": "assistant", "content": "The analysis shows …"}
          or, when the model wants to call a tool:
            {"role": "assistant", "content": "", "tool_calls": [{…}]}
    """
    if STUB_MODE:
        return _stub_message()

    payload: dict = {
        "model":    OLLAMA_MODEL,
        "messages": messages,
        "stream":   False,
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["message"]


# ─── stub ─────────────────────────────────────────────────
def _stub_message() -> dict:
    """
    Deterministic placeholder returned when STUB_MODE=true.
    Matches the structured output format that analyze.py expects
    so the full pipeline still runs without a real model.
    """
    return {
        "role": "assistant",
        "content": (
            "[STUB – Ollama not connected]\n"
            "Set STUB_MODE=false and start the Ollama service to get real responses.\n\n"
            "**ANALYSIS:**\n"
            "This is a placeholder. The agent pipeline is working end-to-end.\n\n"
            "**CONFIDENCE:** 0%\n\n"
            "**SUGGESTED ACTIONS:**\n"
            "1. Start the Ollama service and pull a model (e.g. llama3.2)\n"
            "2. Set STUB_MODE=false in the agent environment\n"
            "3. Re-trigger the analysis\n"
        ),
    }

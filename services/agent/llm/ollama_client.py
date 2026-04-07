"""
Ollama LLM client.

Calls a locally-running Ollama instance via the /api/chat endpoint.
This endpoint supports tool/function calling, which is required for the
agentic loop in analyze.py.

Configuration:
  OLLAMA_URL              Base URL of Ollama. Default: http://ollama:11434
  OLLAMA_MODEL            Default model to use. Default: llama3.2
  OLLAMA_TIMEOUT_SECONDS  Chat timeout in seconds. Default: 600
  STUB_MODE               Set to "true" to skip Ollama and return a
                          placeholder response. Default: false
"""

import os

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
STUB_MODE = os.getenv("STUB_MODE", "false").lower() == "true"
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "600"))

# Local LLMs can be slow, especially on CPU-only Docker setups.
TIMEOUT = OLLAMA_TIMEOUT_SECONDS


async def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
    options: dict | None = None,
) -> dict:
    """
    Send a conversation to Ollama and return the assistant message dict.
    """
    if STUB_MODE:
        return _stub_message()

    resolved_model = model or OLLAMA_MODEL
    payload: dict = {
        "model": resolved_model,
        "messages": messages,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
    if options:
        payload["options"] = options

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["message"]


def _stub_message() -> dict:
    """
    Deterministic placeholder returned when STUB_MODE=true.
    Matches the structured output format that analyze.py expects
    so the full pipeline still runs without a real model.
    """
    return {
        "role": "assistant",
        "content": (
            "[STUB - Ollama not connected]\n"
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

"""
Ollama LLM client – STUB
=========================
Sends prompts to a locally-running Ollama instance.

Currently **STUB_MODE = True**, so every call returns a canned
placeholder response.  This lets the full pipeline run end-to-end
without needing a GPU or a running Ollama.

To switch to a real model:
  1. Uncomment the `ollama` service in docker-compose.yml.
  2. Pull a model:  docker exec -it maritime_ollama ollama pull llama3
  3. Set STUB_MODE = False below (or use an env var).

TODO: set STUB_MODE via env var so it can be toggled without code change.
"""

import os
import httpx

OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Set to False once Ollama is running and a model is pulled
STUB_MODE = True


async def generate_analysis(prompt: str) -> dict:
    """
    Send *prompt* to Ollama and return the raw response dict.

    STUB: returns a placeholder when STUB_MODE is True.

    Expected Ollama response shape:
        {"model": "llama3", "response": "<text>", "done": true, ...}
    """
    if STUB_MODE:
        return _stub_response(prompt)

    # ── Real Ollama call (uncomment / enable when ready) ──
    # async with httpx.AsyncClient(timeout=60.0) as client:
    #     resp = await client.post(
    #         f"{OLLAMA_URL}/api/generate",
    #         json={
    #             "model":  OLLAMA_MODEL,
    #             "prompt": prompt,
    #             "stream": False,
    #         },
    #     )
    #     resp.raise_for_status()
    #     return resp.json()

    # Fallback if somehow STUB_MODE is False but code above is commented
    return _stub_response(prompt)   # pragma: no cover


# ─── stub ─────────────────────────────────────────────────
def _stub_response(prompt: str) -> dict:
    """
    Deterministic placeholder that proves the pipeline works.
    The response text intentionally mentions that it is a stub
    so it is obvious in the Grafana dashboard.
    """
    return {
        "response": (
            "[STUB – AI analysis] The agent pipeline is working end-to-end. "
            "Connect a real Ollama model to get genuine LLM-generated analyses. "
            "Prompt received was:\n\n"
            f"\"{prompt[:200]}…\""
        ),
        "model": "stub",
        "done":  True,
    }

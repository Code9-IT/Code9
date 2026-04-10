"""Thin HTTP wrapper around the MCP REST adapter.

Usage:
    result = await call_tool("get_vessel_alerts", {"vessel_id": "IMO9300001"})
"""

import os

import httpx

MCP_URL = os.getenv("MCP_URL", "http://mcp:8001").rstrip("/")
MCP_API_KEY = os.getenv("MCP_API_KEY", "").strip()


async def call_tool(tool_name: str, arguments: dict) -> dict:
    """POST to /tools/{tool_name} with the MCP API key and return the JSON body.

    Raises:
        httpx.HTTPStatusError: on non-2xx response from MCP.
        httpx.TimeoutException: if the MCP tool takes longer than 30 s.
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if MCP_API_KEY:
        headers["X-API-Key"] = MCP_API_KEY

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{MCP_URL}/tools/{tool_name}",
            json=arguments,
            headers=headers,
        )
        r.raise_for_status()
        return r.json()

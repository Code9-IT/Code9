"""Thin MCP HTTP client for the dynamic dashboard flow."""

from __future__ import annotations

import os
from typing import Any

import httpx


class MCPClient:
    """Minimal wrapper around the existing MCP REST adapter."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("MCP_URL", "http://mcp:8001")).rstrip("/")
        self.api_key = (api_key if api_key is not None else os.getenv("MCP_API_KEY", "")).strip()
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"X-API-Key": self.api_key}

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(f"{self.base_url}/health", headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/tools/call",
                json={"name": name, "arguments": arguments or {}},
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_vessel_app_status(self, vessel_id: str) -> dict[str, Any]:
        return await self.call_tool("get_vessel_app_status", {"vessel_id": vessel_id})

    async def get_vessel_alerts(self, vessel_id: str, hours: int = 24) -> dict[str, Any]:
        return await self.call_tool(
            "get_vessel_alerts",
            {"vessel_id": vessel_id, "hours": hours},
        )

    async def get_fleet_alerts(self, hours: int = 24, severity: str | None = None) -> dict[str, Any]:
        arguments: dict[str, Any] = {"hours": hours}
        if severity:
            arguments["severity"] = severity
        return await self.call_tool("get_fleet_alerts", arguments)

    async def get_app_metric_history(
        self,
        vessel_id: str,
        app: str,
        metric: str,
        hours: int = 24,
    ) -> dict[str, Any]:
        return await self.call_tool(
            "get_app_metric_history",
            {
                "vessel_id": vessel_id,
                "app": app,
                "metric": metric,
                "hours": hours,
            },
        )

    async def get_app_logs(
        self,
        vessel_id: str,
        app: str,
        *,
        hours: int = 24,
        limit: int = 100,
    ) -> dict[str, Any]:
        return await self.call_tool(
            "get_app_logs",
            {
                "vessel_id": vessel_id,
                "app": app,
                "hours": hours,
                "limit": limit,
            },
        )

    async def get_incident_timeline(
        self,
        vessel_id: str,
        *,
        hours: int = 24,
        app: str | None = None,
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {"vessel_id": vessel_id, "hours": hours}
        if app:
            arguments["app"] = app
        return await self.call_tool("get_incident_timeline", arguments)

    async def get_operational_snapshot(self, vessel_id: str) -> dict[str, Any]:
        return await self.call_tool("get_operational_snapshot", {"vessel_id": vessel_id})

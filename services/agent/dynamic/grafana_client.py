"""Grafana HTTP client for dynamic-dashboard upserts."""

from __future__ import annotations

import os
from typing import Any

import httpx


class GrafanaClient:
    """Minimal Grafana API wrapper."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        public_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("GRAFANA_URL", "http://grafana:3000")).rstrip("/")
        self.public_url = (
            public_url or os.getenv("GRAFANA_PUBLIC_URL", "http://localhost:3000")
        ).rstrip("/")
        self.username = (username or os.getenv("GRAFANA_ADMIN_USER", "admin")).strip()
        self.password = password or os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")
        self.timeout_seconds = timeout_seconds

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds, auth=self._auth()) as client:
            response = await client.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            return response.json()

    async def upsert_dashboard(
        self,
        dashboard: dict[str, Any],
        *,
        folder_id: int = 0,
        message: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "dashboard": dashboard,
            "folderId": folder_id,
            "overwrite": True,
            "message": message or "Dynamic incident dashboard update",
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds, auth=self._auth()) as client:
            response = await client.post(f"{self.base_url}/api/dashboards/db", json=payload)
            response.raise_for_status()
            return response.json()

    def dashboard_url(self, dashboard_uid: str, slug: str = "dynamic-incident-dashboard") -> str:
        return f"{self.public_url}/d/{dashboard_uid}/{slug}"

    def _auth(self) -> tuple[str, str]:
        return (self.username, self.password)

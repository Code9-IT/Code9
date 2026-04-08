"""Grafana HTTP client for deterministic dashboard upserts."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping

import httpx


DEFAULT_GRAFANA_API_URL = "http://grafana:3000"
DEFAULT_GRAFANA_PUBLIC_URL = "http://localhost:3000"


@dataclass(slots=True)
class GrafanaClientSettings:
    """Connection settings for Grafana's HTTP API."""

    api_url: str
    public_url: str
    username: str
    password: str
    timeout_seconds: float = 15.0
    verify_tls: bool = True
    dynamic_folder_title: str | None = None

    @classmethod
    def from_env(cls) -> "GrafanaClientSettings":
        """Create settings from the agent service environment."""
        api_url = (
            os.getenv("GRAFANA_API_URL", "").strip()
            or os.getenv("GRAFANA_URL", "").strip()
            or DEFAULT_GRAFANA_API_URL
        )
        public_url = (
            os.getenv("GRAFANA_PUBLIC_URL", "").strip()
            or os.getenv("GF_SERVER_ROOT_URL", "").strip()
            or os.getenv("GRAFANA_URL", "").strip()
            or DEFAULT_GRAFANA_PUBLIC_URL
        )
        # Accept both agent-specific vars and Grafana's native env names so the
        # writer can run cleanly in docker-compose and direct local setups.
        username = (
            os.getenv("GRAFANA_ADMIN_USER", "").strip()
            or os.getenv("GF_SECURITY_ADMIN_USER", "").strip()
            or "admin"
        )
        password = (
            os.getenv("GRAFANA_ADMIN_PASSWORD", "")
            or os.getenv("GF_SECURITY_ADMIN_PASSWORD", "")
            or "admin"
        )
        timeout_seconds = float(os.getenv("GRAFANA_TIMEOUT_SECONDS", "15"))
        verify_raw = os.getenv("GRAFANA_VERIFY_TLS", "true").strip().lower()
        dynamic_folder_title = os.getenv("GRAFANA_DYNAMIC_DASHBOARD_FOLDER", "").strip() or None
        return cls(
            api_url=api_url.rstrip("/"),
            public_url=public_url.rstrip("/"),
            username=username,
            password=password,
            timeout_seconds=timeout_seconds,
            verify_tls=verify_raw not in {"0", "false", "no"},
            dynamic_folder_title=dynamic_folder_title,
        )


@dataclass(slots=True)
class GrafanaDashboardUpsertResult:
    """Serializable result returned after a dashboard upsert."""

    status: str
    uid: str
    version: int | None
    dashboard_id: int | None
    slug: str | None
    relative_url: str
    url: str


class GrafanaClient:
    """Small async client for Grafana health, folder lookup, and dashboard writes."""

    def __init__(self, settings: GrafanaClientSettings | None = None):
        self.settings = settings or GrafanaClientSettings.from_env()

    async def check_health(self) -> dict[str, Any]:
        """Return the Grafana health payload."""
        response = await self._request("GET", "/api/health")
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Grafana health endpoint returned a non-object payload")
        return payload

    async def get_folder_id(self, title: str | None = None) -> int | None:
        """Resolve a folder title to a Grafana folder id."""
        resolved_title = (title or self.settings.dynamic_folder_title or "").strip()
        if not resolved_title:
            return None
        if resolved_title.lower() == "general":
            return 0

        response = await self._request("GET", "/api/folders", params={"limit": 1000})
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("Grafana folders endpoint returned an unexpected payload")

        for folder in payload:
            folder_title = str(folder.get("title", "")).strip()
            if folder_title == resolved_title:
                folder_id = folder.get("id")
                if isinstance(folder_id, int):
                    return folder_id
                raise RuntimeError(f"Grafana folder '{resolved_title}' did not expose a numeric id")

        raise RuntimeError(f"Grafana folder '{resolved_title}' was not found")

    async def upsert_dashboard(
        self,
        dashboard: Mapping[str, Any],
        *,
        folder_title: str | None = None,
        message: str = "Dynamic incident dashboard update",
    ) -> GrafanaDashboardUpsertResult:
        """Create or overwrite one Grafana dashboard."""
        dashboard_uid = str(dashboard.get("uid") or "").strip()
        if not dashboard_uid:
            raise ValueError("Grafana dashboard payload must include a uid")

        payload: dict[str, Any] = {
            "dashboard": dict(dashboard),
            "overwrite": True,
            "message": message,
        }

        folder_id = await self.get_folder_id(folder_title)
        if folder_id is not None:
            payload["folderId"] = folder_id

        response = await self._request("POST", "/api/dashboards/db", json=payload)
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError("Grafana upsert endpoint returned an unexpected payload")

        relative_url = str(body.get("url") or f"/d/{dashboard_uid}")
        return GrafanaDashboardUpsertResult(
            status=str(body.get("status") or "unknown"),
            uid=str(body.get("uid") or dashboard_uid),
            version=body.get("version") if isinstance(body.get("version"), int) else None,
            dashboard_id=body.get("id") if isinstance(body.get("id"), int) else None,
            slug=str(body.get("slug") or "") or None,
            relative_url=relative_url,
            url=self._absolute_dashboard_url(relative_url),
        )

    def build_dashboard_url(self, uid: str) -> str:
        """Build a public Grafana URL for a dashboard uid."""
        return self._absolute_dashboard_url(f"/d/{uid}")

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        async with httpx.AsyncClient(
            base_url=self.settings.api_url,
            auth=(self.settings.username, self.settings.password),
            timeout=self.settings.timeout_seconds,
            verify=self.settings.verify_tls,
            headers={"Accept": "application/json"},
        ) as client:
            response = await client.request(method, path, **kwargs)

        if response.is_error:
            error_body = response.text.strip()
            if len(error_body) > 400:
                error_body = error_body[:400] + "... [truncated]"
            raise RuntimeError(
                f"Grafana API {method} {path} failed "
                f"({response.status_code}): {error_body or response.reason_phrase}"
            )

        return response

    def _absolute_dashboard_url(self, relative_url: str) -> str:
        normalized_relative = relative_url if relative_url.startswith("/") else f"/{relative_url}"
        return f"{self.settings.public_url}{normalized_relative}"

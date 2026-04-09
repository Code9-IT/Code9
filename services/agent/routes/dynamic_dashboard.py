"""Dynamic dashboard API routes."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from dynamic.orchestrator import DynamicDashboardOrchestrator, TriggerRequest


router = APIRouter(tags=["dynamic-dashboard"])
orchestrator = DynamicDashboardOrchestrator()


class DynamicTriggerRequest(BaseModel):
    mode: Literal["explicit_context", "latest_firing_alert"] = "explicit_context"
    vessel_imo: str | None = None
    app_external_id: str | None = None
    alert_name: str | None = None
    severity: str | None = None
    source_alert_fingerprint: str | None = None
    dry_run: bool = False

    @field_validator("vessel_imo", "app_external_id", "alert_name", "severity", "source_alert_fingerprint")
    @classmethod
    def _normalize_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split()).strip()
        return normalized or None


class DynamicTriggerResponse(BaseModel):
    dashboard_uid: str
    dashboard_url: str
    scenario_key: str
    trigger_mode: str
    generated_at: str
    summary: str
    used_tools: list[str] = Field(default_factory=list)
    dry_run: bool = False
    # Populated only when dry_run=true so callers have a usable fallback
    # if Grafana is unreachable on demo day. Skipped for live runs to keep
    # the response payload small.
    dashboard_json: dict[str, Any] | None = None
    grafana_result: dict[str, Any] | None = None


class DynamicStatusRun(BaseModel):
    created_at: str
    trigger_mode: str
    vessel_imo: str
    app_external_id: str | None = None
    alert_name: str | None = None
    severity: str | None = None
    scenario_key: str
    dashboard_uid: str
    dry_run: bool = False


class DynamicStatusResponse(BaseModel):
    status: str
    dashboard_uid: str
    dashboard_url: str
    grafana_reachable: bool
    mcp_reachable: bool
    recent_runs: list[DynamicStatusRun] = Field(default_factory=list)


@router.post("/dynamic/trigger", response_model=DynamicTriggerResponse)
async def trigger_dynamic_dashboard(request: DynamicTriggerRequest):
    """Trigger one deterministic dynamic-dashboard generation run."""
    try:
        result = await orchestrator.trigger(
            TriggerRequest(
                mode=request.mode,
                dry_run=request.dry_run,
                vessel_imo=request.vessel_imo,
                app_external_id=request.app_external_id,
                alert_name=request.alert_name,
                severity=request.severity,
                source_alert_fingerprint=request.source_alert_fingerprint,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic dashboard trigger failed: {exc}") from exc

    return DynamicTriggerResponse(**result)


@router.get("/dynamic/status", response_model=DynamicStatusResponse)
async def dynamic_dashboard_status():
    """Expose readiness and recent runs for the dynamic-dashboard flow."""
    try:
        result = await orchestrator.status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic dashboard status failed: {exc}") from exc

    return DynamicStatusResponse(**result)

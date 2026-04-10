"""Dynamic dashboard route.

POST /api/v1/dynamic/trigger  — run the two-agent pipeline and push a
                                Grafana dashboard for the specified incident.
GET  /api/v1/dynamic/status   — list recent dynamic dashboard runs.
"""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from db import get_pool
from dynamic.orchestrator import DynamicDashboardResult, run as orchestrate

router = APIRouter(tags=["dynamic-dashboard"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class TriggerRequest(BaseModel):
    vessel_imo: str = Field(
        ...,
        description="IMO number of the vessel, e.g. IMO9300001",
        examples=["IMO9300001"],
    )
    app_external_id: str = Field(
        ...,
        description="Application external ID, e.g. data-quality-processor",
        examples=["data-quality-processor"],
    )
    alert_name: str = Field(
        default="",
        description="Name of the triggering alert (used for scenario classification)",
        examples=["ServiceUnavailable"],
    )
    alert_type: str = Field(
        default="",
        description="Alert type string (optional, supplements alert_name for classification)",
    )
    severity: str = Field(
        default="",
        description="Alert severity: info | warning | high | critical",
        examples=["critical"],
    )
    trigger_mode: str = Field(
        default="api",
        description="Tag stored in the run log to identify how the trigger was invoked",
        examples=["api", "demo", "grafana_alert"],
    )
    dry_run: bool = Field(
        default=False,
        description="Build the dashboard but do NOT push it to Grafana",
    )
    fingerprint: Optional[str] = Field(
        default=None,
        description="Optional alert fingerprint for run deduplication tracking",
    )


class TriggerResponse(BaseModel):
    run_id: str
    vessel_imo: str
    app_external_id: str
    alert_name: str
    scenario_key: str
    scenario_title: str
    dashboard_uid: str
    grafana_url: str
    summary: str
    used_tools: list[str]
    dry_run: bool


class RunLogEntry(BaseModel):
    id: str
    created_at: str
    trigger_mode: str
    vessel_imo: str
    app_external_id: str
    alert_name: Optional[str]
    severity: Optional[str]
    scenario_key: str
    dashboard_uid: str
    dry_run: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response(result: DynamicDashboardResult) -> TriggerResponse:
    return TriggerResponse(
        run_id=result.run_id,
        vessel_imo=result.vessel_imo,
        app_external_id=result.app_external_id,
        alert_name=result.alert_name,
        scenario_key=result.scenario_key,
        scenario_title=result.scenario_title,
        dashboard_uid=result.dashboard_uid,
        grafana_url=result.grafana_url,
        summary=result.summary,
        used_tools=result.used_tools,
        dry_run=result.dry_run,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/dynamic/trigger",
    response_model=TriggerResponse,
    summary="Trigger a dynamic incident dashboard",
    description=(
        "Runs the two-agent pipeline: Agent 1 gathers incident context via MCP "
        "tools; Agent 2 classifies the scenario and pushes a tailored Grafana "
        "dashboard to the stable UID `maritime_dynamic_incident`."
    ),
)
async def trigger_dynamic_dashboard(body: TriggerRequest) -> TriggerResponse:
    pool = get_pool()
    try:
        result = await orchestrate(
            pool,
            vessel_imo=body.vessel_imo,
            app_external_id=body.app_external_id,
            alert_name=body.alert_name,
            alert_type=body.alert_type,
            severity=body.severity,
            trigger_mode=body.trigger_mode,
            dry_run=body.dry_run,
            fingerprint=body.fingerprint,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _to_response(result)


@router.get(
    "/dynamic/status",
    response_model=list[RunLogEntry],
    summary="List recent dynamic dashboard runs",
)
async def get_dynamic_status(
    limit: int = Query(default=20, ge=1, le=200, description="Max rows to return"),
    vessel_imo: Optional[str] = Query(default=None, description="Filter by vessel IMO"),
) -> list[RunLogEntry]:
    pool = get_pool()
    try:
        async with pool.acquire() as conn:
            if vessel_imo:
                rows = await conn.fetch(
                    """
                    SELECT id, created_at, trigger_mode, vessel_imo,
                           app_external_id, alert_name, severity,
                           scenario_key, dashboard_uid, dry_run
                    FROM dynamic_dashboard_runs
                    WHERE vessel_imo = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    vessel_imo,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, created_at, trigger_mode, vessel_imo,
                           app_external_id, alert_name, severity,
                           scenario_key, dashboard_uid, dry_run
                    FROM dynamic_dashboard_runs
                    ORDER BY created_at DESC
                    LIMIT $1
                    """,
                    limit,
                )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [
        RunLogEntry(
            id=str(r["id"]),
            created_at=r["created_at"].isoformat(),
            trigger_mode=r["trigger_mode"],
            vessel_imo=r["vessel_imo"],
            app_external_id=r["app_external_id"],
            alert_name=r["alert_name"],
            severity=r["severity"],
            scenario_key=r["scenario_key"],
            dashboard_uid=r["dashboard_uid"],
            dry_run=r["dry_run"],
        )
        for r in rows
    ]

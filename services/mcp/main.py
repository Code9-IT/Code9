"""
Maritime MCP Server
===================
FastAPI entry point for MCP-style tools exposed over HTTP.

This is a REST adapter that exposes DB query tools using MCP-style
tool definitions (name + inputSchema). The agent calls these via HTTP.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
import secrets
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

from db import close_pool, get_pool, init_pool

load_dotenv()

MCP_API_KEY = os.getenv("MCP_API_KEY", "").strip()


def _cors_allow_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    if not MCP_API_KEY:
        print("[mcp] WARNING: MCP_API_KEY is empty; MCP auth is effectively disabled.")
    yield
    await close_pool()


app = FastAPI(
    title="Maritime MCP Server",
    description="HTTP wrapper exposing MCP tool definitions for maritime data.",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow local dev + Grafana/agent access
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Tool definitions (MCP-style metadata)
# -----------------------------------------------------------------------------
TOOLS = [
    {
        "name": "get_telemetry",
        "description": "Fetch recent telemetry readings for a vessel sensor.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_id": {
                    "type": "string",
                    "description": "Vessel identifier, e.g. vessel_001",
                },
                "sensor_name": {
                    "type": "string",
                    "description": "Telemetry sensor name, e.g. engine_temp",
                },
                "minutes_back": {
                    "type": "integer",
                    "description": "How many minutes to look back",
                    "default": 60,
                    "minimum": 1,
                    "maximum": 1440,
                },
            },
            "required": ["vessel_id", "sensor_name"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "vessel_id": {"type": "string"},
                "sensor_name": {"type": "string"},
                "minutes_back": {"type": "integer"},
                "readings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "string", "format": "date-time"},
                            "value": {"type": "number"},
                        },
                        "required": ["timestamp", "value"],
                    },
                },
            },
            "required": ["vessel_id", "sensor_name", "minutes_back", "readings"],
        },
    },
    {
        "name": "get_events",
        "description": "Fetch recent anomaly events.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_id": {
                    "type": ["string", "null"],
                    "description": "Optional vessel filter",
                },
                "acknowledged": {
                    "type": ["boolean", "null"],
                    "description": "Optional acknowledgement filter",
                },
            },
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "vessel_id": {"type": "string"},
                            "sensor_name": {"type": "string"},
                            "event_type": {"type": "string"},
                            "severity": {"type": "string"},
                            "details": {"type": ["string", "null"]},
                            "acknowledged": {"type": "boolean"},
                            "acknowledged_by": {"type": ["string", "null"]},
                            "acknowledged_at": {
                                "type": ["string", "null"],
                                "format": "date-time",
                            },
                        },
                        "required": [
                            "id",
                            "timestamp",
                            "vessel_id",
                            "sensor_name",
                            "event_type",
                            "severity",
                            "details",
                            "acknowledged",
                            "acknowledged_by",
                            "acknowledged_at",
                        ],
                    },
                },
            },
            "required": ["events"],
        },
    },
    {
        "name": "get_analysis",
        "description": "Fetch the latest AI analysis for an event.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "integer",
                    "description": "Event id",
                }
            },
            "required": ["event_id"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "integer"},
                "analysis": {
                    "type": ["object", "null"],
                    "properties": {
                        "id": {"type": "integer"},
                        "event_id": {"type": "integer"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "analysis_mode": {"type": "string"},
                        "analysis_text": {"type": ["string", "null"]},
                        "suggested_actions": {
                            "type": ["array", "null"],
                            "items": {"type": "string"},
                        },
                        "confidence": {"type": ["number", "null"]},
                        "model_used": {"type": ["string", "null"]},
                        "status": {"type": "string"},
                    },
                    "required": [
                        "id",
                        "event_id",
                        "timestamp",
                        "analysis_mode",
                        "analysis_text",
                        "suggested_actions",
                        "confidence",
                        "model_used",
                        "status",
                    ],
                },
            },
            "required": ["event_id", "analysis"],
        },
    },
    {
        "name": "get_vessel_app_status",
        "description": (
            "Fetch latest UDS app status, latest metrics, and active alert count "
            "for all applications on one vessel."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_id": {
                    "type": "string",
                    "description": (
                        "Vessel identifier in UDS schema "
                        "(imo_nr, external_id, name, or udslocations.id)"
                    ),
                },
            },
            "required": ["vessel_id"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "vessel": {"type": "object"},
                "application_count": {"type": "integer"},
                "applications": {"type": "array"},
                "generated_at": {"type": "string", "format": "date-time"},
            },
            "required": ["vessel", "application_count", "applications", "generated_at"],
        },
    },
    {
        "name": "get_vessel_alerts",
        "description": (
            "Fetch active or unresolved UDS alerts for a vessel in the last N hours."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_id": {
                    "type": "string",
                    "description": (
                        "Vessel identifier in UDS schema "
                        "(imo_nr, external_id, name, or udslocations.id)"
                    ),
                },
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to search",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168,
                },
            },
            "required": ["vessel_id"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "vessel": {"type": "object"},
                "hours": {"type": "integer"},
                "count": {"type": "integer"},
                "alerts": {"type": "array"},
            },
            "required": ["vessel", "hours", "count", "alerts"],
        },
    },
    {
        "name": "get_app_metric_history",
        "description": (
            "Fetch UDS metric history for one vessel, one app, and one metric in the "
            "last N hours."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_id": {
                    "type": "string",
                    "description": (
                        "Vessel identifier in UDS schema "
                        "(imo_nr, external_id, name, or udslocations.id)"
                    ),
                },
                "app": {
                    "type": "string",
                    "description": (
                        "Application selector (app_id, external_id, name, or applications.id)"
                    ),
                },
                "metric": {
                    "type": "string",
                    "description": "Metric name, e.g. service_up",
                },
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to return",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 720,
                },
            },
            "required": ["vessel_id", "app", "metric"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "vessel": {"type": "object"},
                "app": {"type": "string"},
                "metric": {"type": "string"},
                "hours": {"type": "integer"},
                "point_count": {"type": "integer"},
                "series": {"type": "array"},
                "metadata": {"type": "object"},
            },
            "required": ["vessel", "app", "metric", "hours", "point_count", "series"],
        },
    },
    {
        "name": "get_app_logs",
        "description": (
            "Fetch lightweight UDS logs or log-like incident context for one vessel "
            "application in the last N hours."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_id": {
                    "type": "string",
                    "description": (
                        "Vessel identifier in UDS schema "
                        "(imo_nr, external_id, name, or udslocations.id)"
                    ),
                },
                "app": {
                    "type": "string",
                    "description": (
                        "Application selector (external_id, name, or applications.id)"
                    ),
                },
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to return",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 720,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of log rows to return",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000,
                },
            },
            "required": ["vessel_id", "app"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "vessel": {"type": "object"},
                "app": {"type": "string"},
                "hours": {"type": "integer"},
                "count": {"type": "integer"},
                "logs": {"type": "array"},
                "metadata": {"type": "object"},
            },
            "required": ["vessel", "app", "hours", "count", "logs"],
        },
    },
    # -----------------------------------------------------------------
    # Scope 2 fleet-level and incident tools
    # -----------------------------------------------------------------
    {
        "name": "get_fleet_status",
        "description": (
            "Fetch operational status of all vessels in the fleet: app counts, "
            "active alerts, affected apps, latest metric freshness, and overall "
            "vessel health."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "vessel_count": {"type": "integer"},
                "vessels": {"type": "array"},
                "generated_at": {"type": "string", "format": "date-time"},
            },
            "required": ["vessel_count", "vessels", "generated_at"],
        },
    },
    {
        "name": "get_fleet_alerts",
        "description": (
            "Fetch active or unresolved alerts across the entire fleet in the "
            "last N hours, optionally filtered by severity."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to search",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168,
                },
                "severity": {
                    "type": ["string", "null"],
                    "description": (
                        "Optional severity filter (e.g. critical, warning)"
                    ),
                },
            },
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "hours": {"type": "integer"},
                "severity_filter": {"type": ["string", "null"]},
                "count": {"type": "integer"},
                "alerts": {"type": "array"},
            },
            "required": ["hours", "severity_filter", "count", "alerts"],
        },
    },
    {
        "name": "get_cross_vessel_correlation",
        "description": (
            "Find correlated issues across the fleet: applications or alert "
            "types that appear on more than one vessel simultaneously."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to search",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168,
                },
            },
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "hours": {"type": "integer"},
                "correlated_apps": {"type": "array"},
                "correlated_alert_types": {"type": "array"},
            },
            "required": ["hours", "correlated_apps", "correlated_alert_types"],
        },
    },
    {
        "name": "get_incident_timeline",
        "description": (
            "Fetch a time-ordered list of alerts and logs for one vessel, "
            "combining both into a single chronological timeline for incident "
            "investigation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_id": {
                    "type": "string",
                    "description": (
                        "Vessel identifier in UDS schema "
                        "(imo_nr, external_id, name, or udslocations.id)"
                    ),
                },
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to search",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168,
                },
                "app": {
                    "type": ["string", "null"],
                    "description": (
                        "Optional application filter "
                        "(external_id, name, or applications.id)"
                    ),
                },
            },
            "required": ["vessel_id"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "vessel": {"type": "object"},
                "hours": {"type": "integer"},
                "app_filter": {"type": ["string", "null"]},
                "count": {"type": "integer"},
                "timeline": {"type": "array"},
            },
            "required": ["vessel", "hours", "app_filter", "count", "timeline"],
        },
    },
    {
        "name": "get_operational_snapshot",
        "description": (
            "Fetch a support-oriented operational snapshot of one vessel: "
            "vessel info, all app statuses, active alerts, recent logs, and "
            "connectivity summary."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_id": {
                    "type": "string",
                    "description": (
                        "Vessel identifier in UDS schema "
                        "(imo_nr, external_id, name, or udslocations.id)"
                    ),
                },
            },
            "required": ["vessel_id"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "vessel": {"type": "object"},
                "applications": {"type": "array"},
                "active_alerts": {"type": "array"},
                "recent_logs": {"type": "array"},
                "connectivity": {"type": "object"},
                "generated_at": {"type": "string", "format": "date-time"},
            },
            "required": [
                "vessel",
                "applications",
                "active_alerts",
                "recent_logs",
                "connectivity",
                "generated_at",
            ],
        },
    },
]


# -----------------------------------------------------------------------------
# Request models
# -----------------------------------------------------------------------------
class GetTelemetryArgs(BaseModel):
    vessel_id: str = Field(..., description="Vessel identifier, e.g. vessel_001")
    sensor_name: str = Field(..., description="Telemetry sensor name, e.g. engine_temp")
    minutes_back: int = Field(60, ge=1, le=1440, description="How many minutes to look back")


class GetEventsArgs(BaseModel):
    vessel_id: Optional[str] = Field(None, description="Optional vessel filter")
    acknowledged: Optional[bool] = Field(None, description="Optional acknowledgement filter")


class GetAnalysisArgs(BaseModel):
    event_id: int = Field(..., ge=1, description="Event id")


class GetVesselAppStatusArgs(BaseModel):
    vessel_id: str = Field(
        ...,
        description=(
            "Vessel identifier in UDS schema "
            "(imo_nr, external_id, name, or udslocations.id)"
        ),
    )


class GetVesselAlertsArgs(BaseModel):
    vessel_id: str = Field(
        ...,
        description=(
            "Vessel identifier in UDS schema "
            "(imo_nr, external_id, name, or udslocations.id)"
        ),
    )
    hours: int = Field(24, ge=1, le=168, description="How many hours to look back")


class GetAppMetricHistoryArgs(BaseModel):
    vessel_id: str = Field(
        ...,
        description=(
            "Vessel identifier in UDS schema "
            "(imo_nr, external_id, name, or udslocations.id)"
        ),
    )
    app: str = Field(
        ...,
        description="Application selector (app_id, external_id, name, or applications.id)",
    )
    metric: str = Field(..., description="Metric name, e.g. service_up")
    hours: int = Field(24, ge=1, le=720, description="How many hours to look back")


class GetAppLogsArgs(BaseModel):
    vessel_id: str = Field(
        ...,
        description=(
            "Vessel identifier in UDS schema "
            "(imo_nr, external_id, name, or udslocations.id)"
        ),
    )
    app: str = Field(
        ...,
        description="Application selector (external_id, name, or applications.id)",
    )
    hours: int = Field(24, ge=1, le=720, description="How many hours to look back")
    limit: int = Field(100, ge=1, le=1000, description="Maximum rows to return")


class GetFleetStatusArgs(BaseModel):
    pass


class GetFleetAlertsArgs(BaseModel):
    hours: int = Field(24, ge=1, le=168, description="How many hours to look back")
    severity: Optional[str] = Field(
        None, description="Optional severity filter (e.g. critical, warning)"
    )


class GetCrossVesselCorrelationArgs(BaseModel):
    hours: int = Field(24, ge=1, le=168, description="How many hours to look back")


class GetIncidentTimelineArgs(BaseModel):
    vessel_id: str = Field(
        ...,
        description=(
            "Vessel identifier in UDS schema "
            "(imo_nr, external_id, name, or udslocations.id)"
        ),
    )
    hours: int = Field(24, ge=1, le=168, description="How many hours to look back")
    app: Optional[str] = Field(
        None,
        description="Optional application filter (external_id, name, or applications.id)",
    )


class GetOperationalSnapshotArgs(BaseModel):
    vessel_id: str = Field(
        ...,
        description=(
            "Vessel identifier in UDS schema "
            "(imo_nr, external_id, name, or udslocations.id)"
        ),
    )


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Auth and DB helpers
# -----------------------------------------------------------------------------
def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if not MCP_API_KEY:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, MCP_API_KEY):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")


def _normalize_error(exc: Exception) -> None:
    message = str(exc).lower()
    if "does not exist" in message and (
        "udslocations" in message
        or "applications" in message
        or "metric_samples" in message
        or "alerts" in message
        or "app_logs" in message
        or "uds_location_application_instances" in message
    ):
        raise HTTPException(
            status_code=503,
            detail="UDS schema is not available yet. Apply db/init/003_uds.sql first.",
        ) from exc
    raise exc


async def _resolve_uds_vessel(vessel_id: str) -> dict[str, Any]:
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            SELECT id, external_id, name, imo_nr
            FROM udslocations
            WHERE id::text = $1
               OR imo_nr = $1
               OR external_id = $1
               OR LOWER(name) = LOWER($1)
            ORDER BY CASE
                WHEN imo_nr = $1 THEN 0
                WHEN external_id = $1 THEN 1
                WHEN id::text = $1 THEN 2
                ELSE 3
            END
            LIMIT 1;
            """,
            vessel_id,
        )
    except Exception as exc:
        _normalize_error(exc)

    if row is None:
        raise HTTPException(status_code=404, detail=f"UDS vessel not found: {vessel_id}")

    return {
        "input_vessel_id": vessel_id,
        "uds_location_id": str(row["id"]),
        "external_id": row["external_id"],
        "name": row["name"],
        "imo_nr": row["imo_nr"],
    }


async def _resolve_uds_application(vessel: dict[str, Any], app: str) -> dict[str, Any]:
    pool = get_pool()
    try:
        row = await pool.fetchrow(
            """
            SELECT a.id, a.external_id, a.name, a.app_type
            FROM uds_location_application_instances uai
            JOIN applications a ON a.id = uai.application_instance_id
            WHERE uai.uds_location_id = $1::uuid
              AND (
                a.id::text = $2
                OR LOWER(a.external_id) = LOWER($2)
                OR LOWER(a.name) = LOWER($2)
              )
            ORDER BY CASE
                WHEN LOWER(a.external_id) = LOWER($2) THEN 0
                WHEN a.id::text = $2 THEN 1
                ELSE 2
            END
            LIMIT 1;
            """,
            vessel["uds_location_id"],
            app,
        )
    except Exception as exc:
        _normalize_error(exc)

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"UDS app not found on vessel {vessel['input_vessel_id']}: {app}",
        )

    return {
        "input_app": app,
        "application_id": str(row["id"]),
        "external_id": row["external_id"],
        "name": row["name"],
        "app_type": row["app_type"],
    }


def _derive_app_status(metrics: list[dict[str, Any]], active_alert_count: int) -> str:
    metric_values = {metric["metric_name"]: metric["value"] for metric in metrics}
    service_up = metric_values.get("service_up")
    health_check = metric_values.get("health_check_status")

    if (service_up is not None and service_up <= 0) or (
        health_check is not None and health_check <= 0
    ):
        return "down"
    if active_alert_count > 0:
        return "degraded"
    if metrics:
        return "healthy"
    return "unknown"


# -----------------------------------------------------------------------------
# Tool handlers
# -----------------------------------------------------------------------------
async def _run_get_telemetry(args: GetTelemetryArgs) -> dict[str, Any]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT timestamp, value
        FROM telemetry
        WHERE vessel_id = $1
          AND sensor_name = $2
          AND timestamp >= NOW() - ($3 * INTERVAL '1 minute')
        ORDER BY timestamp DESC;
        """,
        args.vessel_id,
        args.sensor_name,
        args.minutes_back,
    )

    readings = [
        {"timestamp": row["timestamp"].isoformat(), "value": row["value"]}
        for row in rows
    ]

    return {
        "vessel_id": args.vessel_id,
        "sensor_name": args.sensor_name,
        "minutes_back": args.minutes_back,
        "readings": readings,
    }


async def _run_get_events(args: GetEventsArgs) -> dict[str, Any]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, timestamp, vessel_id, sensor_name, event_type, severity, details,
               acknowledged, acknowledged_by, acknowledged_at
        FROM events
        WHERE ($1::text IS NULL OR vessel_id = $1)
          AND ($2::boolean IS NULL OR acknowledged = $2)
        ORDER BY timestamp DESC
        LIMIT 200;
        """,
        args.vessel_id,
        args.acknowledged,
    )

    events = [
        {
            "id": row["id"],
            "timestamp": row["timestamp"].isoformat(),
            "vessel_id": row["vessel_id"],
            "sensor_name": row["sensor_name"],
            "event_type": row["event_type"],
            "severity": row["severity"],
            "details": row["details"],
            "acknowledged": row["acknowledged"],
            "acknowledged_by": row["acknowledged_by"],
            "acknowledged_at": _iso(row["acknowledged_at"]),
        }
        for row in rows
    ]

    return {"events": events}


async def _run_get_analysis(args: GetAnalysisArgs) -> dict[str, Any]:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, event_id, timestamp, analysis_mode, analysis_text, suggested_actions,
               confidence, model_used, status
        FROM ai_analyses
        WHERE event_id = $1
        ORDER BY CASE WHEN COALESCE(analysis_mode, 'full') = 'full' THEN 0 ELSE 1 END,
                 timestamp DESC
        LIMIT 1;
        """,
        args.event_id,
    )

    if row is None:
        return {"event_id": args.event_id, "analysis": None}

    analysis = {
        "id": row["id"],
        "event_id": row["event_id"],
        "timestamp": row["timestamp"].isoformat(),
        "analysis_mode": row["analysis_mode"] or "full",
        "analysis_text": row["analysis_text"],
        "suggested_actions": row["suggested_actions"],
        "confidence": row["confidence"],
        "model_used": row["model_used"],
        "status": row["status"],
    }

    return {"event_id": args.event_id, "analysis": analysis}


async def _run_get_vessel_app_status(args: GetVesselAppStatusArgs) -> dict[str, Any]:
    vessel = await _resolve_uds_vessel(args.vessel_id)
    pool = get_pool()

    try:
        app_rows = await pool.fetch(
            """
            SELECT a.id, a.external_id, a.name, a.app_type
            FROM uds_location_application_instances uai
            JOIN applications a ON a.id = uai.application_instance_id
            WHERE uai.uds_location_id = $1::uuid
            ORDER BY a.name ASC;
            """,
            vessel["uds_location_id"],
        )

        latest_metric_rows = await pool.fetch(
            """
            SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
                   ms.application_instance_id,
                   ms.app_id,
                   ms.metric_name,
                   ms.time,
                   ms.value,
                   ms.min_value,
                   ms.max_value,
                   ms.metric_type,
                   ms.metric_unit
            FROM metric_samples ms
            WHERE ms.imo_nr = $1
            ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC;
            """,
            vessel["imo_nr"],
        )

        alert_rows = await pool.fetch(
            """
            SELECT application_id, COUNT(*)::int AS active_alert_count
            FROM alerts
            WHERE uds_location_id = $1::uuid
              AND (
                status IS NULL
                OR LOWER(status) NOT IN ('resolved', 'closed', 'completed', 'cleared')
              )
              AND (ends_at IS NULL OR ends_at > NOW())
            GROUP BY application_id;
            """,
            vessel["uds_location_id"],
        )
    except Exception as exc:
        _normalize_error(exc)

    metrics_by_application_id: dict[str, list[dict[str, Any]]] = {}
    metrics_by_app_key: dict[str, list[dict[str, Any]]] = {}

    for row in latest_metric_rows:
        metric = {
            "metric_name": row["metric_name"],
            "time": _iso(row["time"]),
            "value": row["value"],
            "min_value": row["min_value"],
            "max_value": row["max_value"],
            "metric_type": row["metric_type"],
            "metric_unit": row["metric_unit"],
        }

        app_instance_id = row["application_instance_id"]
        if app_instance_id is not None:
            metrics_by_application_id.setdefault(str(app_instance_id), []).append(metric)

        app_key = (row["app_id"] or "").strip().lower()
        if app_key:
            metrics_by_app_key.setdefault(app_key, []).append(metric)

    active_alerts_by_app = {
        str(row["application_id"]): row["active_alert_count"] for row in alert_rows
    }

    applications = []
    for app_row in app_rows:
        app_id = str(app_row["id"])
        app_key = (app_row["external_id"] or "").strip().lower()
        latest_metrics = metrics_by_application_id.get(app_id) or metrics_by_app_key.get(app_key, [])
        latest_metrics.sort(key=lambda metric: metric["metric_name"])

        latest_metric_at = max(
            (metric["time"] for metric in latest_metrics if metric["time"] is not None),
            default=None,
        )
        active_alert_count = active_alerts_by_app.get(app_id, 0)

        applications.append(
            {
                "application_id": app_id,
                "external_id": app_row["external_id"],
                "name": app_row["name"],
                "app_type": app_row["app_type"],
                "status": _derive_app_status(latest_metrics, active_alert_count),
                "active_alert_count": active_alert_count,
                "latest_metric_at": latest_metric_at,
                "latest_metrics": latest_metrics,
            }
        )

    return {
        "vessel": vessel,
        "application_count": len(applications),
        "applications": applications,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _run_get_vessel_alerts(args: GetVesselAlertsArgs) -> dict[str, Any]:
    vessel = await _resolve_uds_vessel(args.vessel_id)
    pool = get_pool()

    try:
        rows = await pool.fetch(
            """
            SELECT al.id,
                   al.uds_location_id,
                   al.application_id,
                   a.external_id AS app_external_id,
                   a.name AS app_name,
                   al.alert_name,
                   al.severity,
                   al.status,
                   al.alert_type,
                   al.fingerprint,
                   al.labels,
                   al.annotations,
                   al.starts_at,
                   al.ends_at,
                   al.received_at
            FROM alerts al
            LEFT JOIN applications a ON a.id = al.application_id
            WHERE al.uds_location_id = $1::uuid
              AND al.received_at >= NOW() - ($2 * INTERVAL '1 hour')
              AND (
                al.status IS NULL
                OR LOWER(al.status) NOT IN ('resolved', 'closed', 'completed', 'cleared')
              )
              AND (al.ends_at IS NULL OR al.ends_at > NOW())
            ORDER BY al.received_at DESC
            LIMIT 500;
            """,
            vessel["uds_location_id"],
            args.hours,
        )
    except Exception as exc:
        _normalize_error(exc)

    alerts = [
        {
            "id": str(row["id"]),
            "uds_location_id": str(row["uds_location_id"]),
            "application_id": str(row["application_id"]) if row["application_id"] else None,
            "app_external_id": row["app_external_id"],
            "app_name": row["app_name"],
            "alert_name": row["alert_name"],
            "severity": row["severity"],
            "status": row["status"],
            "alert_type": row["alert_type"],
            "fingerprint": row["fingerprint"],
            "labels": row["labels"],
            "annotations": row["annotations"],
            "starts_at": _iso(row["starts_at"]),
            "ends_at": _iso(row["ends_at"]),
            "received_at": _iso(row["received_at"]),
        }
        for row in rows
    ]

    return {
        "vessel": vessel,
        "hours": args.hours,
        "count": len(alerts),
        "alerts": alerts,
    }


async def _run_get_app_metric_history(args: GetAppMetricHistoryArgs) -> dict[str, Any]:
    vessel = await _resolve_uds_vessel(args.vessel_id)
    pool = get_pool()

    try:
        rows = await pool.fetch(
            """
            SELECT ms.time,
                   ms.value,
                   ms.min_value,
                   ms.max_value,
                   ms.metric_type,
                   ms.metric_unit,
                   ms.app_id,
                   ms.application_instance_id,
                   a.external_id AS app_external_id,
                   a.name AS app_name,
                   a.app_type AS app_type
            FROM metric_samples ms
            LEFT JOIN applications a ON a.id = ms.application_instance_id
            WHERE ms.imo_nr = $1
              AND LOWER(ms.metric_name) = LOWER($3)
              AND ms.time >= NOW() - ($4 * INTERVAL '1 hour')
              AND (
                LOWER(ms.app_id) = LOWER($2)
                OR LOWER(COALESCE(a.external_id, '')) = LOWER($2)
                OR LOWER(COALESCE(a.name, '')) = LOWER($2)
                OR COALESCE(a.id::text, '') = $2
              )
            ORDER BY ms.time ASC
            LIMIT 5000;
            """,
            vessel["imo_nr"],
            args.app,
            args.metric,
            args.hours,
        )
    except Exception as exc:
        _normalize_error(exc)

    series = [
        {
            "timestamp": _iso(row["time"]),
            "value": row["value"],
            "min_value": row["min_value"],
            "max_value": row["max_value"],
        }
        for row in rows
    ]

    metadata = {
        "app_id": rows[0]["app_id"] if rows else None,
        "application_id": str(rows[0]["application_instance_id"]) if rows and rows[0]["application_instance_id"] else None,
        "app_external_id": rows[0]["app_external_id"] if rows else None,
        "app_name": rows[0]["app_name"] if rows else None,
        "app_type": rows[0]["app_type"] if rows else None,
        "metric_type": rows[0]["metric_type"] if rows else None,
        "metric_unit": rows[0]["metric_unit"] if rows else None,
    }

    return {
        "vessel": vessel,
        "app": args.app,
        "metric": args.metric,
        "hours": args.hours,
        "point_count": len(series),
        "series": series,
        "metadata": metadata,
    }


async def _run_get_app_logs(args: GetAppLogsArgs) -> dict[str, Any]:
    vessel = await _resolve_uds_vessel(args.vessel_id)
    app_meta = await _resolve_uds_application(vessel, args.app)
    pool = get_pool()

    try:
        rows = await pool.fetch(
            """
            SELECT l.id,
                   l.logged_at,
                   l.level,
                   l.source,
                   l.message,
                   l.context,
                   l.alert_id,
                   l.correlation_key,
                   l.application_id,
                   COALESCE(a.external_id, l.app_external_id) AS app_external_id,
                   a.name AS app_name,
                   a.app_type AS app_type
            FROM app_logs l
            LEFT JOIN applications a ON a.id = l.application_id
            WHERE l.uds_location_id = $1::uuid
              AND l.logged_at >= NOW() - ($4 * INTERVAL '1 hour')
              AND (
                l.application_id = $2::uuid
                OR LOWER(COALESCE(l.app_external_id, '')) = LOWER($3)
              )
            ORDER BY l.logged_at DESC
            LIMIT $5;
            """,
            vessel["uds_location_id"],
            app_meta["application_id"],
            app_meta["external_id"],
            args.hours,
            args.limit,
        )
    except Exception as exc:
        _normalize_error(exc)

    logs = [
        {
            "id": str(row["id"]),
            "timestamp": _iso(row["logged_at"]),
            "level": row["level"],
            "source": row["source"],
            "message": row["message"],
            "alert_id": str(row["alert_id"]) if row["alert_id"] else None,
            "correlation_key": row["correlation_key"],
            "application_id": (
                str(row["application_id"]) if row["application_id"] else None
            ),
            "app_external_id": row["app_external_id"],
            "app_name": row["app_name"] or app_meta["name"],
            "context": row["context"],
        }
        for row in rows
    ]

    metadata = {
        "application_id": app_meta["application_id"],
        "app_external_id": app_meta["external_id"],
        "app_name": app_meta["name"],
        "app_type": app_meta["app_type"],
    }

    return {
        "vessel": vessel,
        "app": args.app,
        "hours": args.hours,
        "count": len(logs),
        "logs": logs,
        "metadata": metadata,
    }


# -----------------------------------------------------------------------------
# Scope 2 tool handlers
# -----------------------------------------------------------------------------
async def _run_get_fleet_status(args: GetFleetStatusArgs) -> dict[str, Any]:
    pool = get_pool()

    try:
        vessel_rows = await pool.fetch(
            """
            SELECT u.id, u.external_id, u.name, u.imo_nr
            FROM udslocations u
            ORDER BY u.name ASC;
            """
        )

        alert_rows = await pool.fetch(
            """
            SELECT al.uds_location_id,
                   al.application_id,
                   COUNT(*)::int AS alert_count
            FROM alerts al
            WHERE (
                al.status IS NULL
                OR LOWER(al.status) NOT IN ('resolved', 'closed', 'completed', 'cleared')
            )
            AND (al.ends_at IS NULL OR al.ends_at > NOW())
            GROUP BY al.uds_location_id, al.application_id;
            """
        )

        metric_rows = await pool.fetch(
            """
            SELECT ms.imo_nr,
                   ms.application_instance_id,
                   MAX(ms.time) AS latest_metric_time
            FROM metric_samples ms
            GROUP BY ms.imo_nr, ms.application_instance_id;
            """
        )

        app_count_rows = await pool.fetch(
            """
            SELECT uai.uds_location_id, COUNT(*)::int AS app_count
            FROM uds_location_application_instances uai
            GROUP BY uai.uds_location_id;
            """
        )

        # Per-app latest metrics for status derivation
        app_status_rows = await pool.fetch(
            """
            SELECT DISTINCT ON (ms.imo_nr, ms.application_instance_id, ms.metric_name)
                   ms.imo_nr,
                   ms.application_instance_id,
                   ms.metric_name,
                   ms.value
            FROM metric_samples ms
            WHERE ms.metric_name IN ('service_up', 'health_check_status')
            ORDER BY ms.imo_nr, ms.application_instance_id, ms.metric_name, ms.time DESC;
            """
        )

        # Critical-severity alerts per vessel (for status derivation)
        critical_alert_rows = await pool.fetch(
            """
            SELECT al.uds_location_id, COUNT(*)::int AS critical_count
            FROM alerts al
            WHERE LOWER(al.severity) = 'critical'
              AND (
                al.status IS NULL
                OR LOWER(al.status) NOT IN ('resolved', 'closed', 'completed', 'cleared')
              )
              AND (al.ends_at IS NULL OR al.ends_at > NOW())
            GROUP BY al.uds_location_id;
            """
        )
    except Exception as exc:
        _normalize_error(exc)

    # Build lookup structures
    alerts_by_vessel: dict[str, dict[str, int]] = {}
    for row in alert_rows:
        vid = str(row["uds_location_id"])
        aid = str(row["application_id"]) if row["application_id"] else "_none"
        alerts_by_vessel.setdefault(vid, {})[aid] = row["alert_count"]

    latest_by_vessel: dict[str, datetime] = {}
    for row in metric_rows:
        imo = row["imo_nr"]
        t = row["latest_metric_time"]
        if t and (imo not in latest_by_vessel or t > latest_by_vessel[imo]):
            latest_by_vessel[imo] = t

    app_counts: dict[str, int] = {
        str(row["uds_location_id"]): row["app_count"] for row in app_count_rows
    }

    # Check if any app is down per vessel (service_up=0 or health_check=0)
    down_apps_by_imo: dict[str, set[str]] = {}
    for row in app_status_rows:
        if row["value"] is not None and row["value"] <= 0:
            down_apps_by_imo.setdefault(row["imo_nr"], set()).add(
                str(row["application_instance_id"]) if row["application_instance_id"] else ""
            )

    critical_by_vessel: dict[str, int] = {
        str(row["uds_location_id"]): row["critical_count"]
        for row in critical_alert_rows
    }

    vessels = []
    for v in vessel_rows:
        vid = str(v["id"])
        imo = v["imo_nr"]
        vessel_alerts = alerts_by_vessel.get(vid, {})
        total_alerts = sum(vessel_alerts.values())
        affected_apps = len([k for k, cnt in vessel_alerts.items() if k != "_none" and cnt > 0])
        has_down = imo in down_apps_by_imo and len(down_apps_by_imo[imo]) > 0
        has_critical_alerts = critical_by_vessel.get(vid, 0) > 0

        # critical = app down OR critical-severity alert active
        # degraded = any non-critical alerts active
        # healthy = no active issues
        if has_down or has_critical_alerts:
            status = "critical"
        elif total_alerts > 0:
            status = "degraded"
        else:
            status = "healthy"

        vessels.append({
            "uds_location_id": vid,
            "external_id": v["external_id"],
            "name": v["name"],
            "imo_nr": imo,
            "app_count": app_counts.get(vid, 0),
            "active_alert_count": total_alerts,
            "affected_app_count": affected_apps,
            "latest_metric_at": _iso(latest_by_vessel.get(imo)),
            "status": status,
        })

    return {
        "vessel_count": len(vessels),
        "vessels": vessels,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _run_get_fleet_alerts(args: GetFleetAlertsArgs) -> dict[str, Any]:
    pool = get_pool()

    try:
        rows = await pool.fetch(
            """
            SELECT al.id,
                   u.name AS vessel_name,
                   u.imo_nr,
                   a.external_id AS app_external_id,
                   a.name AS app_name,
                   al.alert_name,
                   al.severity,
                   al.status,
                   al.alert_type,
                   al.starts_at,
                   al.ends_at,
                   al.received_at
            FROM alerts al
            JOIN udslocations u ON u.id = al.uds_location_id
            LEFT JOIN applications a ON a.id = al.application_id
            WHERE al.received_at >= NOW() - ($1 * INTERVAL '1 hour')
              AND (
                al.status IS NULL
                OR LOWER(al.status) NOT IN ('resolved', 'closed', 'completed', 'cleared')
              )
              AND (al.ends_at IS NULL OR al.ends_at > NOW())
              AND ($2::text IS NULL OR LOWER(al.severity) = LOWER($2))
            ORDER BY
                CASE LOWER(COALESCE(al.severity, 'info'))
                    WHEN 'critical' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'warning' THEN 2
                    WHEN 'info' THEN 3
                    ELSE 4
                END,
                al.starts_at DESC
            LIMIT 500;
            """,
            args.hours,
            args.severity,
        )
    except Exception as exc:
        _normalize_error(exc)

    alerts = [
        {
            "id": str(row["id"]),
            "vessel_name": row["vessel_name"],
            "imo_nr": row["imo_nr"],
            "app_external_id": row["app_external_id"],
            "app_name": row["app_name"],
            "alert_name": row["alert_name"],
            "severity": row["severity"],
            "status": row["status"],
            "alert_type": row["alert_type"],
            "starts_at": _iso(row["starts_at"]),
            "ends_at": _iso(row["ends_at"]),
            "received_at": _iso(row["received_at"]),
        }
        for row in rows
    ]

    return {
        "hours": args.hours,
        "severity_filter": args.severity,
        "count": len(alerts),
        "alerts": alerts,
    }


async def _run_get_cross_vessel_correlation(
    args: GetCrossVesselCorrelationArgs,
) -> dict[str, Any]:
    pool = get_pool()

    try:
        app_rows = await pool.fetch(
            """
            SELECT a.external_id AS app_id,
                   a.name AS app_name,
                   COUNT(DISTINCT u.imo_nr)::int AS affected_vessels,
                   STRING_AGG(
                       DISTINCT u.name || ' (' || u.imo_nr || ')',
                       ', ' ORDER BY u.name || ' (' || u.imo_nr || ')'
                   ) AS vessels,
                   STRING_AGG(
                       DISTINCT al.alert_name, ', ' ORDER BY al.alert_name
                   ) AS alert_names
            FROM alerts al
            JOIN udslocations u ON u.id = al.uds_location_id
            JOIN applications a ON a.id = al.application_id
            WHERE al.received_at >= NOW() - ($1 * INTERVAL '1 hour')
              AND (
                al.status IS NULL
                OR LOWER(al.status) NOT IN ('resolved', 'closed', 'completed', 'cleared')
              )
              AND (al.ends_at IS NULL OR al.ends_at > NOW())
            GROUP BY a.external_id, a.name
            HAVING COUNT(DISTINCT u.imo_nr) > 1
            ORDER BY affected_vessels DESC, a.name ASC;
            """,
            args.hours,
        )

        alert_type_rows = await pool.fetch(
            """
            SELECT al.alert_name,
                   al.alert_type,
                   COUNT(DISTINCT u.imo_nr)::int AS affected_vessels,
                   STRING_AGG(
                       DISTINCT u.name || ' (' || u.imo_nr || ')',
                       ', ' ORDER BY u.name || ' (' || u.imo_nr || ')'
                   ) AS vessels,
                   STRING_AGG(
                       DISTINCT a.name, ', ' ORDER BY a.name
                   ) AS affected_apps
            FROM alerts al
            JOIN udslocations u ON u.id = al.uds_location_id
            LEFT JOIN applications a ON a.id = al.application_id
            WHERE al.received_at >= NOW() - ($1 * INTERVAL '1 hour')
              AND (
                al.status IS NULL
                OR LOWER(al.status) NOT IN ('resolved', 'closed', 'completed', 'cleared')
              )
              AND (al.ends_at IS NULL OR al.ends_at > NOW())
            GROUP BY al.alert_name, al.alert_type
            HAVING COUNT(DISTINCT u.imo_nr) > 1
            ORDER BY affected_vessels DESC, al.alert_name ASC;
            """,
            args.hours,
        )
    except Exception as exc:
        _normalize_error(exc)

    correlated_apps = [
        {
            "app_id": row["app_id"],
            "app_name": row["app_name"],
            "affected_vessels": row["affected_vessels"],
            "vessels": row["vessels"],
            "alert_names": row["alert_names"],
        }
        for row in app_rows
    ]

    correlated_alert_types = [
        {
            "alert_name": row["alert_name"],
            "alert_type": row["alert_type"],
            "affected_vessels": row["affected_vessels"],
            "vessels": row["vessels"],
            "affected_apps": row["affected_apps"],
        }
        for row in alert_type_rows
    ]

    return {
        "hours": args.hours,
        "correlated_apps": correlated_apps,
        "correlated_alert_types": correlated_alert_types,
    }


async def _run_get_incident_timeline(
    args: GetIncidentTimelineArgs,
) -> dict[str, Any]:
    vessel = await _resolve_uds_vessel(args.vessel_id)
    pool = get_pool()

    # Resolve optional app filter to application_id for precise filtering
    app_filter_id: str | None = None
    app_filter_ext: str | None = None
    if args.app:
        app_meta = await _resolve_uds_application(vessel, args.app)
        app_filter_id = app_meta["application_id"]
        app_filter_ext = app_meta["external_id"]

    try:
        rows = await pool.fetch(
            """
            SELECT time, event_type, application, severity, message FROM (
                SELECT al.starts_at AS time,
                       'alert' AS event_type,
                       COALESCE(a.name, 'unknown') AS application,
                       al.severity,
                       al.alert_name AS message
                FROM alerts al
                LEFT JOIN applications a ON a.id = al.application_id
                WHERE al.uds_location_id = $1::uuid
                  AND al.starts_at >= NOW() - ($2 * INTERVAL '1 hour')
                  AND ($3::uuid IS NULL OR al.application_id = $3::uuid)
                UNION ALL
                SELECT l.logged_at AS time,
                       'log' AS event_type,
                       COALESCE(a.name, l.app_external_id, 'unknown') AS application,
                       l.level AS severity,
                       l.message
                FROM app_logs l
                LEFT JOIN applications a ON a.id = l.application_id
                WHERE l.uds_location_id = $1::uuid
                  AND l.logged_at >= NOW() - ($2 * INTERVAL '1 hour')
                  AND (
                    $3::uuid IS NULL
                    OR l.application_id = $3::uuid
                    OR LOWER(COALESCE(l.app_external_id, '')) = LOWER(COALESCE($4, ''))
                  )
            ) combined
            ORDER BY time DESC
            LIMIT 500;
            """,
            vessel["uds_location_id"],
            args.hours,
            app_filter_id,
            app_filter_ext,
        )
    except Exception as exc:
        _normalize_error(exc)

    timeline = [
        {
            "time": _iso(row["time"]),
            "event_type": row["event_type"],
            "application": row["application"],
            "severity": row["severity"],
            "message": row["message"],
        }
        for row in rows
    ]

    return {
        "vessel": vessel,
        "hours": args.hours,
        "app_filter": args.app,
        "count": len(timeline),
        "timeline": timeline,
    }


async def _run_get_operational_snapshot(
    args: GetOperationalSnapshotArgs,
) -> dict[str, Any]:
    vessel = await _resolve_uds_vessel(args.vessel_id)
    pool = get_pool()

    try:
        # App statuses (reuse same logic as get_vessel_app_status)
        app_rows = await pool.fetch(
            """
            SELECT a.id, a.external_id, a.name, a.app_type
            FROM uds_location_application_instances uai
            JOIN applications a ON a.id = uai.application_instance_id
            WHERE uai.uds_location_id = $1::uuid
            ORDER BY a.name ASC;
            """,
            vessel["uds_location_id"],
        )

        latest_metric_rows = await pool.fetch(
            """
            SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
                   ms.application_instance_id,
                   ms.app_id,
                   ms.metric_name,
                   ms.time,
                   ms.value
            FROM metric_samples ms
            WHERE ms.imo_nr = $1
            ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC;
            """,
            vessel["imo_nr"],
        )

        alert_count_rows = await pool.fetch(
            """
            SELECT application_id, COUNT(*)::int AS active_alert_count
            FROM alerts
            WHERE uds_location_id = $1::uuid
              AND (
                status IS NULL
                OR LOWER(status) NOT IN ('resolved', 'closed', 'completed', 'cleared')
              )
              AND (ends_at IS NULL OR ends_at > NOW())
            GROUP BY application_id;
            """,
            vessel["uds_location_id"],
        )

        active_alert_rows = await pool.fetch(
            """
            SELECT al.id,
                   a.name AS app_name,
                   a.external_id AS app_external_id,
                   al.alert_name,
                   al.severity,
                   al.status,
                   al.alert_type,
                   al.starts_at,
                   al.received_at
            FROM alerts al
            LEFT JOIN applications a ON a.id = al.application_id
            WHERE al.uds_location_id = $1::uuid
              AND (
                al.status IS NULL
                OR LOWER(al.status) NOT IN ('resolved', 'closed', 'completed', 'cleared')
              )
              AND (al.ends_at IS NULL OR al.ends_at > NOW())
            ORDER BY al.starts_at DESC
            LIMIT 50;
            """,
            vessel["uds_location_id"],
        )

        log_rows = await pool.fetch(
            """
            SELECT l.logged_at,
                   l.level,
                   l.source,
                   l.message,
                   COALESCE(a.name, l.app_external_id) AS app_name
            FROM app_logs l
            LEFT JOIN applications a ON a.id = l.application_id
            WHERE l.uds_location_id = $1::uuid
            ORDER BY l.logged_at DESC
            LIMIT 20;
            """,
            vessel["uds_location_id"],
        )

        connectivity_rows = await pool.fetch(
            """
            SELECT DISTINCT ON (ms.metric_name)
                   ms.metric_name,
                   ms.value,
                   ms.time
            FROM metric_samples ms
            WHERE ms.imo_nr = $1
              AND ms.metric_name IN ('last_sync_age_seconds', 'reporting_stale', 'sync_delayed')
            ORDER BY ms.metric_name, ms.time DESC;
            """,
            vessel["imo_nr"],
        )
    except Exception as exc:
        _normalize_error(exc)

    # Build per-app metrics lookup
    metrics_by_app: dict[str, list[dict]] = {}
    for row in latest_metric_rows:
        aid = str(row["application_instance_id"]) if row["application_instance_id"] else (row["app_id"] or "")
        metrics_by_app.setdefault(aid, []).append({
            "metric_name": row["metric_name"],
            "value": row["value"],
        })

    active_alerts_by_app = {
        str(row["application_id"]): row["active_alert_count"] for row in alert_count_rows
    }

    applications = []
    for app_row in app_rows:
        app_id = str(app_row["id"])
        app_key = (app_row["external_id"] or "").strip().lower()
        app_metrics = metrics_by_app.get(app_id) or metrics_by_app.get(app_key, [])
        alert_count = active_alerts_by_app.get(app_id, 0)

        applications.append({
            "application_id": app_id,
            "external_id": app_row["external_id"],
            "name": app_row["name"],
            "app_type": app_row["app_type"],
            "status": _derive_app_status(app_metrics, alert_count),
            "active_alert_count": alert_count,
        })

    active_alerts = [
        {
            "id": str(row["id"]),
            "app_name": row["app_name"],
            "app_external_id": row["app_external_id"],
            "alert_name": row["alert_name"],
            "severity": row["severity"],
            "status": row["status"],
            "alert_type": row["alert_type"],
            "starts_at": _iso(row["starts_at"]),
            "received_at": _iso(row["received_at"]),
        }
        for row in active_alert_rows
    ]

    recent_logs = [
        {
            "timestamp": _iso(row["logged_at"]),
            "level": row["level"],
            "source": row["source"],
            "message": row["message"],
            "app_name": row["app_name"],
        }
        for row in log_rows
    ]

    connectivity = {}
    for row in connectivity_rows:
        connectivity[row["metric_name"]] = {
            "value": row["value"],
            "time": _iso(row["time"]),
        }

    return {
        "vessel": vessel,
        "applications": applications,
        "active_alerts": active_alerts,
        "recent_logs": recent_logs,
        "connectivity": connectivity,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


TOOL_HANDLERS = {
    "get_telemetry": (GetTelemetryArgs, _run_get_telemetry),
    "get_events": (GetEventsArgs, _run_get_events),
    "get_analysis": (GetAnalysisArgs, _run_get_analysis),
    "get_vessel_app_status": (GetVesselAppStatusArgs, _run_get_vessel_app_status),
    "get_vessel_alerts": (GetVesselAlertsArgs, _run_get_vessel_alerts),
    "get_app_metric_history": (GetAppMetricHistoryArgs, _run_get_app_metric_history),
    "get_app_logs": (GetAppLogsArgs, _run_get_app_logs),
    "get_fleet_status": (GetFleetStatusArgs, _run_get_fleet_status),
    "get_fleet_alerts": (GetFleetAlertsArgs, _run_get_fleet_alerts),
    "get_cross_vessel_correlation": (GetCrossVesselCorrelationArgs, _run_get_cross_vessel_correlation),
    "get_incident_timeline": (GetIncidentTimelineArgs, _run_get_incident_timeline),
    "get_operational_snapshot": (GetOperationalSnapshotArgs, _run_get_operational_snapshot),
}


# -----------------------------------------------------------------------------
# HTTP endpoints
# -----------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "maritime-mcp", "version": "0.1.0"}


@app.get("/tools")
async def list_tools(_: None = Depends(_require_api_key)):
    return {"tools": TOOLS}


@app.post("/tools/call")
async def call_tool(req: ToolCallRequest, _: None = Depends(_require_api_key)):
    if req.name not in TOOL_HANDLERS:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {req.name}")

    model_cls, handler = TOOL_HANDLERS[req.name]
    try:
        args = model_cls(**req.arguments)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors())

    return await handler(args)


@app.post("/tools/get_telemetry")
async def get_telemetry(args: GetTelemetryArgs, _: None = Depends(_require_api_key)):
    return await _run_get_telemetry(args)


@app.post("/tools/get_events")
async def get_events(args: GetEventsArgs, _: None = Depends(_require_api_key)):
    return await _run_get_events(args)


@app.post("/tools/get_analysis")
async def get_analysis(args: GetAnalysisArgs, _: None = Depends(_require_api_key)):
    return await _run_get_analysis(args)


@app.post("/tools/get_vessel_app_status")
async def get_vessel_app_status(
    args: GetVesselAppStatusArgs,
    _: None = Depends(_require_api_key),
):
    return await _run_get_vessel_app_status(args)


@app.post("/tools/get_vessel_alerts")
async def get_vessel_alerts(
    args: GetVesselAlertsArgs,
    _: None = Depends(_require_api_key),
):
    return await _run_get_vessel_alerts(args)


@app.post("/tools/get_app_metric_history")
async def get_app_metric_history(
    args: GetAppMetricHistoryArgs,
    _: None = Depends(_require_api_key),
):
    return await _run_get_app_metric_history(args)


@app.post("/tools/get_app_logs")
async def get_app_logs(
    args: GetAppLogsArgs,
    _: None = Depends(_require_api_key),
):
    return await _run_get_app_logs(args)


@app.post("/tools/get_fleet_status")
async def get_fleet_status(
    args: GetFleetStatusArgs,
    _: None = Depends(_require_api_key),
):
    return await _run_get_fleet_status(args)


@app.post("/tools/get_fleet_alerts")
async def get_fleet_alerts(
    args: GetFleetAlertsArgs,
    _: None = Depends(_require_api_key),
):
    return await _run_get_fleet_alerts(args)


@app.post("/tools/get_cross_vessel_correlation")
async def get_cross_vessel_correlation(
    args: GetCrossVesselCorrelationArgs,
    _: None = Depends(_require_api_key),
):
    return await _run_get_cross_vessel_correlation(args)


@app.post("/tools/get_incident_timeline")
async def get_incident_timeline(
    args: GetIncidentTimelineArgs,
    _: None = Depends(_require_api_key),
):
    return await _run_get_incident_timeline(args)


@app.post("/tools/get_operational_snapshot")
async def get_operational_snapshot(
    args: GetOperationalSnapshotArgs,
    _: None = Depends(_require_api_key),
):
    return await _run_get_operational_snapshot(args)

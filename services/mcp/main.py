"""
Maritime MCP Server
===================
FastAPI entry point for MCP-style tools exposed over HTTP.

This is a REST adapter that exposes DB query tools using MCP-style
tool definitions (name + inputSchema).  The agent calls these via HTTP.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
import secrets
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

from db import init_pool, close_pool, get_pool

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
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
    allow_origins=["*"],
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


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# DB helpers
# -----------------------------------------------------------------------------
def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


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
        SELECT id, event_id, timestamp, analysis_text, suggested_actions,
               confidence, model_used, status
        FROM ai_analyses
        WHERE event_id = $1
        ORDER BY timestamp DESC
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


TOOL_HANDLERS = {
    "get_telemetry": (GetTelemetryArgs, _run_get_telemetry),
    "get_events": (GetEventsArgs, _run_get_events),
    "get_analysis": (GetAnalysisArgs, _run_get_analysis),
}


# -----------------------------------------------------------------------------
# HTTP endpoints
# -----------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "maritime-mcp", "version": "0.1.0"}


@app.get("/tools")
async def list_tools():
    return {"tools": TOOLS}


@app.post("/tools/call")
async def call_tool(req: ToolCallRequest):
    if req.name not in TOOL_HANDLERS:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {req.name}")

    model_cls, handler = TOOL_HANDLERS[req.name]
    try:
        args = model_cls(**req.arguments)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors())

    return await handler(args)


@app.post("/tools/get_telemetry")
async def get_telemetry(args: GetTelemetryArgs):
    return await _run_get_telemetry(args)


@app.post("/tools/get_events")
async def get_events(args: GetEventsArgs):
    return await _run_get_events(args)


@app.post("/tools/get_analysis")
async def get_analysis(args: GetAnalysisArgs):
    return await _run_get_analysis(args)

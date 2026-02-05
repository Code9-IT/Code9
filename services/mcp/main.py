"""
Maritime MCP Server
===================
FastAPI entry point for MCP-style tools exposed over HTTP.
"""

from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

from db import init_pool, close_pool, get_pool

load_dotenv()

app = FastAPI(
    title="Maritime MCP Server",
    description="HTTP wrapper exposing MCP tool definitions for maritime data.",
    version="0.1.0",
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


TOOL_HANDLERS = {
    "get_telemetry": (GetTelemetryArgs, _run_get_telemetry),
    "get_events": (GetEventsArgs, _run_get_events),
    "get_analysis": (GetAnalysisArgs, _run_get_analysis),
}


# -----------------------------------------------------------------------------
# Lifecycle
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    await init_pool()


@app.on_event("shutdown")
async def shutdown():
    await close_pool()


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

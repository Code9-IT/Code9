"""
GET  /api/v1/events                          - list recent events
POST /api/v1/events/{id}/acknowledge         - human-in-the-loop: operator ack
GET  /api/v1/events/{id}/acknowledge/confirm - HTML confirmation page
=====================================================================
"""

import html

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing  import Optional

from db import get_pool

router = APIRouter(tags=["events"])


# --- GET /events ------------------------------------------------------------
@router.get("/events")
async def get_recent_events(
    limit:        int            = Query(default=20, le=100),
    acknowledged: Optional[bool] = Query(default=None),
):
    """
    Return recent events.
    Pass ?acknowledged=false to see only unacknowledged ones.
    """
    pool = get_pool()

    if acknowledged is not None:
        rows = await _fetch(pool,
            "SELECT * FROM events WHERE acknowledged = $2 ORDER BY timestamp DESC LIMIT $1",
            limit, acknowledged,
        )
    else:
        rows = await _fetch(pool,
            "SELECT * FROM events ORDER BY timestamp DESC LIMIT $1",
            limit,
        )

    return [dict(r) for r in rows]


# --- POST /events/{event_id}/acknowledge ------------------------------------
@router.post("/events/{event_id}/acknowledge")
async def acknowledge_event(
    event_id: int,
    operator: str = Query(default="unknown"),
):
    """
    Mark an event as acknowledged by an operator.
    This is the human-in-the-loop action.

    TODO: replace 'operator' query param with proper auth / JWT claim.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        status = await conn.execute(
            """
            UPDATE events
            SET    acknowledged    = TRUE,
                   acknowledged_by = $2,
                   acknowledged_at = NOW()
            WHERE  id              = $1
              AND  acknowledged    = FALSE
            """,
            event_id, operator,
        )

    # status looks like "UPDATE 1" or "UPDATE 0"
    updated = int(status.split()[-1])
    if updated == 0:
        return {"message": "Event not found or already acknowledged", "event_id": event_id}

    return {"message": "Event acknowledged", "event_id": event_id, "operator": operator}


# --- GET /events/{event_id}/acknowledge -------------------------------
@router.get("/events/{event_id}/acknowledge")
async def acknowledge_event_get(
    event_id: int,
    operator: str = Query(default="unknown"),
):
    """
    GET is not allowed for state-changing operations.
    Use POST /events/{event_id}/acknowledge or open the
    /events/{event_id}/acknowledge/confirm page instead.
    """
    raise HTTPException(
        status_code=405,
        detail={
            "error": "Method Not Allowed: use POST to acknowledge events",
            "hint": f"POST /api/v1/events/{event_id}/acknowledge?operator={operator}",
            "confirm_page": f"/api/v1/events/{event_id}/acknowledge/confirm?operator={operator}",
        },
        headers={"Allow": "POST"},
    )


# --- GET /events/{event_id}/acknowledge/confirm -----------------------
@router.get("/events/{event_id}/acknowledge/confirm", response_class=HTMLResponse)
async def acknowledge_event_confirm(
    event_id: int,
    operator: str = Query(default="unknown"),
):
    """
    Browser-friendly confirmation page used by Grafana data links.
    Renders a small page with a POST form so the human-in-the-loop
    acknowledge action stays explicit and is never triggered by a
    plain link click.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, vessel_id, sensor_name, event_type, severity,
                   acknowledged, acknowledged_by, acknowledged_at, timestamp
            FROM events WHERE id = $1
            """,
            event_id,
        )

    if row is None:
        return HTMLResponse(
            f"<html><body><h1>Event {event_id} not found</h1></body></html>",
            status_code=404,
        )

    safe_event_id = html.escape(str(event_id))
    safe_operator = html.escape(operator)
    safe_vessel = html.escape(str(row["vessel_id"] or "-"))
    safe_sensor = html.escape(str(row["sensor_name"] or "-"))
    safe_type = html.escape(str(row["event_type"] or "-"))
    safe_severity = html.escape(str(row["severity"] or "-"))
    safe_timestamp = html.escape(str(row["timestamp"] or "-"))

    if row["acknowledged"]:
        ack_by = html.escape(str(row["acknowledged_by"] or "unknown"))
        ack_at = html.escape(str(row["acknowledged_at"] or "-"))
        body = (
            f"<div class='card ok'><strong>Already acknowledged</strong>"
            f" by {ack_by} at {ack_at}.</div>"
        )
    else:
        body = (
            "<form method='POST' "
            f"action='/api/v1/events/{safe_event_id}/acknowledge?operator={safe_operator}'>"
            "<button type='submit' class='ack-btn'>Acknowledge event</button>"
            "</form>"
            "<p class='hint'>Clicking this button issues an explicit POST "
            "to the acknowledge endpoint.</p>"
        )

    page = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Acknowledge event {safe_event_id}</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 2rem; max-width: 720px; }}
.card {{ padding: 1rem; border-radius: 6px; margin-bottom: 1rem; background: #f6f6f6; }}
.card.ok {{ background: #e6f4ea; }}
.field {{ margin: 0.25rem 0; }}
.label {{ color: #555; font-size: 0.85rem; }}
.value {{ font-weight: 600; }}
.ack-btn {{ padding: 0.6rem 1.2rem; font-size: 1rem; cursor: pointer;
            background: #1a73e8; color: white; border: 0; border-radius: 4px; }}
.hint {{ color: #666; font-size: 0.85rem; }}
</style></head>
<body>
<h1>Acknowledge event #{safe_event_id}</h1>
<div class='card'>
  <div class='field'><span class='label'>Vessel:</span> <span class='value'>{safe_vessel}</span></div>
  <div class='field'><span class='label'>Sensor:</span> <span class='value'>{safe_sensor}</span></div>
  <div class='field'><span class='label'>Event type:</span> <span class='value'>{safe_type}</span></div>
  <div class='field'><span class='label'>Severity:</span> <span class='value'>{safe_severity}</span></div>
  <div class='field'><span class='label'>Timestamp:</span> <span class='value'>{safe_timestamp}</span></div>
  <div class='field'><span class='label'>Operator:</span> <span class='value'>{safe_operator}</span></div>
</div>
{body}
</body></html>"""
    return HTMLResponse(page)


# --- private helpers ----------------------------------------------------
async def _fetch(pool, query: str, *args):
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

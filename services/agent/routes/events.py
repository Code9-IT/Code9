"""
GET  /api/v1/events              – list recent events
POST /api/v1/events/{id}/acknowledge – human-in-the-loop: operator ack
=====================================================================
"""

from fastapi import APIRouter, Query
from typing  import Optional

from db import get_pool

router = APIRouter(tags=["events"])


# ─── GET /events ──────────────────────────────────────────
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


# ─── POST /events/{event_id}/acknowledge ──────────────────
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
    GET alias for Grafana data links.
    Reuses the same acknowledge logic as POST /events/{event_id}/acknowledge.
    """
    return await acknowledge_event(event_id=event_id, operator=operator)


# --- private helpers ----------------------------------------------------
async def _fetch(pool, query: str, *args):
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

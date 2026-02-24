"""
Pydantic models – request / response schemas for the Agent API.
"""

from datetime import datetime
from typing  import List, Optional
from pydantic import BaseModel


# ─── Analyse endpoint ─────────────────────────────────────
class AnalyzeRequest(BaseModel):
    """POST /api/v1/analyze"""
    event_id: int
    force: bool = False


class AnalyzeResponse(BaseModel):
    """Response returned after a successful analysis."""
    id:                int
    event_id:          int
    analysis_text:     str
    suggested_actions: List[str]
    confidence:        float          # 0.0 – 1.0
    model_used:        str            # e.g. 'stub', 'ollama/llama3'
    status:            str            # 'completed' | 'failed'


# ─── Event schema ─────────────────────────────────────────
class EventSchema(BaseModel):
    """Used when returning event data from the API."""
    id:               int
    timestamp:        datetime
    vessel_id:        str
    sensor_name:      str
    event_type:       str
    severity:         str
    details:          Optional[str] = None
    acknowledged:     bool
    acknowledged_by:  Optional[str] = None

"""
Pydantic models for the Agent API.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request used by quick and full analysis routes."""

    event_id: int
    force: bool = False
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    min_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AnalyzeResponse(BaseModel):
    """Analysis row or job status returned by the API."""

    id: int
    event_id: int
    analysis_mode: str
    analysis_text: str
    suggested_actions: List[str]
    confidence: float
    model_used: str
    status: str


class RetrievedDocument(BaseModel):
    """Serializable RAG retrieval result."""

    title: str
    source: str
    similarity: float
    content_preview: str


class RetrievalValidationCase(BaseModel):
    """One representative retrieval check."""

    name: str
    event_type: str
    sensor_name: str
    vessel_id: str = "vessel_001"
    expected_sources: List[str] = Field(default_factory=list)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    min_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class RetrievalValidationRequest(BaseModel):
    """Batch retrieval validation request."""

    cases: List[RetrievalValidationCase] = Field(default_factory=list)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    min_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class RetrievalValidationCaseResult(BaseModel):
    """Result for one retrieval validation case."""

    name: str
    query: str
    expected_sources: List[str]
    matched_expected_source: bool
    retrieved_documents: List[RetrievedDocument]


class RetrievalValidationResponse(BaseModel):
    """Aggregated retrieval validation summary."""

    total_cases: int
    matched_cases: int
    requested_top_k: Optional[int] = None
    requested_min_similarity: Optional[float] = None
    results: List[RetrievalValidationCaseResult]


class AnalysisValidationRequest(BaseModel):
    """Run one event through the validation analysis pipeline."""

    event_id: int
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    min_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ToolCallTrace(BaseModel):
    """One live MCP tool call executed by the analysis pipeline."""

    name: str
    arguments: dict[str, Any]
    succeeded: bool
    response_size_chars: int
    response_preview: str


class AnalysisQualityFactors(BaseModel):
    """Inputs that materially affect analysis quality."""

    rag_top_k: int
    rag_min_similarity: float
    retrieved_documents_count: int
    retrieved_sources: List[str]
    tool_calls_count: int
    used_live_tools: bool
    model_used: str
    status: str


class AnalysisValidationResponse(BaseModel):
    """Diagnostic view of one pipeline run."""

    event: "EventSchema"
    analysis_text: str
    suggested_actions: List[str]
    confidence: float
    retrieved_documents: List[RetrievedDocument]
    tool_calls: List[ToolCallTrace]
    quality_factors: AnalysisQualityFactors


class EventSchema(BaseModel):
    """Used when returning event data from the API."""

    id: int
    timestamp: datetime
    vessel_id: str
    sensor_name: str
    event_type: str
    severity: str
    details: Optional[str] = None
    acknowledged: bool
    acknowledged_by: Optional[str] = None


AnalysisValidationResponse.model_rebuild()

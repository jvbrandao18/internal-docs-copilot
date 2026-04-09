from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class QuerySessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question: str
    answer: str
    confidence: float
    latency_ms: int
    created_at: datetime


class QueryListResponse(BaseModel):
    items: list[QuerySessionResponse]


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    document_id: str | None = None
    query_session_id: str | None = None
    payload_json: dict[str, Any]
    created_at: datetime


class QueryAuditTrailResponse(BaseModel):
    query: QuerySessionResponse
    audit_events: list[AuditEventResponse]

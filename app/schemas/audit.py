from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    status: str
    actor: str
    document_id: str | None = None
    query_id: str | None = None
    payload: dict[str, Any]
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditEventResponse]

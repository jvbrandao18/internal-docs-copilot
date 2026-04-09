from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    filename: str
    content_type: str
    file_extension: str
    status: str
    chunk_count: int
    metadata: dict[str, Any] = Field(alias="document_metadata")
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    audit_event_id: str


class DocumentDeleteResponse(BaseModel):
    document_id: str
    status: str
    audit_event_id: str


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    status: str
    uploaded_at: datetime
    processed_at: datetime | None = None
    page_count: int | None = None
    sheet_count: int | None = None
    error_message: str | None = None


class DocumentListResponse(BaseModel):
    items: list[DocumentListItem]


class DocumentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    status: str
    path: str
    sha256_hash: str
    uploaded_at: datetime
    processed_at: datetime | None = None
    page_count: int | None = None
    sheet_count: int | None = None
    error_message: str | None = None


class DocumentDeleteResponse(BaseModel):
    document_id: str
    status: str

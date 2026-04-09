from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies import get_document_service
from app.domain.services.document_service import DocumentService
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    document, audit_event = service.ingest_upload(file)
    return DocumentUploadResponse(document=document, audit_event_id=audit_event.id)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    include_deleted: bool = False,
    service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    return DocumentListResponse(items=list(service.list_documents(include_deleted=include_deleted)))


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentDeleteResponse:
    deleted_document, audit_event = service.delete_document(document_id)
    return DocumentDeleteResponse(
        document_id=deleted_document.id,
        status=deleted_document.status,
        audit_event_id=audit_event.id,
    )

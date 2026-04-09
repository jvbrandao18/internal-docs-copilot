from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies import get_document_service
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.services.document_ingestion_service import DocumentIngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    service: DocumentIngestionService = Depends(get_document_service),
) -> DocumentUploadResponse:
    document = service.ingest(file)
    return DocumentUploadResponse(document_id=document.id, status=document.status)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    service: DocumentIngestionService = Depends(get_document_service),
) -> DocumentListResponse:
    return DocumentListResponse(items=list(service.list_documents()))


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: str,
    service: DocumentIngestionService = Depends(get_document_service),
) -> DocumentDetailResponse:
    return DocumentDetailResponse.model_validate(service.get_document(document_id))


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: str,
    service: DocumentIngestionService = Depends(get_document_service),
) -> DocumentDeleteResponse:
    service.delete_document(document_id)
    return DocumentDeleteResponse(document_id=document_id, status="deleted")

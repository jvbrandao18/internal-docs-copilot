from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_audit_service
from app.domain.services.audit_service import AuditService
from app.schemas.audit import AuditListResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=AuditListResponse)
def list_audit_events(
    limit: int = Query(default=100, ge=1, le=500),
    event_type: str | None = None,
    document_id: str | None = None,
    service: AuditService = Depends(get_audit_service),
) -> AuditListResponse:
    return AuditListResponse(
        items=list(service.list_events(limit=limit, event_type=event_type, document_id=document_id))
    )

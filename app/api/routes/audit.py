from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_audit_service
from app.schemas.audit import QueryAuditTrailResponse, QueryListResponse, QuerySessionResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/queries", response_model=QueryListResponse)
def list_queries(
    limit: int = Query(default=100, ge=1, le=500),
    service: AuditService = Depends(get_audit_service),
) -> QueryListResponse:
    return QueryListResponse(items=list(service.list_queries(limit=limit)))


@router.get("/queries/{query_id}", response_model=QueryAuditTrailResponse)
def get_query_audit_trail(
    query_id: str,
    service: AuditService = Depends(get_audit_service),
) -> QueryAuditTrailResponse:
    query_session, audit_events = service.get_query_trail(query_id)
    return QueryAuditTrailResponse(
        query=QuerySessionResponse.model_validate(query_session),
        audit_events=list(audit_events),
    )

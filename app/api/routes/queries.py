from fastapi import APIRouter, Depends

from app.api.dependencies import get_query_service
from app.domain.services.query_service import QueryService
from app.schemas.query import AskRequest, AskResponse

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    service: QueryService = Depends(get_query_service),
) -> AskResponse:
    return service.ask(
        question=payload.question,
        top_k=payload.top_k,
        document_ids=payload.document_ids,
    )

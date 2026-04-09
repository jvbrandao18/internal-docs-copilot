from fastapi import APIRouter, Depends

from app.api.dependencies import get_query_service
from app.schemas.query import AskRequest, AskResponse, QuerySourceResponse
from app.services.query_service import QueryService

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    service: QueryService = Depends(get_query_service),
) -> AskResponse:
    result = service.ask(
        question=payload.question,
        document_ids=payload.document_ids or None,
        top_k=payload.top_k,
    )
    return AskResponse(
        answer=result.answer,
        confidence=result.confidence,
        sources=[
            QuerySourceResponse(
                document_name=source.document_name,
                page_number=source.page_number,
                sheet_name=source.sheet_name,
                excerpt=source.excerpt,
            )
            for source in result.sources
        ],
        retrieved_chunks=result.retrieved_chunks,
        latency_ms=result.latency_ms,
    )

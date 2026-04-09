from dataclasses import asdict, dataclass
from time import perf_counter

from sqlalchemy.orm import Session

from app.core.logging import get_logger, log_event
from app.infra.vectorstore.chroma_store import RetrievedChunk
from app.services.answer_service import AnswerService
from app.services.audit_service import AuditService
from app.services.retrieval_service import RetrievalService


@dataclass(slots=True)
class QuerySource:
    document_name: str
    page_number: int | None
    sheet_name: str | None
    excerpt: str


@dataclass(slots=True)
class QueryResult:
    query_id: str
    answer: str
    confidence: float
    sources: list[QuerySource]
    retrieved_chunks: int
    latency_ms: int


class QueryService:
    def __init__(
        self,
        *,
        session: Session,
        retrieval_service: RetrievalService,
        answer_service: AnswerService,
        audit_service: AuditService,
    ) -> None:
        self.session = session
        self.retrieval_service = retrieval_service
        self.answer_service = answer_service
        self.audit_service = audit_service
        self.logger = get_logger(__name__)

    def ask(
        self,
        *,
        question: str,
        document_ids: list[str] | None,
        top_k: int | None,
    ) -> QueryResult:
        started_at = perf_counter()
        try:
            retrieved_chunks = list(
                self.retrieval_service.retrieve(
                    question=question,
                    document_ids=document_ids,
                    top_k=top_k,
                )
            )
            answer_result = self.answer_service.answer(
                question=question,
                retrieved_chunks=retrieved_chunks,
            )
            latency_ms = int((perf_counter() - started_at) * 1000)
            sources = self._build_sources(retrieved_chunks)
            query_session = self.audit_service.store_query_result(
                question=question,
                answer=answer_result.answer,
                confidence=answer_result.confidence,
                latency_ms=latency_ms,
                payload_json={
                    "question": question,
                    "document_ids": document_ids or [],
                    "refused": answer_result.refused,
                    "refusal_reason": answer_result.refusal_reason,
                    "retrieved_chunks": len(retrieved_chunks),
                    "sources": [asdict(source) for source in sources],
                },
            )
            log_event(
                self.logger,
                "query_completed",
                query_id=query_session.id,
                status="success",
                latency_ms=latency_ms,
                details={
                    "retrieved_chunks": len(retrieved_chunks),
                    "confidence": answer_result.confidence,
                    "refused": answer_result.refused,
                },
            )
            return QueryResult(
                query_id=query_session.id,
                answer=answer_result.answer,
                confidence=answer_result.confidence,
                sources=sources,
                retrieved_chunks=len(retrieved_chunks),
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = int((perf_counter() - started_at) * 1000)
            self.session.rollback()
            self.audit_service.store_query_failure(
                question=question,
                payload_json={
                    "document_ids": document_ids or [],
                    "top_k": top_k,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "latency_ms": latency_ms,
                },
            )
            log_event(
                self.logger,
                "query_failed",
                status="failed",
                latency_ms=latency_ms,
                error_type=type(exc).__name__,
                details=str(exc),
            )
            raise

    def _build_sources(self, retrieved_chunks: list[RetrievedChunk]) -> list[QuerySource]:
        sources: list[QuerySource] = []
        for chunk in retrieved_chunks:
            sources.append(
                QuerySource(
                    document_name=str(chunk.metadata.get("document_name", "unknown")),
                    page_number=chunk.metadata.get("page_number"),
                    sheet_name=chunk.metadata.get("sheet_name"),
                    excerpt=" ".join(chunk.content.split())[:280],
                )
            )
        return sources

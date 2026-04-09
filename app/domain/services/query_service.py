from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppError, NotFoundError
from app.core.logging import get_logger
from app.db.models import AuditEvent
from app.db.repositories.documents import AuditRepository, DocumentRepository
from app.infra.openai.client import OpenAIClient
from app.infra.vector.chroma_store import ChromaVectorStore, RetrievedChunk
from app.schemas.query import AskResponse, Citation


class QueryService:
    def __init__(
        self,
        *,
        session: Session,
        settings: Settings,
        vector_store: ChromaVectorStore,
        openai_client: OpenAIClient,
    ) -> None:
        self.session = session
        self.settings = settings
        self.vector_store = vector_store
        self.openai_client = openai_client
        self.document_repository = DocumentRepository(session)
        self.audit_repository = AuditRepository(session)
        self.logger = get_logger(__name__)

    def ask(
        self,
        *,
        question: str,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
    ) -> AskResponse:
        query_id = str(uuid4())
        top_k = top_k or self.settings.top_k_results
        normalized_document_ids = sorted(set(document_ids or [])) or None

        try:
            if normalized_document_ids:
                self._ensure_documents_are_available(normalized_document_ids)

            question_embedding = self.openai_client.embed_texts([question])[0]
            retrieved_chunks = self.vector_store.query(
                question_embedding,
                top_k=top_k,
                document_ids=normalized_document_ids,
            )
            evidence_score = self._calculate_evidence_score(retrieved_chunks)
            citations = self._build_citations(retrieved_chunks)

            if not retrieved_chunks or evidence_score < self.settings.min_evidence_score:
                response = AskResponse(
                    query_id=query_id,
                    answer="I cannot answer safely because the indexed evidence is insufficient.",
                    confidence=round(evidence_score, 2),
                    refused=True,
                    refusal_reason=(
                        "Insufficient supporting evidence was retrieved " "from indexed documents."
                    ),
                    citations=citations,
                )
                self._store_audit_event(
                    query_id=query_id,
                    status="success",
                    payload=self._build_query_payload(
                        question=question,
                        response=response,
                        document_ids=normalized_document_ids,
                    ),
                )
                return response

            answer_payload = self.openai_client.answer_question(
                question=question,
                evidence=retrieved_chunks,
            )
            model_confidence = self._clamp_confidence(answer_payload.get("confidence"))
            refused = bool(answer_payload.get("refused"))
            refusal_reason = answer_payload.get("refusal_reason")
            answer = str(answer_payload.get("answer", "")).strip()

            if refused:
                answer = (
                    answer
                    or "I cannot answer safely because the retrieved evidence is not strong enough."
                )
                refusal_reason = (
                    refusal_reason or "The retrieved evidence did not support a safe answer."
                )
            elif not answer:
                answer = "No grounded answer was generated."

            final_confidence = (
                evidence_score if model_confidence == 0 else min(evidence_score, model_confidence)
            )

            response = AskResponse(
                query_id=query_id,
                answer=answer,
                confidence=round(final_confidence, 2),
                refused=refused,
                refusal_reason=refusal_reason,
                citations=citations,
            )
            self._store_audit_event(
                query_id=query_id,
                status="success",
                payload=self._build_query_payload(
                    question=question,
                    response=response,
                    document_ids=normalized_document_ids,
                ),
            )

            self.logger.info(
                "query_answered",
                extra={
                    "query_id": query_id,
                    "refused": refused,
                    "confidence": response.confidence,
                    "citations": len(citations),
                },
            )
            return response

        except Exception as exc:
            self.session.rollback()
            self._store_audit_event(
                query_id=query_id,
                status="failed",
                payload={
                    "question": question,
                    "document_ids": normalized_document_ids or [],
                    "error": str(exc),
                },
            )
            if isinstance(exc, AppError):
                raise
            raise AppError(
                "Query execution failed.",
                status_code=500,
                code="query_execution_failed",
            ) from exc

    def _ensure_documents_are_available(self, document_ids: list[str]) -> None:
        for document_id in document_ids:
            document = self.document_repository.get(document_id)
            if document is None or document.deleted_at is not None:
                raise NotFoundError(f"Document '{document_id}' was not found.")

    def _build_citations(self, retrieved_chunks: list[RetrievedChunk]) -> list[Citation]:
        citations: list[Citation] = []
        for chunk in retrieved_chunks:
            normalized_excerpt = " ".join(chunk.text.split())[
                : self.settings.max_citation_excerpt_chars
            ]
            citations.append(
                Citation(
                    document_id=str(chunk.metadata.get("document_id", "")),
                    filename=str(chunk.metadata.get("filename", "unknown")),
                    chunk_id=chunk.chunk_id,
                    source_label=str(chunk.metadata.get("source_label", "unknown source")),
                    excerpt=normalized_excerpt,
                    score=round(chunk.score, 4),
                )
            )
        return citations

    def _calculate_evidence_score(self, retrieved_chunks: list[RetrievedChunk]) -> float:
        if not retrieved_chunks:
            return 0.0
        return round(sum(chunk.score for chunk in retrieved_chunks) / len(retrieved_chunks), 4)

    def _store_audit_event(self, *, query_id: str, status: str, payload: dict[str, object]) -> None:
        audit_event = AuditEvent(
            id=str(uuid4()),
            event_type="query_executed",
            status=status,
            actor="system",
            query_id=query_id,
            payload=payload,
        )
        self.audit_repository.add(audit_event)
        self.session.commit()

    def _build_query_payload(
        self,
        *,
        question: str,
        response: AskResponse,
        document_ids: list[str] | None,
    ) -> dict[str, object]:
        return {
            "question": question,
            "document_ids": document_ids or [],
            "answer": response.answer,
            "refused": response.refused,
            "refusal_reason": response.refusal_reason,
            "confidence": response.confidence,
            "citations": [citation.model_dump() for citation in response.citations],
        }

    @staticmethod
    def _clamp_confidence(value: object) -> float:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, numeric_value))

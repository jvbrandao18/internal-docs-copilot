from collections.abc import Sequence
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models import AuditEvent, QuerySession
from app.repositories.audit_repository import AuditRepository
from app.repositories.query_repository import QueryRepository


class AuditService:
    def __init__(
        self,
        *,
        session: Session,
        audit_repository: AuditRepository,
        query_repository: QueryRepository,
    ) -> None:
        self.session = session
        self.audit_repository = audit_repository
        self.query_repository = query_repository

    def record_event(
        self,
        *,
        event_type: str,
        document_id: str | None = None,
        query_session_id: str | None = None,
        payload_json: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=str(uuid4()),
            event_type=event_type,
            document_id=document_id,
            query_session_id=query_session_id,
            payload_json=payload_json or {},
        )
        self.audit_repository.add(event)
        return event

    def store_query_result(
        self,
        *,
        question: str,
        answer: str,
        confidence: float,
        latency_ms: int,
        payload_json: dict[str, object],
    ) -> QuerySession:
        query_session = QuerySession(
            id=str(uuid4()),
            question=question,
            answer=answer,
            confidence=confidence,
            latency_ms=latency_ms,
        )
        self.query_repository.add(query_session)
        self.record_event(
            event_type="query_completed",
            query_session_id=query_session.id,
            payload_json=payload_json,
        )
        self.session.commit()
        return query_session

    def store_query_failure(
        self,
        *,
        question: str,
        payload_json: dict[str, object],
    ) -> None:
        self.record_event(
            event_type="query_failed",
            payload_json={"question": question, **payload_json},
        )
        self.session.commit()

    def list_queries(self, *, limit: int = 100) -> Sequence[QuerySession]:
        return self.query_repository.list(limit=limit)

    def get_query_trail(self, query_id: str) -> tuple[QuerySession, Sequence[AuditEvent]]:
        query_session = self.query_repository.get(query_id)
        if query_session is None:
            raise NotFoundError(f"Query '{query_id}' was not found.")
        return query_session, self.audit_repository.list_by_query(query_id)

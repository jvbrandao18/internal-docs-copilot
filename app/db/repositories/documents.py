from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent, Document


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, document: Document) -> None:
        self.session.add(document)

    def get(self, document_id: str) -> Document | None:
        return self.session.get(Document, document_id)

    def list(self, *, include_deleted: bool = False) -> Sequence[Document]:
        statement = select(Document).order_by(Document.created_at.desc())
        if not include_deleted:
            statement = statement.where(Document.deleted_at.is_(None))
        return list(self.session.scalars(statement))


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, audit_event: AuditEvent) -> None:
        self.session.add(audit_event)

    def list(
        self,
        *,
        limit: int = 100,
        event_type: str | None = None,
        document_id: str | None = None,
    ) -> Sequence[AuditEvent]:
        statement = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
        if event_type:
            statement = statement.where(AuditEvent.event_type == event_type)
        if document_id:
            statement = statement.where(AuditEvent.document_id == document_id)
        return list(self.session.scalars(statement))

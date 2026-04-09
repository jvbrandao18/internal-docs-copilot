from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AuditEvent


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, audit_event: AuditEvent) -> None:
        self.session.add(audit_event)

    def list_by_query(self, query_session_id: str) -> Sequence[AuditEvent]:
        statement = (
            select(AuditEvent)
            .where(AuditEvent.query_session_id == query_session_id)
            .order_by(AuditEvent.created_at.asc())
        )
        return list(self.session.scalars(statement))

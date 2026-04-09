from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.db.models import AuditEvent
from app.db.repositories.documents import AuditRepository


class AuditService:
    def __init__(self, *, session: Session) -> None:
        self.audit_repository = AuditRepository(session)

    def list_events(
        self,
        *,
        limit: int = 100,
        event_type: str | None = None,
        document_id: str | None = None,
    ) -> Sequence[AuditEvent]:
        return self.audit_repository.list(
            limit=limit,
            event_type=event_type,
            document_id=document_id,
        )

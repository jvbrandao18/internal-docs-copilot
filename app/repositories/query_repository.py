from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import QuerySession


class QueryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, query_session: QuerySession) -> None:
        self.session.add(query_session)

    def get(self, query_session_id: str) -> QuerySession | None:
        return self.session.get(QuerySession, query_session_id)

    def list(self, *, limit: int = 100) -> Sequence[QuerySession]:
        statement = select(QuerySession).order_by(QuerySession.created_at.desc()).limit(limit)
        return list(self.session.scalars(statement))

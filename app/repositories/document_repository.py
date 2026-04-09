from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Document


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, document: Document) -> None:
        self.session.add(document)

    def get(self, document_id: str) -> Document | None:
        return self.session.get(Document, document_id)

    def list(self) -> Sequence[Document]:
        statement = select(Document).order_by(Document.uploaded_at.desc())
        return list(self.session.scalars(statement))

    def delete(self, document: Document) -> None:
        self.session.delete(document)

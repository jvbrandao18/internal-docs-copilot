from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Chunk


class ChunkRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_many(self, chunks: list[Chunk]) -> None:
        self.session.add_all(chunks)

    def list_by_document(self, document_id: str) -> Sequence[Chunk]:
        statement = (
            select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index.asc())
        )
        return list(self.session.scalars(statement))

    def count_by_document(self, document_id: str) -> int:
        statement = select(func.count(Chunk.id)).where(Chunk.document_id == document_id)
        return int(self.session.scalar(statement) or 0)

    def delete_by_document(self, document_id: str) -> int:
        chunks = list(self.list_by_document(document_id))
        for chunk in chunks:
            self.session.delete(chunk)
        return len(chunks)

from collections.abc import Sequence

from app.core.exceptions import NotFoundError
from app.infra.vectorstore.chroma_store import ChromaStore, RetrievedChunk
from app.repositories.document_repository import DocumentRepository
from app.services.embedding_service import EmbeddingService


class RetrievalService:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
        embedding_service: EmbeddingService,
        chroma_store: ChromaStore,
        default_top_k: int,
    ) -> None:
        self.document_repository = document_repository
        self.embedding_service = embedding_service
        self.chroma_store = chroma_store
        self.default_top_k = default_top_k

    def retrieve(
        self,
        *,
        question: str,
        document_ids: list[str] | None,
        top_k: int | None,
    ) -> Sequence[RetrievedChunk]:
        if document_ids:
            self._ensure_documents_exist(document_ids)
        question_embedding = self.embedding_service.embed_texts([question])[0]
        return self.chroma_store.query(
            embedding=question_embedding,
            top_k=top_k or self.default_top_k,
            document_ids=document_ids,
        )

    def _ensure_documents_exist(self, document_ids: list[str]) -> None:
        for document_id in document_ids:
            if self.document_repository.get(document_id) is None:
                raise NotFoundError(f"Document '{document_id}' was not found.")

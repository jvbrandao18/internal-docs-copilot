from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chromadb import PersistentClient

from app.domain.services.chunking import DocumentChunk


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    score: float


class ChromaVectorStore:
    def __init__(self, *, persist_path: Path, collection_name: str) -> None:
        self._client = PersistentClient(path=str(persist_path))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self._collection.count()

    def upsert_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("The number of chunks and embeddings must match.")

        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
            embeddings=embeddings,
        )

    def query(
        self,
        embedding: list[float],
        *,
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        candidate_count = top_k if not document_ids else max(top_k * 5, top_k)
        raw_result = self._collection.query(
            query_embeddings=[embedding],
            n_results=candidate_count,
            include=["documents", "metadatas", "distances"],
        )

        allowed_document_ids = set(document_ids or [])
        chunk_ids = raw_result.get("ids", [[]])[0]
        documents = raw_result.get("documents", [[]])[0]
        metadatas = raw_result.get("metadatas", [[]])[0]
        distances = raw_result.get("distances", [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for chunk_id, text, metadata, distance in zip(
            chunk_ids,
            documents,
            metadatas,
            distances,
            strict=False,
        ):
            metadata = metadata or {}
            if allowed_document_ids and metadata.get("document_id") not in allowed_document_ids:
                continue
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    text=text,
                    metadata=metadata,
                    score=self._distance_to_score(distance),
                )
            )
            if len(retrieved) >= top_k:
                break
        return retrieved

    def delete_document(self, document_id: str) -> int:
        snapshot = self._collection.get(include=["metadatas"])
        ids = snapshot.get("ids", [])
        metadatas = snapshot.get("metadatas", [])
        ids_to_delete = [
            chunk_id
            for chunk_id, metadata in zip(ids, metadatas, strict=False)
            if (metadata or {}).get("document_id") == document_id
        ]
        if ids_to_delete:
            self._collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)

    @staticmethod
    def _distance_to_score(distance: float | None) -> float:
        if distance is None:
            return 0.0
        return max(0.0, min(1.0, 1.0 - float(distance)))

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chromadb import PersistentClient

from app.core.exceptions import ExternalServiceError
from app.database.models import Chunk


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    content: str
    metadata: dict[str, Any]
    score: float


class ChromaStore:
    def __init__(self, persist_dir: Path, collection_name: str = "document_chunks") -> None:
        self.client = PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        filename: str,
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ExternalServiceError("Chunk and embedding counts do not match for indexing.")
        try:
            self.collection.upsert(
                ids=[chunk.id for chunk in chunks],
                documents=[chunk.content for chunk in chunks],
                embeddings=embeddings,
                metadatas=[
                    {
                        "document_id": chunk.document_id,
                        "document_name": filename,
                        "page_number": chunk.page_number,
                        "sheet_name": chunk.sheet_name,
                        "row_start": chunk.row_start,
                        "row_end": chunk.row_end,
                        "source_type": chunk.source_type,
                    }
                    for chunk in chunks
                ],
            )
        except Exception as exc:
            raise ExternalServiceError("Failed to index chunks in ChromaDB.") from exc

    def delete_document(self, document_id: str) -> int:
        try:
            snapshot = self.collection.get(include=["metadatas"])
        except Exception:
            return 0
        ids = snapshot.get("ids", [])
        metadatas = snapshot.get("metadatas", [])
        ids_to_delete = [
            chunk_id
            for chunk_id, metadata in zip(ids, metadatas, strict=False)
            if (metadata or {}).get("document_id") == document_id
        ]
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)

    def query(
        self,
        *,
        embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        if self.collection.count() == 0:
            return []
        try:
            raw_result = self.collection.query(
                query_embeddings=[embedding],
                n_results=max(top_k * 5, top_k),
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise ExternalServiceError("Failed to retrieve chunks from ChromaDB.") from exc

        allowed_document_ids = set(document_ids or [])
        chunk_ids = raw_result.get("ids", [[]])[0]
        documents = raw_result.get("documents", [[]])[0]
        metadatas = raw_result.get("metadatas", [[]])[0]
        distances = raw_result.get("distances", [[]])[0]

        matches: list[RetrievedChunk] = []
        for chunk_id, content, metadata, distance in zip(
            chunk_ids,
            documents,
            metadatas,
            distances,
            strict=False,
        ):
            metadata = metadata or {}
            if allowed_document_ids and metadata.get("document_id") not in allowed_document_ids:
                continue
            matches.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    content=content,
                    metadata=metadata,
                    score=max(0.0, min(1.0, 1.0 - float(distance or 0.0))),
                )
            )
            if len(matches) >= top_k:
                break
        return matches

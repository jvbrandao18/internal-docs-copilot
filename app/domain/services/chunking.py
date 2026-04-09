from dataclasses import dataclass, field
from typing import Any

from app.infra.parsers.base import ParsedDocument


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ChunkingService:
    def __init__(
        self,
        *,
        chunk_size: int = 350,
        chunk_overlap: int = 60,
        min_chunk_chars: int = 80,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_chars = min_chunk_chars

    def chunk_document(
        self, *, document_id: str, parsed_document: ParsedDocument
    ) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []

        for section in parsed_document.sections:
            for section_chunk_index, chunk_text in enumerate(
                self._split_text(section.text), start=1
            ):
                metadata = {
                    **section.metadata,
                    "document_id": document_id,
                    "filename": parsed_document.filename,
                    "section_id": section.section_id,
                    "section_chunk_index": section_chunk_index,
                }
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}:{section.section_id}:{section_chunk_index}",
                        text=chunk_text,
                        metadata=metadata,
                    )
                )
        return chunks

    def _split_text(self, text: str) -> list[str]:
        words = text.split()
        if not words:
            return []

        if len(words) <= self.chunk_size:
            return [" ".join(words)]

        step = max(self.chunk_size - self.chunk_overlap, 1)
        chunks: list[str] = []
        for start in range(0, len(words), step):
            end = start + self.chunk_size
            chunk_text = " ".join(words[start:end]).strip()
            if not chunk_text:
                continue
            if len(chunk_text) < self.min_chunk_chars and chunks:
                chunks[-1] = f"{chunks[-1]} {chunk_text}".strip()
                break
            chunks.append(chunk_text)
            if end >= len(words):
                break
        return chunks

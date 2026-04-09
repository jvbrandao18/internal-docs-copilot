from dataclasses import dataclass
from typing import Any

from app.infra.parsers.models import ParsedDocumentResult, ParsedRecord


@dataclass(slots=True)
class ChunkPayload:
    content: str
    source_type: str
    page_number: int | None
    sheet_name: str | None
    row_start: int | None
    row_end: int | None
    metadata_json: dict[str, Any] | None


class ChunkingService:
    def __init__(self, *, pdf_chunk_size: int = 800, pdf_chunk_overlap: int = 120) -> None:
        if pdf_chunk_overlap >= pdf_chunk_size:
            raise ValueError("pdf_chunk_overlap must be smaller than pdf_chunk_size.")
        self.pdf_chunk_size = pdf_chunk_size
        self.pdf_chunk_overlap = pdf_chunk_overlap

    def build_chunks(self, parsed_document: ParsedDocumentResult) -> list[ChunkPayload]:
        if parsed_document.file_type == "pdf":
            return self._build_pdf_chunks(parsed_document.records)
        return [self._record_to_chunk(record) for record in parsed_document.records]

    def _build_pdf_chunks(self, records: list[ParsedRecord]) -> list[ChunkPayload]:
        chunks: list[ChunkPayload] = []
        for record in records:
            for content in self._split_pdf_text(record.content):
                chunks.append(
                    ChunkPayload(
                        content=content,
                        source_type=record.source_type,
                        page_number=record.page_number,
                        sheet_name=None,
                        row_start=None,
                        row_end=None,
                        metadata_json=record.metadata or None,
                    )
                )
        return chunks

    def _record_to_chunk(self, record: ParsedRecord) -> ChunkPayload:
        return ChunkPayload(
            content=record.content,
            source_type=record.source_type,
            page_number=record.page_number,
            sheet_name=record.sheet_name,
            row_start=record.row_start,
            row_end=record.row_end,
            metadata_json=record.metadata or None,
        )

    def _split_pdf_text(self, text: str) -> list[str]:
        clean_text = " ".join(text.split())
        if not clean_text:
            return []
        if len(clean_text) <= self.pdf_chunk_size:
            return [clean_text]

        chunks: list[str] = []
        start = 0
        while start < len(clean_text):
            end = min(start + self.pdf_chunk_size, len(clean_text))
            if end < len(clean_text):
                split_at = clean_text.rfind(" ", start, end)
                if split_at > start + (self.pdf_chunk_size // 2):
                    end = split_at
            chunk = clean_text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(clean_text):
                break
            start = max(end - self.pdf_chunk_overlap, 0)
        return chunks

from pathlib import Path

from app.domain.services.chunking import ChunkingService
from app.infra.parsers.base import ParsedDocument, ParsedSection


def test_chunking_creates_overlapping_chunks() -> None:
    text = " ".join(f"word{i}" for i in range(120))
    parsed_document = ParsedDocument(
        source_path=Path("sample.pdf"),
        filename="sample.pdf",
        content_type="application/pdf",
        metadata={"source_type": "pdf"},
        sections=[
            ParsedSection(
                section_id="page-1",
                text=text,
                metadata={"page_number": 1, "source_label": "page 1"},
            )
        ],
    )

    chunking_service = ChunkingService(chunk_size=30, chunk_overlap=5, min_chunk_chars=1)
    chunks = chunking_service.chunk_document(document_id="doc-1", parsed_document=parsed_document)

    assert len(chunks) >= 4
    assert chunks[0].metadata["document_id"] == "doc-1"
    assert chunks[0].metadata["source_label"] == "page 1"
    assert chunks[0].text.split()[-5:] == chunks[1].text.split()[:5]

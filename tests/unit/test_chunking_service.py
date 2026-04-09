from app.infra.parsers.models import ParsedDocumentResult, ParsedRecord
from app.services.chunking_service import ChunkingService


def test_chunking_service_splits_large_pdf_text_with_overlap() -> None:
    text = " ".join(f"word{i}" for i in range(300))
    parsed_document = ParsedDocumentResult(
        file_type="pdf",
        records=[ParsedRecord(content=text, source_type="pdf_page", page_number=1)],
        page_count=1,
    )

    service = ChunkingService(pdf_chunk_size=200, pdf_chunk_overlap=40)
    chunks = service.build_chunks(parsed_document)

    assert len(chunks) >= 2
    assert all(chunk.page_number == 1 for chunk in chunks)
    assert all(chunk.content.strip() for chunk in chunks)

from pathlib import Path

import fitz

from app.infra.parsers.base import ParsedDocument, ParsedSection


class PdfParser:
    supported_suffixes = (".pdf",)

    def parse(
        self,
        source_path: Path,
        *,
        filename: str,
        content_type: str | None = None,
    ) -> ParsedDocument:
        document = fitz.open(source_path)
        sections: list[ParsedSection] = []

        try:
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                if not text:
                    continue
                sections.append(
                    ParsedSection(
                        section_id=f"page-{page_number}",
                        text=text,
                        metadata={
                            "page_number": page_number,
                            "source_label": f"page {page_number}",
                        },
                    )
                )
            metadata = {
                "source_type": "pdf",
                "page_count": document.page_count,
                "section_count": len(sections),
            }
        finally:
            document.close()

        return ParsedDocument(
            source_path=source_path,
            filename=filename,
            content_type=content_type or "application/pdf",
            metadata=metadata,
            sections=sections,
        )

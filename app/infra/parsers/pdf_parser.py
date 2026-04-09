from pathlib import Path

import fitz

from app.core.exceptions import ValidationError
from app.infra.parsers.models import ParsedDocumentResult, ParsedRecord


class PdfParser:
    def parse(self, file_path: Path) -> ParsedDocumentResult:
        try:
            document = fitz.open(file_path)
        except Exception as exc:
            raise ValidationError("The uploaded PDF could not be opened.") from exc

        records: list[ParsedRecord] = []
        try:
            for page_number, page in enumerate(document, start=1):
                text = self._normalize_text(page.get_text("text"))
                if not text:
                    continue
                records.append(
                    ParsedRecord(
                        content=text,
                        source_type="pdf_page",
                        page_number=page_number,
                        metadata={"page_number": page_number},
                    )
                )
            return ParsedDocumentResult(
                file_type="pdf",
                records=records,
                page_count=document.page_count,
            )
        finally:
            document.close()

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.split()).strip()

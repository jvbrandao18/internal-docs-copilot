from pathlib import Path

from app.core.exceptions import UnsupportedFileTypeError, ValidationError
from app.infra.parsers.csv_parser import CsvParser
from app.infra.parsers.models import ParsedDocumentResult
from app.infra.parsers.pdf_parser import PdfParser
from app.infra.parsers.xlsx_parser import XlsxParser


class ParsingService:
    def __init__(self) -> None:
        self.pdf_parser = PdfParser()
        self.xlsx_parser = XlsxParser()
        self.csv_parser = CsvParser()

    def parse(self, file_path: Path, file_type: str) -> ParsedDocumentResult:
        try:
            if file_type == "pdf":
                return self.pdf_parser.parse(file_path)
            if file_type == "xlsx":
                return self.xlsx_parser.parse(file_path)
            if file_type == "csv":
                return self.csv_parser.parse(file_path)
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(
                f"Failed to parse the uploaded {file_type.upper()} file."
            ) from exc
        raise UnsupportedFileTypeError(f"Unsupported file type: {file_type}")

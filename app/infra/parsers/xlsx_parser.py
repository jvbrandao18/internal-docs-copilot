from pathlib import Path

import pandas as pd

from app.core.exceptions import ValidationError
from app.infra.parsers.models import ParsedDocumentResult, ParsedRecord


class XlsxParser:
    def parse(self, file_path: Path) -> ParsedDocumentResult:
        try:
            sheets = pd.read_excel(file_path, sheet_name=None)
        except Exception as exc:
            raise ValidationError("The uploaded XLSX could not be parsed.") from exc

        records: list[ParsedRecord] = []

        for sheet_name, dataframe in sheets.items():
            normalized = dataframe.fillna("")
            for index, row in normalized.iterrows():
                row_number = int(index) + 2
                row_parts = [
                    f"{column}: {self._normalize_text(str(value))}"
                    for column, value in row.items()
                    if self._normalize_text(str(value))
                ]
                if not row_parts:
                    continue
                content = f"Sheet: {sheet_name} | Row: {row_number} | " + " | ".join(row_parts)
                records.append(
                    ParsedRecord(
                        content=content,
                        source_type="xlsx_row",
                        sheet_name=str(sheet_name),
                        row_start=row_number,
                        row_end=row_number,
                        metadata={"sheet_name": str(sheet_name), "row_number": row_number},
                    )
                )

        return ParsedDocumentResult(
            file_type="xlsx",
            records=records,
            sheet_count=len(sheets),
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.split()).strip()

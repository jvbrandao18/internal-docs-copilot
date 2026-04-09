from pathlib import Path

import pandas as pd

from app.core.exceptions import ValidationError
from app.infra.parsers.models import ParsedDocumentResult, ParsedRecord


class CsvParser:
    def parse(self, file_path: Path) -> ParsedDocumentResult:
        try:
            dataframe = pd.read_csv(file_path)
        except Exception as exc:
            raise ValidationError("The uploaded CSV could not be parsed.") from exc

        normalized = dataframe.fillna("")
        records: list[ParsedRecord] = []

        for index, row in normalized.iterrows():
            row_number = int(index) + 2
            row_parts = [
                f"{column}: {self._normalize_text(str(value))}"
                for column, value in row.items()
                if self._normalize_text(str(value))
            ]
            if not row_parts:
                continue
            content = f"Row: {row_number} | " + " | ".join(row_parts)
            records.append(
                ParsedRecord(
                    content=content,
                    source_type="csv_row",
                    row_start=row_number,
                    row_end=row_number,
                    metadata={"row_number": row_number},
                )
            )

        return ParsedDocumentResult(file_type="csv", records=records)

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.split()).strip()

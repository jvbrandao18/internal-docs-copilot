from pathlib import Path
from typing import Any

import pandas as pd

from app.infra.parsers.base import ParsedDocument, ParsedSection


class SpreadsheetParser:
    supported_suffixes = (".xlsx", ".csv")

    def parse(
        self,
        source_path: Path,
        *,
        filename: str,
        content_type: str | None = None,
    ) -> ParsedDocument:
        suffix = source_path.suffix.lower()
        if suffix == ".csv":
            dataframe = pd.read_csv(source_path)
            sections = self._build_sections(dataframe, sheet_name="csv")
            metadata = {
                "source_type": "csv",
                "sheet_count": 1,
                "row_count": int(len(dataframe.index)),
                "columns": [str(column) for column in dataframe.columns],
            }
            return ParsedDocument(
                source_path=source_path,
                filename=filename,
                content_type=content_type or "text/csv",
                metadata=metadata,
                sections=sections,
            )

        sheets = pd.read_excel(source_path, sheet_name=None)
        sections: list[ParsedSection] = []
        sheet_metadata: dict[str, Any] = {}
        total_rows = 0

        for sheet_name, dataframe in sheets.items():
            sheet_name = str(sheet_name)
            sections.extend(self._build_sections(dataframe, sheet_name=sheet_name))
            sheet_metadata[sheet_name] = {
                "row_count": int(len(dataframe.index)),
                "columns": [str(column) for column in dataframe.columns],
            }
            total_rows += int(len(dataframe.index))

        metadata = {
            "source_type": "xlsx",
            "sheet_count": len(sheets),
            "row_count": total_rows,
            "sheets": sheet_metadata,
        }
        return ParsedDocument(
            source_path=source_path,
            filename=filename,
            content_type=content_type
            or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            metadata=metadata,
            sections=sections,
        )

    def _build_sections(self, dataframe: pd.DataFrame, *, sheet_name: str) -> list[ParsedSection]:
        if dataframe.empty:
            return []

        sections: list[ParsedSection] = []
        normalized = dataframe.fillna("")
        for index, row in normalized.iterrows():
            row_number = int(index) + 2
            parts = []
            for column_name, value in row.items():
                if value == "":
                    continue
                parts.append(f"{column_name}: {value}")
            if not parts:
                continue
            sections.append(
                ParsedSection(
                    section_id=f"{sheet_name}-row-{row_number}",
                    text=" | ".join(parts),
                    metadata={
                        "sheet_name": sheet_name,
                        "row_number": row_number,
                        "source_label": f"{sheet_name} row {row_number}",
                    },
                )
            )
        return sections
